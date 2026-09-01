const FIELD_NAMES = {
  birth_date: "生年月日",
  birth_time: "出生時刻",
  full_name: "氏名",
  question: "問い",
};

function normalizeError(response, payload) {
  if (response.status === 429) {
    const retryAfter = response.headers.get("Retry-After");
    const seconds = Number.parseInt(retryAfter || "60", 10);
    return { status: 429, message: `${Number.isNaN(seconds) ? 60 : seconds}秒待ってから再試行してください。` };
  }
  if (response.status === 404) {
    return { status: 404, message: "未知の流派です。" };
  }
  if (response.status === 422) {
    const detail = payload?.detail;
    if (detail && typeof detail === "object" && Array.isArray(detail.missing_fields)) {
      const fields = detail.missing_fields.map((field) => FIELD_NAMES[field] || field);
      return { status: 422, message: `入力が不足しています：${fields.join("、")}` };
    }
    return { status: 422, message: typeof detail === "string" ? detail : "入力を確認してください。" };
  }
  const detail = payload?.detail;
  return {
    status: response.status,
    message: typeof detail === "string" ? detail : "リクエストに失敗しました。",
  };
}

async function requestJson(url, options) {
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw { status: 0, message: "通信に失敗しました。" };
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

export function fetchSystems() {
  return requestJson("/api/v1/systems");
}

export function createReading({ engine_id, input, subject_key }) {
  return requestJson("/api/v1/readings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ engine_id, input, subject_key }),
  });
}

export function dailyReading({ target_date, question, birth_date, birth_time, full_name, options, subject_key }) {
  return requestJson("/api/v1/readings/daily", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      target_date,
      question,
      birth_date,
      birth_time,
      full_name,
      options,
      subject_key,
    }),
  });
}
