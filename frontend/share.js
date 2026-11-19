export const TAROT_ENGINE_ID = "tarot";

export function shareUrl(base, engineId, input, subjectToken, lang) {
  const params = new URLSearchParams();
  params.set("engine", engineId);
  params.set("date", input.target_date);
  if (input.question) params.set("q", input.question);
  if (input.birth_date) params.set("birth", input.birth_date);
  if (input.full_name) params.set("name", input.full_name);
  if (input.options?.spread) params.set("spread", input.options.spread);
  params.set("s", subjectToken);
  params.set("lang", lang);
  return `${base}#${params.toString()}`;
}

export function readShareParams(hash, search) {
  const fragment = hash.replace(/^#/, "");
  return new URLSearchParams(fragment || search);
}

export function inputFromShareParams(params, fallbackDate) {
  return {
    target_date: params.get("date") || fallbackDate,
    question: params.get("q") || undefined,
    birth_date: params.get("birth") || undefined,
    full_name: params.get("name") || undefined,
    options: { spread: params.get("spread") || "three-card" },
  };
}

export function isUnsupportedShare(params) {
  return params.get("daily") === "1" || (params.has("engine") && params.get("engine") !== TAROT_ENGINE_ID);
}
