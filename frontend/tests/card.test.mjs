import assert from "node:assert/strict";

const {
  CARD_WIDTH,
  CARD_HEIGHT,
  buildCardContent,
  canShareFile,
  cardFileName,
  drawnLine,
  luckyLine,
  renderCardImage,
  wrapText,
} = await import("../card.js");

const charMeasure = (text) => [...text].length * 10;

// --- wrapText ---
assert.deepEqual(wrapText("hello world foo", 60, charMeasure), ["hello", "world", "foo"]);
assert.deepEqual(wrapText("あいうえおかきくけこ", 40, charMeasure), ["あいうえ", "おかきく", "けこ"]);
assert.deepEqual(wrapText("あ".repeat(20), 45, charMeasure, 2), ["ああああ", "あああ…"]);
assert.deepEqual(wrapText("", 100, charMeasure), [""]);
assert.deepEqual(wrapText("one\ntwo", 100, charMeasure), ["one", "two"]);

// --- buildCardContent / drawnLine / luckyLine ---
const labels = {
  score: "スコア",
  lucky: "ラッキーアイテム",
  color: "色",
  number: "数字",
  direction: "方角",
  item: "アイテム",
  reversed: "（逆位置）",
  brand: "Magi",
  site: "https://example.test/",
};

const reading = {
  engine_id: "tarot",
  engine_name: "タロット",
  tradition: "西洋",
  summary: "今日は良い日です。",
  drawn: [
    { name: "太陽", position: "現在", reversed: false },
    { name: "月", position: "過去", reversed: true },
  ],
  score: null,
  lucky: { color: "赤", number: 7, direction: "東", item: "鍵" },
  generated_at: "2026-11-16T12:00:00Z",
};

const content = buildCardContent(reading);
assert.equal(content.title, "タロット");
assert.equal(content.tradition, "西洋");
assert.equal(content.score, null);
assert.equal(content.drawn[1].reversed, true);
assert.equal(content.lucky.number, "7");

assert.equal(drawnLine(content.drawn[0], labels), "太陽 — 現在");
assert.equal(drawnLine(content.drawn[1], labels), "月（逆位置） — 過去");
assert.equal(drawnLine({ name: "星", position: "", reversed: false }, labels), "星");
assert.equal(
  luckyLine(content.lucky, labels),
  "ラッキーアイテム: 色: 赤 / 数字: 7 / 方角: 東 / アイテム: 鍵",
);

const bare = buildCardContent({ engine_name: "易経", tradition: "中国", summary: "x", drawn: [], score: 42, lucky: null });
assert.equal(bare.score, 42);
assert.equal(bare.lucky, null);

// --- renderCardImage with a stub canvas ---
function fakeCanvas() {
  const texts = [];
  const ctx = {
    fillStyle: "",
    font: "",
    textBaseline: "",
    fillRect() {},
    fillText(text, x, y) {
      texts.push({ text, x, y });
    },
    measureText(text) {
      const size = Number(/(\d+)px/.exec(this.font)?.[1] ?? 10);
      return { width: [...text].length * size * 0.5 };
    },
  };
  return {
    canvas: { width: 0, height: 0, getContext: () => ctx },
    texts,
  };
}

const { canvas, texts } = fakeCanvas();
const rendered = renderCardImage(reading, labels, () => canvas);
assert.equal(rendered, canvas);
assert.equal(canvas.width, CARD_WIDTH);
assert.equal(canvas.height, CARD_HEIGHT);
const drawnTexts = texts.map((entry) => entry.text);
assert.ok(drawnTexts.includes("タロット"), "title is drawn");
assert.ok(drawnTexts.includes("西洋"), "tradition is drawn");
assert.ok(drawnTexts.includes("今日は良い日です。"), "summary is drawn");
assert.ok(drawnTexts.some((text) => text.includes("太陽 — 現在")), "drawn symbols are drawn");
assert.ok(drawnTexts.some((text) => text.includes("ラッキーアイテム")), "lucky line is drawn");
assert.ok(drawnTexts.includes("Magi"), "brand attribution is drawn");
const siteEntry = texts.find((entry) => entry.text === "https://example.test/");
assert.ok(siteEntry, "site attribution is drawn");
assert.ok(siteEntry.x > 64, "site attribution is right-aligned");

// score is only drawn when present
const scored = fakeCanvas();
renderCardImage({ ...reading, score: 88, lucky: null }, labels, () => scored.canvas);
assert.ok(scored.texts.some((entry) => entry.text === "スコア: 88"), "score is drawn when present");
assert.ok(!scored.texts.some((entry) => entry.text.includes("ラッキーアイテム")), "lucky line omitted when absent");

// --- cardFileName / canShareFile ---
assert.equal(cardFileName(reading), "magi-tarot-2026-11-16.png");
assert.equal(cardFileName({ engine_id: "iching" }), "magi-iching.png");
assert.equal(cardFileName({ engine_id: "a/b c", generated_at: "2026-01-02" }), "magi-abc-2026-01-02.png");
assert.equal(cardFileName({}), "magi-reading.png");

const file = { name: "x.png" };
assert.equal(canShareFile(null, file), false);
assert.equal(canShareFile({}, file), false);
assert.equal(canShareFile({ share() {}, canShare: () => true }, file), true);
assert.equal(canShareFile({ share() {}, canShare: () => false }, file), false);
assert.equal(canShareFile({ share() {}, canShare() { throw new Error("nope"); } }, file), false);

console.log("frontend result card tests passed");
