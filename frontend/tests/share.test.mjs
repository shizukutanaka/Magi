import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const { inputFromShareParams, isUnsupportedShare, readShareParams, shareUrl } = await import("../share.js");

// Generated from the pre-specialization frontend (main@e7a00a7) and verified offline by the backend.
const golden = JSON.parse(await readFile(new URL("../../backend/tests/fixtures/tarot_golden.json", import.meta.url), "utf8"));

for (const item of golden.share_urls) {
  const url = shareUrl("http://localhost:8000/", "tarot", item.input, item.subject, item.lang);
  assert.equal(url, item.url, "tarot share URL format must not change");

  const parsed = new URL(url);
  for (const params of [readShareParams(parsed.hash, ""), readShareParams("", `?${parsed.hash.slice(1)}`)]) {
    assert.equal(isUnsupportedShare(params), false);
    assert.deepEqual(
      JSON.parse(JSON.stringify(inputFromShareParams(params, "2000-01-01"))),
      JSON.parse(JSON.stringify(item.input)),
      "a tarot share URL must restore the original input",
    );
    assert.equal(params.get("s"), item.subject);
  }
}

assert.equal(inputFromShareParams(new URLSearchParams("engine=tarot"), "2026-11-19").options.spread, "three-card");
assert.equal(readShareParams("#engine=tarot&s=a", "?engine=tarot&s=b").get("s"), "a");

for (const engine of ["iching", "runes", "omikuji", "astrology", "numerology", "bazi", "mayan", "geomancy"]) {
  assert.equal(isUnsupportedShare(new URLSearchParams(`engine=${engine}&date=2026-01-01&s=x`)), true);
}
assert.equal(isUnsupportedShare(new URLSearchParams("daily=1&date=2026-01-01&s=x")), true);
assert.equal(isUnsupportedShare(new URLSearchParams("lang=en")), false);

console.log(`frontend share URL test passed (${golden.share_urls.length} tarot URLs)`);
