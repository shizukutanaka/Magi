const CATALOGS = {
  ja: {
    "nav.daily": "今日の三賢者",
    "nav.reading": "鑑定",
    "nav.history": "履歴",
    "nav.aria": "メインナビゲーション",
    "language.label": "言語",
    "landing.eyebrow": "Magi / Daily Magi",
    "landing.title": "今日の三賢者",
    "landing.lead": "異なる伝統の象徴を並べ、今日の問いを静かに見つめます。",
    "landing.start": "今日の鑑定をはじめる",
    "privacy.note": "ログイン不要。入力は鑑定計算にのみ使われ、サーバには保存されません。",
    "reading.eyebrow": "Magi / Reading",
    "reading.title": "鑑定",
    "form.engine": "占術",
    "form.date": "対象日",
    "form.question": "問い",
    "form.question_optional": "問い（任意）",
    "form.question_placeholder": "いま心にある問い",
    "form.birth_date": "生年月日",
    "form.birth_time": "出生時刻",
    "form.full_name": "氏名",
    "form.full_name_optional": "氏名（任意）",
    "form.spread": "スプレッド",
    "form.spread_three": "スリーカード",
    "form.spread_celtic": "ケルト十字",
    "form.submit": "鑑定する",
    "history.eyebrow": "Magi / Local History",
    "history.title": "履歴",
    "history.export": "エクスポート",
    "history.clear": "全削除",
    "history.empty": "まだ履歴はありません。",
    "result.eyebrow": "Magi / Result",
    "result.title": "鑑定結果",
    "result.summary": "要約",
    "result.score": "スコア",
    "result.average_score": "平均スコア",
    "result.lucky": "ラッキーアイテム",
    "result.color": "色",
    "result.number": "数字",
    "result.direction": "方角",
    "result.item": "アイテム",
    "result.reversed": "（逆位置）",
    "result.reproducibility": "再現性：同じ入力とシードなら誰でも同じ結果を再現できます。",
    "result.copy_seed": "シードをコピー",
    "result.copy_share": "共有リンクをコピー",
    "result.copy_daily": "この三賢者の共有リンクをコピー",
    "result.copied": "コピーしました",
    "result.interpretation_notice": "この流派の解釈文は現在、日本語のみで提供されています。",
    "status.daily": "三賢者を呼び出しています…",
    "status.reading": "鑑定しています…",
    "status.copy_failed": "コピーに失敗しました。",
    "status.network": "通信に失敗しました。",
    "status.deleted": "履歴を削除しました。",
    "error.unknown_engine": "未知の流派です。",
    "error.check_input": "入力を確認してください。",
    "error.request_failed": "リクエストに失敗しました。",
    "error.missing": "入力が不足しています：{fields}",
    "error.retry": "{seconds}秒待ってから再試行してください。",
    "label.past": "過去",
    "label.present": "現在",
    "label.future": "未来",
  },
  en: {
    "nav.daily": "Daily Magi",
    "nav.reading": "Reading",
    "nav.history": "History",
    "nav.aria": "Main navigation",
    "language.label": "Language",
    "landing.eyebrow": "Magi / Daily Magi",
    "landing.title": "Daily Magi",
    "landing.lead": "Place symbols from different traditions side by side and quietly consider today's question.",
    "landing.start": "Begin today's reading",
    "privacy.note": "No login required. Your input is used only for the reading and is not stored on the server.",
    "reading.eyebrow": "Magi / Reading",
    "reading.title": "Reading",
    "form.engine": "System",
    "form.date": "Date",
    "form.question": "Question",
    "form.question_optional": "Question (optional)",
    "form.question_placeholder": "The question on your mind",
    "form.birth_date": "Birth date",
    "form.birth_time": "Birth time",
    "form.full_name": "Name",
    "form.full_name_optional": "Name (optional)",
    "form.spread": "Spread",
    "form.spread_three": "Three-card",
    "form.spread_celtic": "Celtic Cross",
    "form.submit": "Cast reading",
    "history.eyebrow": "Magi / Local History",
    "history.title": "History",
    "history.export": "Export",
    "history.clear": "Clear all",
    "history.empty": "There are no readings in your history yet.",
    "result.eyebrow": "Magi / Result",
    "result.title": "Reading result",
    "result.summary": "Summary",
    "result.score": "Score",
    "result.average_score": "Average score",
    "result.lucky": "Lucky items",
    "result.color": "Color",
    "result.number": "Number",
    "result.direction": "Direction",
    "result.item": "Item",
    "result.reversed": " (reversed)",
    "result.reproducibility": "Reproducibility: anyone can get the same result from the same input and seed.",
    "result.copy_seed": "Copy seed",
    "result.copy_share": "Copy share link",
    "result.copy_daily": "Copy this Daily Magi link",
    "result.copied": "Copied",
    "result.interpretation_notice": "Interpretations for this system are currently written in Japanese only.",
    "status.daily": "Calling the three sages…",
    "status.reading": "Casting a reading…",
    "status.copy_failed": "Copy failed.",
    "status.network": "Communication failed.",
    "status.deleted": "History deleted.",
    "error.unknown_engine": "Unknown system.",
    "error.check_input": "Please check your input.",
    "error.request_failed": "The request failed.",
    "error.missing": "Missing input: {fields}",
    "error.retry": "Please try again in {seconds} seconds.",
    "label.past": "Past",
    "label.present": "Present",
    "label.future": "Future",
  },
};

export const SUPPORTED_LANGS = ["ja", "en"];
let activeLang = "ja";

export function translate(key, params = {}) {
  const template = CATALOGS[activeLang][key] ?? CATALOGS.ja[key] ?? key;
  return template.replace(/\{(\w+)\}/g, (_, name) => String(params[name] ?? ""));
}

export function currentLanguage() {
  return activeLang;
}

export function resolveBrowserLanguage(params = new URLSearchParams(window.location.search)) {
  const explicit = params.get("lang")?.toLowerCase().split("-")[0];
  const stored = localStorage.getItem("magi.lang")?.toLowerCase().split("-")[0];
  const browser = navigator.language?.toLowerCase().split("-")[0];
  return SUPPORTED_LANGS.includes(explicit) ? explicit
    : SUPPORTED_LANGS.includes(stored) ? stored
      : SUPPORTED_LANGS.includes(browser) ? browser : "ja";
}

export function setLanguage(lang, { persist = true } = {}) {
  activeLang = SUPPORTED_LANGS.includes(lang) ? lang : "ja";
  if (persist) localStorage.setItem("magi.lang", activeLang);
  document.documentElement.lang = activeLang;
  document.title = activeLang === "en" ? "Magi — Daily Magi" : "Magi — 今日の三賢者";
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = translate(node.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    node.placeholder = translate(node.dataset.i18nPlaceholder);
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((node) => {
    node.setAttribute("aria-label", translate(node.dataset.i18nAriaLabel));
  });
}
