'use strict';

const { DEFAULT_SERVER_URL } = require('./policy');

const PAGE_CSP = "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'";

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[ch]);
}

const STYLE = `
  :root { color-scheme: light dark; font-family: system-ui, -apple-system, "Segoe UI", "Hiragino Sans", "Noto Sans JP", sans-serif; }
  body { margin: 0; padding: 32px; line-height: 1.6; }
  main { max-width: 720px; margin: 0 auto; }
  h1 { font-size: 1.4rem; margin: 0 0 16px; }
  h2 { font-size: 1.05rem; margin: 24px 0 8px; }
  .reason { padding: 12px 16px; border-left: 4px solid #c0392b; background: rgba(192, 57, 43, 0.08); }
  pre { padding: 12px 16px; background: rgba(127, 127, 127, 0.12); overflow-x: auto; }
  code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
  form { display: flex; gap: 8px; flex-wrap: wrap; }
  input[type=url] { flex: 1 1 320px; padding: 6px 8px; font: inherit; }
  button, .button { padding: 6px 14px; font: inherit; cursor: pointer; }
  .actions { display: flex; gap: 12px; margin-top: 12px; }
  .note { font-size: 0.9rem; opacity: 0.8; }
`;

function layout(title, body) {
  return `<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>${escapeHtml(title)}</title>
<style>${STYLE}</style>
</head>
<body><main>${body}</main></body>
</html>`;
}

function connectForm(serverUrl) {
  return `
<h2>接続先</h2>
<form method="get" action="/connect">
  <input type="url" name="url" required value="${escapeHtml(serverUrl)}" aria-label="接続先の URL">
  <button type="submit">保存して接続</button>
</form>
<div class="actions">
  <a class="button" href="/connect">再試行</a>
  <a class="button" href="/connect?url=${encodeURIComponent(DEFAULT_SERVER_URL)}">既定（${escapeHtml(DEFAULT_SERVER_URL)}）に戻す</a>
</div>
<p class="note">接続先はこの PC のユーザーデータに保存され、次回の起動から使われます。</p>`;
}

const HOW_TO_START = `
<h2>Magi の起動方法</h2>
<p>このアプリは、利用者が自分の環境で起動した Magi を開くだけのランチャーです。Magi 本体は含まれていません。
Docker がある環境で、次のコマンドで起動してください。</p>
<pre><code>git clone https://github.com/shizukutanaka/Magi.git
cd Magi
docker compose pull
docker compose up -d</code></pre>
<p>公開イメージを取得できない場合は <code>docker compose up -d --build</code> でソースからビルドできます。
ポートを変える場合は <code>MAGI_PORT=8080 docker compose up -d</code> とし、接続先を <code>http://localhost:8080</code> にしてください。
起動後、<code>docker compose ps</code> で状態を確認できます。</p>`;

function renderOfflinePage({ serverUrl, reason }) {
  return layout('Magi に接続できません', `
<h1>Magi に接続できませんでした</h1>
<p class="reason"><strong>${escapeHtml(serverUrl)}</strong> に接続できませんでした。<br>${escapeHtml(reason)}</p>
${HOW_TO_START}
${connectForm(serverUrl)}`);
}

function renderSettingsPage({ serverUrl }) {
  return layout('接続先の設定', `
<h1>接続先の設定</h1>
<p>現在の接続先: <strong>${escapeHtml(serverUrl)}</strong></p>
${connectForm(serverUrl)}
${HOW_TO_START}`);
}

function renderConnectingPage({ serverUrl }) {
  return layout('Magi に接続しています', `
<h1>Magi に接続しています…</h1>
<p>${escapeHtml(serverUrl)}</p>`);
}

module.exports = { PAGE_CSP, escapeHtml, renderOfflinePage, renderSettingsPage, renderConnectingPage };
