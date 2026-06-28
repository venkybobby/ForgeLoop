"""browser_executor — real browser actions for a ForgeLoop loop run (Playwright).

Wraps Playwright's sync API over the pre-installed Chromium so an *approved* loop
run can actually act on a live page and reach a real terminal state. Kept small
and focused on the actions the example skills need: navigate / click / fill /
read-back.

Playwright is an optional dependency: this module imports cleanly without it, and
only raises (with an install hint) when you actually try to launch a browser.

`actions_from_trace()` turns a recorded human-track `trace.json` into a concrete,
replayable action plan — the recording is the ground truth of *what* to do, while
the `loop.md` provides the governance/acceptance policy of *whether* it's allowed
and *when* it's done.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

try:  # optional dependency
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except Exception:  # noqa: BLE001
    PLAYWRIGHT_AVAILABLE = False


def default_executable() -> str | None:
    """The pre-installed Chromium in this environment, if present."""
    cand = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")) / "chromium"
    return str(cand) if cand.exists() else None


def _sel(selector: str) -> str:
    """Accept raw XPath (from recordings) or a CSS selector."""
    s = selector.strip()
    if s.startswith("//") or s.startswith("(//") or s.startswith("xpath="):
        return s if s.startswith("xpath=") else f"xpath={s}"
    return s


class BrowserExecutor:
    """Minimal, auto-waiting browser driver. Use as a context manager."""

    def __init__(self, *, headless: bool = True, executable_path: str | None = None,
                 timeout_ms: int = 8000):
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError(
                "Playwright is not installed. Install it with:\n"
                "    python -m pip install playwright\n"
                "This environment ships Chromium at $PLAYWRIGHT_BROWSERS_PATH, so no "
                "'playwright install' is needed."
            )
        self.headless = headless
        self.executable_path = executable_path or default_executable()
        self.timeout_ms = timeout_ms
        self._pw = None
        self._browser = None
        self.page = None

    # -- lifecycle -----------------------------------------------------------
    def start(self) -> "BrowserExecutor":
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            executable_path=self.executable_path,
            headless=self.headless,
            args=["--no-sandbox"],  # required when running as root in a sandbox
        )
        self.page = self._browser.new_page()
        self.page.set_default_timeout(self.timeout_ms)
        return self

    def __enter__(self) -> "BrowserExecutor":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        for closer in (getattr(self._browser, "close", None), getattr(self._pw, "stop", None)):
            try:
                if closer:
                    closer()
            except Exception:  # noqa: BLE001
                pass

    # -- actions -------------------------------------------------------------
    def navigate(self, url: str) -> None:
        self.page.goto(url)

    def click(self, selector: str) -> None:
        self.page.click(_sel(selector))

    def fill(self, selector: str, value: str) -> None:
        self.page.fill(_sel(selector), value)

    # -- observation ---------------------------------------------------------
    def current_url(self) -> str:
        return self.page.url

    def page_text(self, limit: int = 600) -> str:
        try:
            txt = self.page.inner_text("body")
        except Exception:  # noqa: BLE001
            txt = self.page.content()
        txt = " ".join(txt.split())
        return txt[:limit]

    def has_text(self, needle: str) -> bool:
        return needle.lower() in self.page.content().lower()

    def screenshot(self, path: str | Path) -> str:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=str(p), full_page=True)
        return str(p)


# ──────────────────────────── trace -> action plan ─────────────────────────
def _rewrite_host(url: str, base_url: str | None) -> str:
    if not base_url:
        return url
    from urllib.parse import urlsplit, urlunsplit
    u = urlsplit(url)
    b = urlsplit(base_url)
    return urlunsplit((b.scheme, b.netloc, u.path or "/", u.query, u.fragment))


def actions_from_trace(trace_path: str | Path, *, base_url: str | None = None) -> list[dict]:
    """Concrete, replayable steps from a human-track recording. `base_url` rewrites
    the recorded scheme+host (e.g. to a locally-served copy when public egress is
    blocked)."""
    data = json.loads(Path(trace_path).read_text())
    actions: list[dict] = []
    navigated = False
    for ev in data.get("events", []):
        etype = ev.get("type")
        target = ev.get("target") or {}
        xpath = target.get("xpath")
        if etype in ("pageLoad", "navigation"):
            # Only the FIRST navigation is an action; later page loads are the
            # *consequence* of a click/submit, not steps to replay (replaying them
            # would issue a spurious GET over the real post-submit result page).
            if navigated:
                continue
            navigated = True
            actions.append({"op": "navigate", "url": _rewrite_host(ev.get("url", ""), base_url),
                            "label": f"navigate {ev.get('url','')}"})
        elif etype == "input" and xpath is not None:
            actions.append({"op": "fill", "selector": xpath, "value": ev.get("value", ""),
                            "label": f"fill {target.get('id') or xpath}"})
        elif etype == "click" and xpath is not None:
            actions.append({"op": "click", "selector": xpath,
                            "label": f"click {target.get('textContent') or target.get('id') or xpath}"})
    return actions
