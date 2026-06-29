"""llm_executor — agentic execution: observe the DOM, let an LLM choose the next
action, act, verify, repeat.

This is the autonomous counterpart to `loop_runner.run_live` (which replays a
recorded trace). Here the next action is *chosen* against the live DOM, so the
loop can handle pages that differ from the recording.

The chooser is injected (`run_agentic(chooser=…)`), so the same loop is driven by:
  * `make_llm_chooser()` — a real LLM (Anthropic or any OpenAI-compatible gateway,
    via SF_LLM_KEY/SF_LLM_BASE — the same config Forge uses), or
  * any callable, e.g. a scripted chooser for tests (no key / no network).

Stdlib + Playwright only.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

from .receipt import Receipt
from .skill_to_loop import parse_skill
from .loop_runner import _loop_identity, _acceptance_from_loop, SAFETY_CAP
from .browser_executor import BrowserExecutor, actions_from_trace

ACTIONS = ("fill", "click", "navigate", "stop")


# ──────────────────────────── minimal LLM client ───────────────────────────
def call_llm(prompt: str, *, max_tokens: int = 1024) -> str:
    """Anthropic Messages API natively; OpenAI-compatible chat/completions when
    SF_LLM_BASE points elsewhere. Mirrors forge/harness/llm.py."""
    base = os.environ.get("SF_LLM_BASE", "https://api.anthropic.com").rstrip("/")
    key = os.environ.get("SF_LLM_KEY", "")
    model = os.environ.get("SF_DISTILL_MODEL", "claude-opus-4-8")
    if not key:
        raise RuntimeError("SF_LLM_KEY is not set — no LLM available for the agentic chooser.")
    if "anthropic.com" in base:
        url, headers = f"{base}/v1/messages", {
            "content-type": "application/json", "x-api-key": key,
            "anthropic-version": "2023-06-01",
        }
        body = {"model": model, "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]}
        extract = lambda d: "".join(b.get("text", "") for b in d.get("content", [])
                                    if b.get("type") == "text")
    else:
        url, headers = f"{base}/v1/chat/completions", {
            "content-type": "application/json", "authorization": f"Bearer {key}"}
        body = {"model": model, "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}}
        extract = lambda d: d["choices"][0]["message"]["content"]
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=90) as resp:  # noqa: S310
        return extract(json.loads(resp.read().decode()))


def parse_action(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.I | re.M).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start >= 0 and end > start:
        cleaned = cleaned[start:end + 1]
    return json.loads(cleaned)


# ──────────────────────────── DOM observation ──────────────────────────────
_DOM_JS = r"""() => {
  const out = [];
  const els = document.querySelectorAll('input, textarea, select, button, a[href]');
  els.forEach((el, i) => {
    if (el.offsetParent === null && el.type !== 'hidden') { /* keep anyway */ }
    const tag = el.tagName.toLowerCase();
    const sel = el.id ? '#'+CSS.escape(el.id)
      : (el.name ? `${tag}[name="${el.name}"]`+(el.value!==undefined&&el.type==='radio'?`[value="${el.value}"]`:'')
      : (tag==='button'? 'button' : tag));
    out.push({ i, tag, type: el.type||'', name: el.name||'', id: el.id||'',
      value: (el.value||'').slice(0,40), text: (el.innerText||el.value||'').trim().slice(0,40),
      selector: sel });
  });
  return out;
}"""


def dom_summary(ex: BrowserExecutor) -> list[dict]:
    try:
        return ex.page.evaluate(_DOM_JS)
    except Exception:  # noqa: BLE001
        return []


def _dom_text(elements: list[dict]) -> str:
    lines = []
    for e in elements:
        desc = f"<{e['tag']}"
        if e["type"]:
            desc += f" type={e['type']}"
        if e["name"]:
            desc += f" name={e['name']}"
        if e["text"]:
            desc += f' text="{e["text"]}"'
        desc += f">  selector: {e['selector']}"
        lines.append(desc)
    return "\n".join(lines) or "(no interactive elements found)"


# ──────────────────────────── choosers ─────────────────────────────────────
CHOOSE_PROMPT = """You are driving a web browser to accomplish a task, one action at a time.

OBJECTIVE: {objective}

SUCCESS when ALL of these are observably true:
{acceptance}

CURRENT URL: {url}
INTERACTIVE ELEMENTS ON THE PAGE:
{dom}

ACTIONS SO FAR:
{history}

VALUES YOU MAY USE (from the recorded task; use the matching one for each field):
{values}

Choose the SINGLE next action. Reply with ONLY a JSON object:
{{"thought": "...", "action": "fill|click|navigate|stop",
  "selector": "<css/xpath selector from the list>", "value": "<for fill>", "done": false}}
Set action "stop" and done=true only when SUCCESS is already met. Never click submit
more than once. Prefer filling required fields before submitting."""


def make_llm_chooser(values: dict | None = None):
    values = values or {}
    val_text = "\n".join(f"- {k}: {v}" for k, v in values.items()) or "(none)"

    def chooser(step: int, ctx: dict) -> dict:
        prompt = CHOOSE_PROMPT.format(
            objective=ctx["objective"],
            acceptance="\n".join(f"- {a}" for a in ctx["acceptance"]) or "- (none)",
            url=ctx["url"], dom=ctx["dom_text"],
            history="\n".join(ctx["history"]) or "(none yet)",
            values=val_text,
        )
        return parse_action(call_llm(prompt))

    return chooser


def values_from_trace(trace_path: str | Path) -> dict:
    data = json.loads(Path(trace_path).read_text())
    out = {}
    for ev in data.get("events", []):
        if ev.get("type") == "input" and ev.get("value") is not None:
            tgt = ev.get("target") or {}
            out[tgt.get("id") or tgt.get("xpath") or f"field{len(out)}"] = ev["value"]
    return out


# ──────────────────────────── agentic loop ─────────────────────────────────
def run_agentic(
    loop_path: str | Path,
    skill_path: str | Path,
    *,
    chooser,
    start_url: str,
    approve: bool = False,
    headless: bool = True,
    max_steps: int = 12,
    evidence_dir: str | Path | None = None,
    runs_dir: str | Path | None = None,
    ts: str | None = None,
    audit: bool = True,
) -> Receipt:
    loop_md = Path(loop_path).read_text()
    name, sha = _loop_identity(loop_md)
    skill = parse_skill(skill_path)
    acceptance = skill.acceptance or _acceptance_from_loop(loop_md)
    objective = skill.objective or skill.title
    boundary = f"max {max_steps} agentic steps"
    check = (f"LLM verifies acceptance against the live DOM; e.g. “{acceptance[0]}”"
             if acceptance else "NO acceptance check")

    def _audit(kind: str, detail: dict) -> None:
        if not audit:
            return
        try:
            from ..governance.audit import record_event
            record_event(actor="system", kind=kind, subject=name, detail=detail, ts=ts)
        except Exception:  # noqa: BLE001
            pass

    if not approve:
        rec = Receipt(loop=name, definition=f"loop.md SHA-256 {sha[:16]}… (agentic)",
                      scope="LIVE agentic — not started", check=check, boundary=boundary,
                      result="Approval required",
                      evidence=["Agentic browser execution requires explicit approval."],
                      actions=["No browser launched."], next="Re-run with approval.", ts=ts)
        from .loop_runner import _persist
        _persist(rec, runs_dir, name)
        return rec

    _audit("approval.granted", {"loop_sha256": sha, "mode": "agentic"})
    _audit("run.started", {"loop_sha256": sha, "mode": "agentic", "approved": True})

    evidence = [f"Mode: agentic (LLM chooses each action). Objective: {objective[:120]}"]
    history: list[str] = []
    result, nxt = "No progress", "nothing"

    ex = BrowserExecutor(headless=headless)
    try:
        ex.start()
        ex.navigate(start_url)
        history.append(f"navigate {start_url}")
        for step in range(max_steps):
            elements = dom_summary(ex)
            ctx = {"objective": objective, "acceptance": acceptance,
                   "url": ex.current_url(), "dom_text": _dom_text(elements),
                   "history": history}
            try:
                action = chooser(step, ctx)
            except Exception as e:  # noqa: BLE001
                result, nxt = "Blocked", f"Chooser failed: {type(e).__name__}: {e}"
                break

            op = (action.get("action") or "").lower()
            sel, val = action.get("selector", ""), action.get("value", "")
            thought = action.get("thought", "")
            if op == "stop" or action.get("done"):
                history.append(f"stop — {thought}")
                break
            try:
                if op == "fill":
                    ex.fill(sel, val); history.append(f'fill {sel} = "{val}"')
                elif op == "click":
                    ex.click(sel); history.append(f"click {sel}")
                elif op == "navigate":
                    ex.navigate(val or sel); history.append(f"navigate {val or sel}")
                else:
                    history.append(f"unknown action {op!r} — skipped")
            except Exception as e:  # noqa: BLE001
                result = "Blocked"
                history.append(f"FAILED {op} {sel} — {type(e).__name__}")
                nxt = f"Action failed: {op} {sel}. Page may not match expectations."
                break
        else:
            result, nxt = "Exhausted", f"Hit step budget ({boundary})."

        final_url = ex.current_url()
        snippet = ex.page_text(400)
        left_start = final_url.rstrip("/") != start_url.rstrip("/")
        if result not in ("Blocked", "Exhausted"):
            result = "Success" if (left_start and snippet.strip()) else "No progress"
            nxt = "nothing — acceptance met." if result == "Success" else \
                  "Objective not confirmed on the page."
        evidence += [f"Start URL: {start_url}", f"Final URL: {final_url}",
                     f"Steps taken: {len(history)}",
                     f"Result page text: “{snippet[:220]}”"]
        if evidence_dir is not None:
            evidence.append(f"Screenshot: {ex.screenshot(Path(evidence_dir) / 'agentic.png')}")
    finally:
        ex.close()

    rec = Receipt(loop=name, definition=f"loop.md SHA-256 {sha[:16]}… (agentic, chooser-driven)",
                  scope="LIVE agentic browser run", check=check, boundary=boundary,
                  result=result, evidence=evidence,
                  actions=[f"Step {i+1}: {h}" for i, h in enumerate(history)] or ["(no steps)"],
                  next=nxt, ts=ts)
    _audit("run.finished", {"result": rec.result, "steps": len(history)})
    from .loop_runner import _persist
    _persist(rec, runs_dir, name)
    return rec
