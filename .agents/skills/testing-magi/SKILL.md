---
name: testing-magi
description: How to run and end-to-end test the Magi divination app locally on macOS — server startup, Chrome launch flags, share-URL formats, history storage, and known input quirks.
---

# Testing Magi locally

## Server

```bash
cd ~/repos/Magi/backend && source .venv/bin/activate && uvicorn app.main:app --port 8901 --no-proxy-headers > /tmp/magi-run.log 2>&1 &
```

- The venv has all deps; no DB, no auth. App serves the frontend at `/` on the same port.
- Startup prints `INFO:app.main:Magi configuration: ...` to stderr — keep stderr redirected to a file so you can later grep the access log (uvicorn logs request lines there).
- Config env vars (`MAGI_TRUST_PROXY`, `MAGI_RATE_LIMIT_PER_MINUTE`, `MAGI_STATIC_DIR`) raise `ConfigError` at import on invalid values; empty string means unset.

## Browser

```bash
open -na "Google Chrome" --args --user-data-dir=/tmp/magi-chrome --remote-debugging-port=29229 --no-first-run --no-default-browser-check http://localhost:8901/
```

- A fresh `--user-data-dir` gives a clean `localStorage` (history starts empty) without clearing anything in the UI.
- macOS quirks seen with synthetic input: clicking the tab-strip `+` may not land (its position shifts as tabs accumulate); `Cmd+T` works after clicking inside the page to focus Chrome. `Cmd+L`/`Cmd+V` work for the omnibox once the window is focused.
- Japanese text cannot be typed reliably via synthetic `type` actions (IME garbles it into stray characters). Use ASCII for question/name inputs — the UI language itself still renders Japanese fine.
- Read clipboard contents with `pbpaste` to assert copied share URLs.
- `browser_console` tool may not attach to a Chrome launched this way; open DevTools visibly with `Cmd+Opt+J` and screenshot the console instead.

## Feature pointers

- Share URL format: `http://localhost:PORT/#engine=<id>&date=YYYY-MM-DD&q=..&birth=..&name=..&s=<subject-token>&lang=ja`. Fragments never reach the server log — verify privacy by grepping the stderr log for `q=`/`birth=`/`name=`. Old `?` URLs still work (readUrl falls back to `location.search`).
- `hashchange` listener calls `location.reload()` — pasting a different `#` URL over the same path auto-reloads and re-runs the reading.
- Engines: `tarot` (no required fields, has spread), `numerology` (requires birth_date + full_name). History lives in `localStorage["magi.history"]`, deduped by `seed`; entries are `<a href>` so clicks navigate.
- To trigger the numerology master-number guidance text (`body.numerology.guidance`), use `birth=1990-01-02` — its digit sum is 22, a master number.
- `python -m app.verify '<share-url>' --expect-seed <seed>` exits 0 on seed match, 1 on mismatch; accepts both `#` and `?` URLs. Sections aren't in human output — use `--json` to inspect section bodies.
- History export downloads `~/Downloads/magi-history.json` (blob URL).
