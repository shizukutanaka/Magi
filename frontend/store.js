const SUBJECT_KEY = "magi.subject_key";
const HISTORY_KEY = "magi.history";
const HISTORY_LIMIT = 100;

export function getSubjectKey() {
  let subjectKey = localStorage.getItem(SUBJECT_KEY);
  if (!subjectKey) {
    subjectKey = crypto.randomUUID();
    localStorage.setItem(SUBJECT_KEY, subjectKey);
  }
  return subjectKey;
}

export function loadHistory() {
  try {
    const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    return Array.isArray(history) ? history : [];
  } catch {
    return [];
  }
}

export function addHistory(entry) {
  const history = [entry, ...loadHistory()].slice(0, HISTORY_LIMIT);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
  return history;
}

export function clearHistory() {
  localStorage.removeItem(HISTORY_KEY);
}

export function exportHistory() {
  const blob = new Blob([JSON.stringify(loadHistory(), null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "magi-history.json";
  link.click();
  URL.revokeObjectURL(url);
}
