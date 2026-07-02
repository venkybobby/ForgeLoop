# Desktop capture agent — architecture spike

**Question this answers:** the browser extension captures web apps; a large share
of healthcare / financial / industrial work happens in **native desktop apps**
(and inside **Citrix/VDI**). How do we capture *those* into the same skills, how
big is the build, and where are the walls?

**TL;DR.** A desktop agent is a **new event *source*, not a new product.** If it
emits the same event envelope the browser extension already does and POSTs to the
same `/v1/traces/*` endpoints with the same `fk_` key, then **tenant isolation,
redaction review, distillation, and the portal all work unchanged.** The real
engineering is (1) turning OS UI-automation trees into our event schema and
(2) the Citrix wall, which forces a vision/OCR fallback. Estimated **6–10
engineer-weeks** to a Windows pilot; Citrix adds meaningfully more.

---

## 1. Design principle: reuse the whole pipeline

The recorder already accepts a generic, resumable trace upload:

```
POST /v1/traces/init                        -> upload_id
PUT  /v1/traces/{upload_id}/chunks/{index}  -> gzip-NDJSON event chunk
POST /v1/traces/{upload_id}/finalize        -> assemble + auto-distil
GET  /v1/traces/{upload_id}/status          -> distill status / result
```

`finalize` assembles the chunks into a `journey_trace_v1` document:

```json
{ "schema_version": "journey_trace_v1", "trace_id": "...", "label": "...",
  "events": [ /* one object per captured action */ ] }
```

and the harness distils it (atomise → classify → bucket → distil → `SKILL.md`).

**So the desktop agent's only job is to produce a compatible `events[]` stream
and push it through the same endpoints.** Everything we already built downstream
is source-agnostic:

| Capability | Status | Reused by desktop agent? |
|---|---|---|
| Per-tenant data isolation (Bearer `fk_` → own store) | ✅ built | **Yes, unchanged** — agent sends the client's `fk_` key |
| Redaction (passwords/PII/tokens) | ✅ built (browser) | **Re-implemented** in the agent (see §5) |
| Pre-upload review + consent | ✅ built (browser) | **Re-implemented** in the agent tray UI |
| Distillation → `SKILL.md` | ✅ built | **Yes, unchanged** |
| Skills portal | ✅ built | **Yes, unchanged** — desktop skills appear alongside web ones |

That table is the whole strategic point: **~70% of a "desktop product" already
exists.** The agent is the missing front-end sensor.

---

## 2. The event contract the agent must emit

The harness normalises each event via `harness/adapter.py::_norm_recorder_event`.
It consumes this shape (browser extension emits it today):

```jsonc
{ "kind": "action",              // action | navigation
  "type": "click",               // click | input | keydown | submit | ...
  "url":  "https://app/…",        // <-- see §3: desktop must SYNTHESISE this
  "timestamp": 1720000000000,
  "target": { "tag": "...", "id": "...", "name": "...", "text": "...", "xpath": "..." },
  "coords": { "x": 100, "y": 240 },
  "value": "<redacted>", "key": "Enter" }
```

The harness reasons over **`url`** to split a recording into per-app,
per-view segments (`registered_domain(url)` + path-prefix boundaries). A native
app has no URL — **this is the one non-obvious mapping the agent must invent.**

---

## 3. The synthetic URL namespace (key design decision)

Give every desktop app a stable pseudo-URL so the atomiser's domain/path
segmentation keeps working with zero harness changes:

```
app://<application>/<window-or-view>/<control-path>
```

Examples:

```
app://SARO/PatientSearch/toolbar.searchButton
app://Epic/Chart/Orders/newOrderButton
app://Excel/Workbook/Sheet1/A1
```

- `<application>` = the process / product (from the top-level window) → becomes
  the "domain", so each app's skills bucket separately, exactly like each website
  does today.
- `<window-or-view>` = active window title or top control view → drives the
  path-prefix segment boundaries (a view change = a new segment, mirroring a page
  navigation).
- A `navigation` event is emitted on **window/view focus change** (analogue of
  `pageLoad`).

**Result:** no harness edits. Desktop recordings segment, classify, and distil
through the identical code path as web recordings.

---

## 4. Capture mechanism A — semantic (Windows UIA)

The *right* way (what UiPath / Power Automate do), not pixel scraping.

- **API:** Windows **UI Automation** (UIA) via `pywinauto` / `comtypes`, or a
  thin C#/.NET helper. macOS analogue: the **AX** (Accessibility) API.
- **What we hook:**
  - Global low-level input (mouse/keyboard) for *when* and *where* an action
    happened — `SetWindowsHookEx` / raw input.
  - UIA **element-from-point** + focus/property-changed events for *what* was
    acted on — control type, name, AutomationId, bounding rect, parent chain
    (→ our `target.tag/id/name/xpath`, where `xpath` = the UIA control path).
  - UIA window/focus events → `navigation` events + the `<window-or-view>`.
- **What we get:** semantic, replayable events ("clicked the *Search* button in
  *PatientSearch*"), not "clicked pixel (412,240)." This is what makes a
  distilled skill *reliable* rather than brittle.
- **Redaction at source:** UIA exposes control type (e.g. `Edit` with
  `IsPassword`) and field names, so we apply the **same redaction classes** the
  browser redactor uses (passwords, email, phone, payment, OTP, tokens) *before*
  the value is ever written to disk.

**Coverage caveat:** UIA quality varies by app. Modern WinUI/WPF/Win32/Electron
expose rich trees; some legacy Win32/Java/Delphi apps expose almost nothing
(name-only, no AutomationId). For those we degrade toward §5.

---

## 5. Capture mechanism B — the Citrix / VDI wall + vision fallback

**The wall:** in Citrix / RDP / VMware Horizon, the app runs on a *remote*
server and the client sees only a **streamed image**. UIA on the client is blind
(there's no local element tree) — and so is any browser extension. This is
extremely common in healthcare/finance, so it must be named up front, not
discovered mid-pilot.

Two ways through, in preference order:

1. **Agent runs *inside* the Citrix session** (on the remote server, via published
   app / golden image). Then UIA works normally — this is the clean answer when
   we can get IT to deploy the agent server-side. **Push for this.**
2. **Client-side vision fallback** when we can't deploy server-side:
   - screen-capture the session region + **OCR** (Tesseract/PaddleOCR or a hosted
     vision model) to recover text and control candidates;
   - correlate with mouse/keyboard timing to reconstruct actions.
   - Brittle, heavier, privacy-hotter (pixels of PHI), and needs redaction on the
     image itself (OCR-then-mask). Treat as **degraded mode**, clearly labelled in
     the recording so a distilled skill's confidence reflects it.

**Recommendation:** lead with option 1 (deploy in the image); offer vision only
where required, and price/scope it as a separate tier.

---

## 6. Redaction & consent parity (non-negotiable)

Whatever we built for the browser must hold for desktop, or the compliance story
regresses:

- **Redact at source** using the shared class list, before any value hits disk.
- **Pre-upload review**: the agent's system-tray UI shows the same
  "Review before upload" panel — app/views touched, event count, and the
  **redaction breakdown** — with **Approve / Discard**. Nothing uploads
  unreviewed, matching the extension.
- Ship a **redaction spec** shared conceptually with
  `forge/extension/src/redaction/redactor.ts` so both sources scrub identically.

---

## 7. Tenant isolation parity (free)

No work needed. The agent authenticates with the client's `fk_` key; the
recorder's dispatcher routes it to that tenant's isolated store. Desktop and web
recordings for the same client **land in the same tenant** and show together in
their portal. Different clients stay isolated exactly as today.

---

## 8. Phasing & effort

| Phase | Scope | Est. |
|---|---|---|
| **0 — Proof of contract** | Tiny Windows script: hook clicks, resolve UIA element, emit synthetic-URL events, POST through `/v1/traces/*` with an `fk_` key, watch a `SKILL.md` appear in the portal. *Proves the whole loop with no new server code.* | 3–5 days |
| **1 — Semantic recorder** | Robust UIA capture (input hooks + element resolution + window/focus nav), synthetic-URL builder, local buffering, resumable upload client. | 2–3 wks |
| **2 — Redaction + consent UI** | Source redaction (class parity) + tray review/approve panel. | 1–2 wks |
| **3 — Packaging** | Signed installer (MSI), auto-update, config (endpoint + key), enterprise silent-deploy (Intune/GPO). | 1–2 wks |
| **4 — Citrix** | Server-side deployment recipe; *then* (optional) vision/OCR degraded mode. | 2 wks → **much more** for vision |
| **macOS (later)** | AX-API port of Phase 1–2. | +2–3 wks |

**To a Windows pilot (Phases 0–3): ~6–10 engineer-weeks.** Citrix vision fallback
and macOS are additive and should be demand-gated by a real design partner.

---

## 9. Risks & open questions

- **UIA coverage on legacy apps** — the single biggest technical unknown. *De-risk
  in Phase 0* by testing the actual apps a design partner uses (name them first).
- **Endpoint security** — an agent with global input hooks is exactly what EDR
  flags. Needs code-signing, a clear privacy whitepaper, and ideally a
  security review. Enterprises will ask.
- **Employee-monitoring optics/law** — always-on desktop capture is more
  sensitive than browser. Must be **explicit start/stop per task**, never ambient,
  with the same consent panel. (Same stance as the browser recorder.)
- **Distillation quality without URLs** — the synthetic namespace is a hypothesis;
  validate that segments/skills come out coherent on a real desktop workflow in
  Phase 0 before investing in Phases 1–3.
- **Vision cost/latency** — OCR-per-frame is expensive; only for the Citrix
  degraded tier.

---

## 10. Recommendation

**Do Phase 0 first, against a named design partner's actual desktop app.** It's a
few days, needs **zero** new server code (the pipeline is already source-agnostic),
and it answers the two questions that decide everything: *does UIA see enough in
their app?* and *does the synthetic-URL namespace distil into coherent skills?*
If Phase 0 produces a real `SKILL.md` from a native app in their portal, the
remaining phases are conventional engineering. If it doesn't, we've spent days,
not months, to learn we need the vision tier — before committing to it.

This keeps the strategy intact: **capture is a sensor; the moat is the shared
skill factory + governed execution + isolation + consent that every sensor feeds.**
