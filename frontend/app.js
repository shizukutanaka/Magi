import { createReading, dailyReading, fetchSystems } from "./api.js";
import { addHistory, clearHistory, exportHistory, getSubjectKey, loadHistory } from "./store.js";

const state = {
  systems: [],
  activeSubjectKey: null,
  activeInput: null,
  activeReadings: [],
};

const panels = [...document.querySelectorAll("[data-view-panel]")];
const status = document.querySelector("#status");
const engineSelect = document.querySelector("#engine-id");

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function setStatus(message = "") {
  status.textContent = message;
}

function showView(view) {
  panels.forEach((panel) => {
    panel.hidden = panel.id !== `view-${view}`;
  });
}

function today() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function selectedSystem() {
  return state.systems.find((system) => system.id === engineSelect.value);
}

function updateFields() {
  const system = selectedSystem();
  const required = new Set(system?.required_fields || []);
  document.querySelector("#birth-date-field").hidden = !required.has("birth_date");
  document.querySelector("#birth-time-field").hidden = !required.has("birth_time");
  document.querySelector("#question-field").hidden = false;
  document.querySelector("#full-name-field").hidden = false;
  document.querySelector("#spread-field").hidden = engineSelect.value !== "tarot";
  document.querySelector("#birth-date").required = required.has("birth_date");
  document.querySelector("#birth-time").required = required.has("birth_time");
  document.querySelector("#full-name").required = required.has("full_name");
  document.querySelector("#question").required = required.has("question");
  updateLabel("#question-field", required.has("question") ? "問い" : "問い（任意）");
  updateLabel("#full-name-field", required.has("full_name") ? "氏名" : "氏名（任意）");
}

function updateLabel(selector, text) {
  const label = document.querySelector(selector);
  const textNode = [...label.childNodes].find((node) => node.nodeType === Node.TEXT_NODE);
  if (textNode) textNode.nodeValue = text;
}

function populateSystems() {
  state.systems.forEach((system) => {
    const option = element("option", `${system.name} — ${system.tradition}`);
    option.value = system.id;
    engineSelect.append(option);
  });
  updateFields();
}

function inputFromForm() {
  const value = {
    target_date: document.querySelector("#target-date").value,
    question: document.querySelector("#question").value || undefined,
    birth_date: document.querySelector("#birth-date").value || undefined,
    birth_time: document.querySelector("#birth-time").value || undefined,
    full_name: document.querySelector("#full-name").value || undefined,
    options: {},
  };
  if (engineSelect.value === "tarot") {
    value.options.spread = document.querySelector("#spread").value;
  }
  return value;
}

function fillForm(params) {
  if (params.get("engine") && state.systems.some((system) => system.id === params.get("engine"))) {
    engineSelect.value = params.get("engine");
  }
  document.querySelector("#target-date").value = params.get("date") || today();
  document.querySelector("#question").value = params.get("q") || "";
  document.querySelector("#birth-date").value = params.get("birth") || "";
  document.querySelector("#birth-time").value = params.get("time") || "";
  document.querySelector("#full-name").value = params.get("name") || "";
  document.querySelector("#spread").value = params.get("spread") || "three-card";
  updateFields();
}

function queryForReading(engineId, input, subjectKey) {
  const params = new URLSearchParams();
  params.set("engine", engineId);
  params.set("date", input.target_date);
  if (input.question) params.set("q", input.question);
  if (input.birth_date) params.set("birth", input.birth_date);
  if (input.birth_time) params.set("time", input.birth_time);
  if (input.full_name) params.set("name", input.full_name);
  if (input.options?.spread) params.set("spread", input.options.spread);
  params.set("s", subjectKey);
  return `${window.location.origin}${window.location.pathname}?${params.toString()}`;
}

function queryForDaily(input, subjectKey) {
  const params = new URLSearchParams();
  params.set("daily", "1");
  params.set("date", input.target_date);
  if (input.question) params.set("q", input.question);
  if (input.birth_date) params.set("birth", input.birth_date);
  if (input.birth_time) params.set("time", input.birth_time);
  if (input.full_name) params.set("name", input.full_name);
  params.set("s", subjectKey);
  return `${window.location.origin}${window.location.pathname}?${params.toString()}`;
}

function textWithLabel(label, value) {
  const wrapper = element("p");
  wrapper.append(element("strong", `${label}: `), document.createTextNode(String(value ?? "")));
  return wrapper;
}

async function copyValue(value, button) {
  try {
    await navigator.clipboard.writeText(value);
    const original = button.textContent;
    button.textContent = "コピーしました";
    window.setTimeout(() => {
      button.textContent = original;
    }, 1500);
  } catch {
    setStatus("コピーに失敗しました。");
  }
}

function saveReading(reading, input, subjectKey) {
  const url = queryForReading(reading.engine_id, input, subjectKey);
  addHistory({
    engine_id: reading.engine_id,
    engine_name: reading.engine_name,
    tradition: reading.tradition,
    seed: reading.seed,
    summary: reading.summary,
    score: reading.score,
    generated_at: reading.generated_at,
    url,
  });
  return url;
}

function formatTimestamp(value) {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  const pad = (part) => String(part).padStart(2, "0");
  return `${parsed.getFullYear()}/${pad(parsed.getMonth() + 1)}/${pad(parsed.getDate())} ${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`;
}

function renderReading(reading, input, subjectKey) {
  const card = element("article", undefined, "reading-card");
  const heading = element("h2", reading.engine_name);
  card.append(heading, element("p", reading.tradition, "tradition"), textWithLabel("要約", reading.summary));
  const drawn = element("ul", undefined, "drawn-list");
  reading.drawn.forEach((symbol) => {
    const marker = symbol.reversed ? "（逆位置）" : "";
    drawn.append(element("li", `${symbol.name}${marker} — ${symbol.position}`));
  });
  card.append(drawn);
  reading.sections.forEach((section) => {
    const sectionNode = element("section", undefined, "reading-section");
    sectionNode.append(element("h3", section.title), element("p", section.body));
    card.append(sectionNode);
  });
  if (reading.score !== null && reading.score !== undefined) card.append(textWithLabel("スコア", reading.score));
  if (reading.lucky) {
    const lucky = element("section", undefined, "reading-section");
    lucky.append(element("h3", "ラッキーアイテム"));
    lucky.append(
      textWithLabel("色", reading.lucky.color),
      textWithLabel("数字", reading.lucky.number),
      textWithLabel("方角", reading.lucky.direction),
      textWithLabel("アイテム", reading.lucky.item),
    );
    card.append(lucky);
  }
  const url = queryForReading(reading.engine_id, input, subjectKey);
  const seedBox = element("div", undefined, "seed-box");
  seedBox.append(
    element("span", "再現性：同じ入力とシードなら誰でも同じ結果を再現できます。"),
    element("code", reading.seed),
  );
  const actions = element("div", undefined, "symbol-actions");
  const copySeed = element("button", "シードをコピー");
  copySeed.type = "button";
  copySeed.addEventListener("click", () => copyValue(reading.seed, copySeed));
  const share = element("button", "共有リンクをコピー");
  share.type = "button";
  share.addEventListener("click", () => copyValue(url, share));
  actions.append(copySeed, share);
  seedBox.append(actions);
  card.append(seedBox);
  return card;
}

function renderResults(readings, input, subjectKey, { overview, score, daily = false } = {}) {
  const result = document.querySelector("#result");
  result.replaceChildren();
  result.append(element("p", "Magi / Result", "eyebrow"), element("h1", "鑑定結果"));
  if (overview) result.append(element("p", overview, "lead"));
  if (score !== undefined && score !== null) result.append(textWithLabel("平均スコア", score));
  if (daily) {
    const dailyShare = element("button", "この三賢者の共有リンクをコピー");
    dailyShare.type = "button";
    dailyShare.addEventListener("click", () => copyValue(queryForDaily(input, subjectKey), dailyShare));
    result.append(dailyShare);
  }
  readings.forEach((reading) => {
    saveReading(reading, input, subjectKey);
    result.append(renderReading(reading, input, subjectKey));
  });
  state.activeReadings = readings;
  state.activeInput = input;
  showView("result");
}

async function runDaily(params = {}) {
  setStatus("三賢者を呼び出しています…");
  const input = {
    target_date: params.date || today(),
    question: params.question || undefined,
    birth_date: params.birth_date || undefined,
    birth_time: params.birth_time || undefined,
    full_name: params.full_name || undefined,
    options: {},
  };
  try {
    const subjectKey = params.subjectKey || state.activeSubjectKey;
    const response = await dailyReading({ ...input, subject_key: subjectKey });
    renderResults(response.readings, input, subjectKey, {
      overview: response.overview,
      score: response.score,
      daily: true,
    });
    setStatus("");
  } catch (error) {
    setStatus(error.message || "通信に失敗しました。");
  }
}

async function runReading(input = inputFromForm(), engineId = engineSelect.value, subjectKey = state.activeSubjectKey) {
  setStatus("鑑定しています…");
  try {
    const reading = await createReading({ engine_id: engineId, input, subject_key: subjectKey });
    renderResults([reading], input, subjectKey, {});
    setStatus("");
  } catch (error) {
    setStatus(error.message || "通信に失敗しました。");
  }
}

function renderHistory() {
  const list = document.querySelector("#history-list");
  list.replaceChildren();
  const history = loadHistory();
  if (!history.length) {
    list.append(element("p", "まだ履歴はありません。", "privacy-note"));
    return;
  }
  history.forEach((entry) => {
    const link = element("a", undefined, "history-item");
    link.href = entry.url;
    link.append(
      element("h2", entry.engine_name),
      element("p", `${entry.tradition} · ${formatTimestamp(entry.generated_at)}`, "meta"),
      element("p", entry.summary),
    );
    if (entry.score !== null && entry.score !== undefined) link.append(textWithLabel("スコア", entry.score));
    list.append(link);
  });
}

function readUrl() {
  return new URLSearchParams(window.location.search);
}

function setupEvents() {
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      const view = button.dataset.view;
      if (view === "history") renderHistory();
      showView(view);
    });
  });
  engineSelect.addEventListener("change", updateFields);
  document.querySelector("#daily-button").addEventListener("click", () => runDaily());
  document.querySelector("#reading-form").addEventListener("submit", (event) => {
    event.preventDefault();
    runReading();
  });
  document.querySelector("#export-history").addEventListener("click", () => exportHistory());
  document.querySelector("#clear-history").addEventListener("click", () => {
    clearHistory();
    renderHistory();
    setStatus("履歴を削除しました。");
  });
}

async function init() {
  state.activeSubjectKey = getSubjectKey();
  document.querySelector("#target-date").value = today();
  setupEvents();
  try {
    state.systems = await fetchSystems();
    populateSystems();
    const params = readUrl();
    if (params.get("engine") || params.get("daily") === "1") {
      fillForm(params);
      const deepLinkSubject = params.get("s") || state.activeSubjectKey;
      if (params.get("daily") === "1") {
        await runDaily({
          date: params.get("date") || today(),
          question: params.get("q"),
          birth_date: params.get("birth"),
          birth_time: params.get("time"),
          full_name: params.get("name"),
          subjectKey: deepLinkSubject,
        });
      } else {
        await runReading(inputFromForm(), params.get("engine"), deepLinkSubject);
      }
    }
  } catch (error) {
    setStatus(error.message || "通信に失敗しました。");
  }
}

init();
