const SUBJECT_KEY = "magi.subject_key";
const HISTORY_KEY = "magi.history";
const HISTORY_LIMIT = 100;

// localStorage は「無効化されている」「容量超過」「プライベートモード」で
// 参照も書き込みも例外を投げる。履歴はおまけの機能なので、失敗しても
// 鑑定そのものを壊さないようにここで吸収する。
let memorySubjectKey = null;

function readItem(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeItem(key, value) {
  try {
    localStorage.setItem(key, value);
    return true;
  } catch {
    return false;
  }
}

// crypto.randomUUID は secure context 限定なので、httpでself-hostした場合に
// 存在しない。鍵は「このブラウザを識別するだけ」の値なので段階的に落とす。
function randomId() {
  const webCrypto = globalThis.crypto;
  if (webCrypto && typeof webCrypto.randomUUID === "function") {
    return webCrypto.randomUUID();
  }
  const bytes = new Uint8Array(16);
  if (webCrypto && typeof webCrypto.getRandomValues === "function") {
    webCrypto.getRandomValues(bytes);
  } else {
    for (let index = 0; index < bytes.length; index += 1) {
      bytes[index] = Math.floor(Math.random() * 256);
    }
  }
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function getSubjectKey() {
  const stored = readItem(SUBJECT_KEY);
  if (stored) return stored;
  if (!memorySubjectKey) memorySubjectKey = randomId();
  writeItem(SUBJECT_KEY, memorySubjectKey);
  return memorySubjectKey;
}

export function loadHistory() {
  try {
    const history = JSON.parse(readItem(HISTORY_KEY) || "[]");
    return Array.isArray(history) ? history : [];
  } catch {
    return [];
  }
}

// 保存できたかを返す。呼び出し側は失敗を通知に使い、描画は止めない。
export function addHistory(entry) {
  const history = loadHistory();
  const existingIndex = entry.seed
    ? history.findIndex((item) => item.seed === entry.seed)
    : -1;
  if (existingIndex >= 0) {
    const original = history[existingIndex];
    history[existingIndex] = {
      ...original,
      ...entry,
      generated_at: original.generated_at,
    };
  } else {
    history.unshift(entry);
    history.splice(HISTORY_LIMIT);
  }
  return writeItem(HISTORY_KEY, JSON.stringify(history));
}

export function clearHistory() {
  try {
    localStorage.removeItem(HISTORY_KEY);
  } catch {
    // 消せない環境では保存もできていないので、何もしない。
  }
}

export function exportHistory() {
  const blob = new Blob([JSON.stringify(loadHistory(), null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "magi-history.json";
  link.click();
  // 即座に revoke するとダウンロードが始まらないブラウザがあるため次のタスクで解放する。
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}
