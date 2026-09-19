import assert from "node:assert/strict";

const values = new Map();
globalThis.localStorage = {
  getItem(key) {
    return values.has(key) ? values.get(key) : null;
  },
  setItem(key, value) {
    values.set(key, String(value));
  },
  removeItem(key) {
    values.delete(key);
  },
};

const { addHistory, loadHistory } = await import("../store.js");

function entry(seed, overrides = {}) {
  return {
    engine_id: "tarot",
    engine_name: "Tarot",
    tradition: "Western",
    seed,
    summary: `summary-${seed}`,
    score: null,
    generated_at: `2026-09-${seed}`,
    url: `https://example.test/${seed}`,
    ...overrides,
  };
}

function reset(entries = []) {
  values.set("magi.history", JSON.stringify(entries));
}

reset([
  entry("first", { generated_at: "2026-09-01T00:00:00Z" }),
  entry("second", { generated_at: "2026-09-02T00:00:00Z" }),
]);
assert.equal(addHistory(entry("second", {
  summary: "updated summary",
  url: "https://example.test/updated",
  engine_name: "タロット",
  tradition: "西洋",
  score: 3,
  generated_at: "2026-09-30T00:00:00Z",
})), true);
let history = loadHistory();
assert.equal(history.length, 2);
assert.equal(history[0].seed, "first");
assert.equal(history[1].seed, "second");
assert.equal(history[1].generated_at, "2026-09-02T00:00:00Z");
assert.equal(history[1].summary, "updated summary");
assert.equal(history[1].url, "https://example.test/updated");
assert.equal(history[1].engine_name, "タロット");
assert.equal(history[1].tradition, "西洋");
assert.equal(history[1].score, 3);

assert.equal(addHistory(entry("new")), true);
history = loadHistory();
assert.deepEqual(history.map((item) => item.seed), ["new", "first", "second"]);

const legacy = { engine_id: "legacy", summary: "keep me", generated_at: "old" };
reset([legacy, entry("existing")]);
assert.equal(addHistory(entry("fresh")), true);
history = loadHistory();
assert.deepEqual(history[1], legacy);
assert.deepEqual(history.map((item) => item.seed), ["fresh", undefined, "existing"]);

reset([]);
for (let index = 0; index < 101; index += 1) addHistory(entry(`seed-${index}`));
history = loadHistory();
assert.equal(history.length, 100);
assert.equal(history[0].seed, "seed-100");
assert.equal(history.at(-1).seed, "seed-1");

console.log("store history tests passed");
