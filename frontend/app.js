import { createReading } from "./api.js";
import { shareCardImage } from "./card.js";
import { resolveBrowserLanguage, setLanguage, setPageTitle, translate } from "./i18n.js";
import { inputFromShareParams, isUnsupportedShare, readShareParams, shareUrl, TAROT_ENGINE_ID } from "./share.js";
import { addHistory, clearHistory, deriveSubjectToken, exportHistory, loadHistory } from "./store.js";

const state = {
  activeReadingSubject: null,
  activeInput: null,
  activeReading: null,
  lang: "ja",
};

const panels = [...document.querySelectorAll("[data-view-panel]")];
const status = document.querySelector("#status");
const readingSubmit = document.querySelector("#reading-form button[type=submit]");
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

function inputFromForm() {
  const value = {
    target_date: document.querySelector("#target-date").value,
    question: document.querySelector("#question").value || undefined,
    birth_date: document.querySelector("#birth-date").value || undefined,
    full_name: document.querySelector("#full-name").value || undefined,
    options: { spread: document.querySelector("#spread").value },
  };
  return value;
}

function fillForm(params) {
  const input = inputFromShareParams(params, today());
  document.querySelector("#target-date").value = input.target_date;
  document.querySelector("#question").value = input.question || "";
  document.querySelector("#birth-date").value = input.birth_date || "";
  document.querySelector("#full-name").value = input.full_name || "";
  document.querySelector("#spread").value = input.options.spread;
}

function queryForReading(engineId, input, subjectToken, lang = state.lang) {
  return shareUrl(`${window.location.origin}${window.location.pathname}`, engineId, input, subjectToken, lang);
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

function cardLabels() {
  return {
    score: translate("result.score"),
    lucky: translate("result.lucky"),
    color: translate("result.color"),
    number: translate("result.number"),
    direction: translate("result.direction"),
    item: translate("result.item"),
    reversed: translate("result.reversed"),
    brand: "Magi",
    site: `${window.location.origin}${window.location.pathname}`,
  };
}

async function shareReadingAsImage(reading) {
  try {
    await shareCardImage(reading, cardLabels());
  } catch {
    setStatus(translate("status.card_failed"));
  }
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
  const shareImage = element("button", translate("result.share_image"));
  shareImage.type = "button";
  shareImage.addEventListener("click", () => shareReadingAsImage(reading));
  actions.append(copySeed, share, shareImage);
  seedBox.append(actions);
  card.append(seedBox);
  return card;
}

function renderResult(reading, input, subjectToken) {
  const result = document.querySelector("#result");
  result.replaceChildren();
  result.append(element("p", translate("result.eyebrow"), "eyebrow"), element("h1", translate("result.title")));
  const { saved } = saveReading(reading, input, subjectToken);
  result.append(renderReading(reading, input, subjectToken));
  if (reading.disclaimer) result.append(element("p", reading.disclaimer, "privacy-note"));
  if (!saved) setStatus(translate("status.history_unavailable"));
  state.activeReading = reading;
  state.activeInput = input;
  state.activeReadingSubject = subjectToken;
  showView("result", { focus: true });
}

async function runReading(input = inputFromForm(), subjectToken) {
  if (readingInFlight) return;
  setReadingInFlight(true);
  setStatus(translate("status.reading"));
  try {
    const token = subjectToken === undefined ? deriveSubjectToken(TAROT_ENGINE_ID, input) : subjectToken;
    const reading = await createReading({ engine_id: TAROT_ENGINE_ID, input, subject_key: token, lang: state.lang });
    setStatus("");
    renderResult(reading, input, token);
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
  return readShareParams(window.location.hash, window.location.search);
}

function setupEvents() {
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      const view = button.dataset.view;
      if (view === "history") renderHistory();
      showView(view, { focus: true });
    });
  });
  document.querySelector("#language-select").addEventListener("change", (event) => changeLanguage(event.target.value));
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
  state.lang = lang;
  setLanguage(lang);
  if (state.activeReading && state.activeInput) {
    await runReading(state.activeInput, state.activeReadingSubject);
  }
}

async function init() {
  state.lang = resolveBrowserLanguage(readUrl());
  setLanguage(state.lang);
  document.querySelector("#language-select").value = state.lang;
  document.querySelector("#target-date").value = today();
  setupEvents();
  showView("reading-form");
  const params = readUrl();
  if (isUnsupportedShare(params)) {
    setStatus(translate("status.unsupported_share"));
    return;
  }
  if (params.get("engine")) {
    fillForm(params);
    const rawSubject = params.get("s")?.trim();
    const deepLinkSubject = rawSubject ? rawSubject : undefined;
    await runReading(inputFromForm(), deepLinkSubject);
    if (!deepLinkSubject && state.activeReading) setStatus(translate("status.share_incomplete"));
  }
}

init();
