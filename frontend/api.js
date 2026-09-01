import { currentLanguage, translate } from "./i18n.js";

const FIELD_NAMES = {
  birth_date: "form.birth_date",
  full_name: "form.full_name",
  question: "form.question",
};

function normalizeError(response, payload) {
  if (response.status === 429) {
    const retryAfter = response.headers.get("Retry-After");
    const seconds = Number.parseInt(retryAfter || "60", 10);
    return { status: 429, message: translate("error.retry", { seconds: Number.isNaN(seconds) ? 60 : seconds }) };
  }
  if (response.status === 404) {
    return { status: 404, message: translate("error.unknown_engine") };
  }
  if (response.status === 422) {
    const detail = payload?.detail;
    if (detail && typeof detail === "object" && Array.isArray(detail.missing_fields)) {
      const fields = detail.missing_fields.map((field) => FIELD_NAMES[field] ? translate(FIELD_NAMES[field]) : field);
      return { status: 422, message: translate("error.missing", { fields: fields.join(currentLanguage() === "ja" ? "、" : ", ") }) };
    }
    return { status: 422, message: typeof detail === "string" ? detail : translate("error.check_input") };
  }
  const detail = payload?.detail;
  return {
    status: response.status,
    message: typeof detail === "string" ? detail : translate("error.request_failed"),
  };
}

async function requestJson(url, options) {
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw { status: 0, message: translate("status.network") };
  }
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    throw normalizeError(response, payload);
  }
  return payload;
}

export function fetchSystems(lang = currentLanguage()) {
  return requestJson(`/api/v1/systems?lang=${encodeURIComponent(lang)}`);
}

export function createReading({ engine_id, input, subject_key, lang = currentLanguage() }) {
  return requestJson("/api/v1/readings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ engine_id, input, subject_key, lang }),
  });
}

export function dailyReading({ target_date, question, birth_date, full_name, options, subject_key, lang = currentLanguage() }) {
  return requestJson("/api/v1/readings/daily", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      target_date,
      question,
      birth_date,
      full_name,
      options,
      subject_key,
      lang,
    }),
  });
}
