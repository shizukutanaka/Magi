import { createReading, dailyReading, fetchSystems } from "./api.js";
import { currentLanguage, resolveBrowserLanguage, setLanguage, setPageTitle, translate } from "./i18n.js";
import { addHistory, clearHistory, deriveSubjectToken, exportHistory, loadHistory } from "./store.js";

const state = {
  systems: [],
  activeReadingSubject: null,
  activeInput: null,
  activeReadings: [],
  activeDaily: false,
  lang: "ja",
};

const panels = [...document.querySelectorAll("[data-view-panel]")];
const status = document.querySelector("#status");
const engineSelect = document.querySelector("#engine-id");
const readingSubmit = document.querySelector("#reading-form button[type=submit]");
const dailyButton = document.querySelector("#daily-button");
let readingInFlight = false;

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function setStatus(message = "") {
  status.textContent = message;
}

function setReadingInFlight(inFlight) {
  readingInFlight = inFlight;
  readingSubmit.disabled = inFlight;
  dailyButton.disabled = inFlight;
}

function showView(view, { focus = false } = {}) {
  setPageTitle(view);
  panels.forEach((panel) => {
    panel.hidden = panel.id !== `view-${view}`;
  });
  const currentView = view === "result" ? "reading-form" : view;
  document.querySelectorAll("[data-view]").forEach((button) => {
    if (button.dataset.view === currentView) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  if (focus) {
    const panel = document.querySelector(`#view-${view}`);
    const target = view === "result" ? panel : panel?.querySelector("h1");
    target?.focus();
  }
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
  document.querySelector("#question-field").hidden = false;
  document.querySelector("#full-name-field").hidden = false;
  document.querySelector("#spread-field").hidden = engineSelect.value !== "tarot";
  document.querySelector("#birth-date").required = required.has("birth_date");
  document.querySelector("#full-name").required = required.has("full_name");
  document.querySelector("#question").required = required.has("question");
  updateLabel("#question-label", required.has("question") ? "form.question" : "form.question_optional");
  updateLabel("#full-name-label", required.has("full_name") ? "form.full_name" : "form.full_name_optional");
}

function updateLabel(selector, key) {
  const label = document.querySelector(selector);
  if (label) label.textContent = translate(key);
}

function populateSystems() {
  const selected = engineSelect.value;
  engineSelect.replaceChildren();
  state.systems.forEach((system) => {
    const option = element("option", `${system.name} — ${system.tradition}`);
    option.value = system.id;
    engineSelect.append(option);
  });
  if (state.systems.some((system) => system.id === selected)) engineSelect.value = selected;
  updateFields();
}

function inputFromForm() {
  const value = {
    target_date: document.querySelector("#target-date").value,
    question: document.querySelector("#question").value || undefined,
    birth_date: document.querySelector("#birth-date").value || undefined,
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
  document.querySelector("#full-name").value = params.get("name") || "";
  document.querySelector("#spread").value = params.get("spread") || "three-card";
  updateFields();
}

function queryForReading(engineId, input, subjectToken, lang = state.lang) {
  const params = new URLSearchParams();
  params.set("engine", engineId);
  params.set("date", input.target_date);
  if (input.question) params.set("q", input.question);
  if (input.birth_date) params.set("birth", input.birth_date);
  if (input.full_name) params.set("name", input.full_name);
  if (input.options?.spread) params.set("spread", input.options.spread);
  params.set("s", subjectToken);
  params.set("lang", lang);
  return `${window.location.origin}${window.location.pathname}#${params.toString()}`;
}

function queryForDaily(input, subjectToken, lang = state.lang) {
  const params = new URLSearchParams();
  params.set("daily", "1");
  params.set("date", input.target_date);
  if (input.question) params.set("q", input.question);
  if (input.birth_date) params.set("birth", input.birth_date);
  if (input.full_name) params.set("name", input.full_name);
  params.set("s", subjectToken);
  params.set("lang", lang);
  return `${window.location.origin}${window.location.pathname}#${params.toString()}`;
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
    button.textContent = translate("result.copied");
    window.setTimeout(() => {
      button.textContent = original;
    }, 1500);
  } catch {
    setStatus(translate("status.copy_failed"));
  }
}

function saveReading(reading, input, subjectToken) {
  const url = queryForReading(reading.engine_id, input, subjectToken);
  const saved = addHistory({
    engine_id: reading.engine_id,
    engine_name: reading.engine_name,
    tradition: reading.tradition,
    seed: reading.seed,
    summary: reading.summary,
    score: reading.score,
    generated_at: reading.generated_at,
    url,
  });
  return { url, saved };
}

function formatTimestamp(value) {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  const pad = (part) => String(part).padStart(2, "0");
  return `${parsed.getFullYear()}/${pad(parsed.getMonth() + 1)}/${pad(parsed.getDate())} ${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`;
}

function renderReading(reading, input, subjectToken) {
  const card = element("article", undefined, "reading-card");
  const heading = element("h2", reading.engine_name);
  card.append(heading, element("p", reading.tradition, "tradition"), textWithLabel(translate("result.summary"), reading.summary));
  if (reading.interpretation_lang !== reading.lang) {
    card.append(element("p", translate("result.interpretation_notice"), "privacy-note"));
  }
  const drawn = element("ul", undefined, "drawn-list");
  reading.drawn.forEach((symbol) => {
    const marker = symbol.reversed ? translate("result.reversed") : "";
    drawn.append(element("li", `${symbol.name}${marker} — ${symbol.position}`));
  });
  card.append(drawn);
  reading.sections.forEach((section) => {
    const sectionNode = element("section", undefined, "reading-section");
    sectionNode.append(element("h3", section.title), element("p", section.body));
    card.append(sectionNode);
  });
  if (reading.score !== null && reading.score !== undefined) card.append(textWithLabel(translate("result.score"), reading.score));
  if (reading.lucky) {
    const lucky = element("section", undefined, "reading-section");
    lucky.append(element("h3", translate("result.lucky")));
    lucky.append(
      textWithLabel(translate("result.color"), reading.lucky.color),
      textWithLabel(translate("result.number"), reading.lucky.number),
      textWithLabel(translate("result.direction"), reading.lucky.direction),
      textWithLabel(translate("result.item"), reading.lucky.item),
    );
    card.append(lucky);
  }
  const url = queryForReading(reading.engine_id, input, subjectToken);
  const seedBox = element("div", undefined, "seed-box");
  seedBox.append(
    element("span", translate("result.reproducibility")),
    element("code", reading.seed),
  );
  const actions = element("div", undefined, "symbol-actions");
  const copySeed = element("button", translate("result.copy_seed"));
  copySeed.type = "button";
  copySeed.addEventListener("click", () => copyValue(reading.seed, copySeed));
  const share = element("button", translate("result.copy_share"));
  share.type = "button";
  share.addEventListener("click", () => copyValue(url, share));
  actions.append(copySeed, share);
  seedBox.append(actions);
  card.append(seedBox);
  return card;
}

function renderResults(readings, input, subjectToken, { overview, score, daily = false } = {}) {
  const result = document.querySelector("#result");
  result.replaceChildren();
  result.append(element("p", translate("result.eyebrow"), "eyebrow"), element("h1", translate("result.title")));
  if (overview) result.append(element("p", overview, "lead"));
  if (score !== undefined && score !== null) result.append(textWithLabel(translate("result.average_score"), score));
  if (daily) {
    const dailyShare = element("button", translate("result.copy_daily"));
    dailyShare.type = "button";
    dailyShare.addEventListener("click", () => copyValue(queryForDaily(input, subjectToken), dailyShare));
    result.append(dailyShare);
  }
  let historyFailed = false;
  readings.forEach((reading) => {
    if (!saveReading(reading, input, subjectToken).saved) historyFailed = true;
    result.append(renderReading(reading, input, subjectToken));
  });
  if (daily) result.append(element("p", translate("result.traditions_may_disagree"), "privacy-note"));
  const disclaimer = readings.find((reading) => reading.disclaimer)?.disclaimer;
  if (disclaimer) result.append(element("p", disclaimer, "privacy-note"));
  if (historyFailed) setStatus(translate("status.history_unavailable"));
  state.activeReadings = readings;
  state.activeInput = input;
  state.activeDaily = daily;
  state.activeReadingSubject = subjectToken;
  showView("result", { focus: true });
}

async function runDaily(params = {}) {
  if (readingInFlight) return;
  setReadingInFlight(true);
  setStatus(translate("status.daily"));
  const input = {
    target_date: params.date || today(),
    question: params.question || undefined,
    birth_date: params.birth_date || undefined,
    full_name: params.full_name || undefined,
    options: {},
  };
  try {
    const subjectToken = params.subjectToken === undefined
      ? deriveSubjectToken("daily", input)
      : params.subjectToken;
    const response = await dailyReading({ ...input, subject_key: subjectToken, lang: state.lang });
    setStatus("");
    renderResults(response.readings, input, subjectToken, {
      overview: response.overview,
      score: response.score,
      daily: true,
    });
  } catch (error) {
    setStatus(error.message || translate("status.network"));
  } finally {
    setReadingInFlight(false);
  }
}

async function runReading(input = inputFromForm(), engineId = engineSelect.value, subjectToken) {
  if (readingInFlight) return;
  setReadingInFlight(true);
  setStatus(translate("status.reading"));
  try {
    const token = subjectToken === undefined ? deriveSubjectToken(engineId, input) : subjectToken;
    const reading = await createReading({ engine_id: engineId, input, subject_key: token, lang: state.lang });
    setStatus("");
    renderResults([reading], input, token, {});
  } catch (error) {
    setStatus(error.message || translate("status.network"));
  } finally {
    setReadingInFlight(false);
  }
}

function renderHistory() {
  const list = document.querySelector("#history-list");
  list.replaceChildren();
  const history = loadHistory();
  if (!history.length) {
    list.append(element("p", translate("history.empty"), "privacy-note"));
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
    if (entry.score !== null && entry.score !== undefined) link.append(textWithLabel(translate("result.score"), entry.score));
    list.append(link);
  });
}

function readUrl() {
  const fragment = window.location.hash.replace(/^#/, "");
  return new URLSearchParams(fragment || window.location.search);
}

function setupEvents() {
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      const view = button.dataset.view;
      if (view === "history") renderHistory();
      showView(view, { focus: true });
    });
  });
  engineSelect.addEventListener("change", updateFields);
  document.querySelector("#language-select").addEventListener("change", (event) => changeLanguage(event.target.value));
  document.querySelector("#daily-button").addEventListener("click", () => runDaily());
  document.querySelector("#reading-form").addEventListener("submit", (event) => {
    event.preventDefault();
    runReading();
  });
  window.addEventListener("hashchange", () => window.location.reload());
  document.querySelector("#export-history").addEventListener("click", () => exportHistory());
  document.querySelector("#clear-history").addEventListener("click", () => {
    clearHistory();
    renderHistory();
    setStatus(translate("status.deleted"));
  });
}

async function changeLanguage(lang) {
  const previousEngine = engineSelect.value;
  state.lang = lang;
  setLanguage(lang);
  state.systems = await fetchSystems(state.lang);
  populateSystems();
  if (state.activeReadings.length && state.activeInput) {
    if (state.activeDaily) {
      await runDaily({
        date: state.activeInput.target_date,
        question: state.activeInput.question,
        birth_date: state.activeInput.birth_date,
        full_name: state.activeInput.full_name,
        subjectToken: state.activeReadingSubject,
      });
    } else {
      await runReading(state.activeInput, previousEngine, state.activeReadingSubject);
    }
  }
}

async function init() {
  state.lang = resolveBrowserLanguage(readUrl());
  setLanguage(state.lang);
  document.querySelector("#language-select").value = state.lang;
  document.querySelector("#target-date").value = today();
  setupEvents();
  showView("landing");
  try {
    state.systems = await fetchSystems(state.lang);
    populateSystems();
    const params = readUrl();
    if (params.get("engine") || params.get("daily") === "1") {
      fillForm(params);
      const rawSubject = params.get("s")?.trim();
      const deepLinkSubject = rawSubject ? rawSubject : undefined;
      if (params.get("daily") === "1") {
        await runDaily({
          date: params.get("date") || today(),
          question: params.get("q"),
          birth_date: params.get("birth"),
          full_name: params.get("name"),
          subjectToken: deepLinkSubject,
        });
      } else {
        await runReading(inputFromForm(), params.get("engine"), deepLinkSubject);
      }
      if (!deepLinkSubject && state.activeReadings.length) setStatus(translate("status.share_incomplete"));
    }
  } catch (error) {
    setStatus(error.message || translate("status.network"));
  }
}

init();
