import assert from "node:assert/strict";

const { CATALOGS } = await import("../i18n.js");
const jaKeys = Object.keys(CATALOGS.ja).sort();
const enKeys = Object.keys(CATALOGS.en).sort();
const cjk = /[\u3040-\u30ff\u4e00-\u9fff]/u;

assert.deepEqual(enKeys, jaKeys, "Japanese and English catalog keys must match");
for (const [key, value] of Object.entries(CATALOGS.en)) {
  assert.equal(typeof value, "string", `${key} must have a string value`);
  assert.equal(cjk.test(value), false, `${key} English value contains CJK`);
}

console.log(`frontend i18n catalog test passed (${enKeys.length} keys)`);
