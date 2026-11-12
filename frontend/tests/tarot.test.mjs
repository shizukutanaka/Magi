import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const html = readFileSync(new URL("../tarot.html", import.meta.url), "utf8");

// --- Embedded card data -------------------------------------------------
const match = html.match(/\/\*CARDS-BEGIN\*\/(\[.*?\])\/\*CARDS-END\*\//s);
assert.ok(match, "tarot.html must embed the card data between CARDS markers");
const cards = JSON.parse(match[1]);

assert.equal(cards.length, 78, "a Rider-Waite deck has 78 cards");
assert.equal(new Set(cards.map((c) => c.key)).size, 78, "card keys must be unique");

const majors = cards.filter((c) => c.major);
const minors = cards.filter((c) => !c.major);
assert.equal(majors.length, 22, "22 major arcana");
assert.equal(minors.length, 56, "56 minor arcana");
assert.deepEqual(
  majors.map((c) => c.num),
  Array.from({ length: 22 }, (_, i) => i),
  "major arcana numbers run 0..21 in order",
);
for (const suit of ["wands", "cups", "swords", "pentacles"]) {
  assert.equal(minors.filter((c) => c.suit === suit).length, 14, `${suit} has 14 cards`);
}

const cjk = /[\u3040-\u30ff\u4e00-\u9fff]/u;
for (const card of cards) {
  for (const lang of ["ja", "en"]) {
    assert.ok(card.name[lang]?.length > 0, `${card.key} needs a ${lang} name`);
    assert.ok(card.up[lang]?.length > 0, `${card.key} needs a ${lang} upright meaning`);
    assert.ok(card.rev[lang]?.length > 0, `${card.key} needs a ${lang} reversed meaning`);
  }
  assert.equal(cjk.test(card.name.en), false, `${card.key} English name contains CJK`);
  assert.equal(cjk.test(card.up.en), false, `${card.key} English upright meaning contains CJK`);
  assert.equal(cjk.test(card.rev.en), false, `${card.key} English reversed meaning contains CJK`);
  assert.equal(card.kwUp.length, 3, `${card.key} has 3 upright keywords`);
  assert.equal(card.kwRev.length, 3, `${card.key} has 3 reversed keywords`);
  for (const kw of [...card.kwUp, ...card.kwRev]) {
    assert.ok(typeof kw === "string" && kw.length > 0, `${card.key} keywords are non-empty strings`);
  }
}

// --- Page structure ------------------------------------------------------
for (const id of ["draw-one", "draw-three", "reveal-all", "history-list", "clear-history", "lang-ja", "lang-en"]) {
  assert.ok(html.includes(`id="${id}"`), `tarot.html needs #${id}`);
}
assert.ok(html.includes("magi.tarot.history.v1"), "history is stored under a versioned localStorage key");
assert.ok(html.includes("エンターテインメント"), "Japanese entertainment disclaimer is present");
assert.ok(html.includes("entertainment purposes only"), "English entertainment disclaimer is present");

// --- Inline script parses -------------------------------------------------
const script = html.match(/<script>\n([\s\S]*?)\n<\/script>/);
assert.ok(script, "tarot.html has an inline script");
new vm.Script(script[1]); // throws on syntax error, without executing

console.log(`frontend tarot test passed (${cards.length} cards, ja/en complete)`);
