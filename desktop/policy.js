'use strict';

const DEFAULT_SERVER_URL = 'http://localhost:8000';
const LAUNCHER_SCHEME = 'magi-launcher';
const LAUNCHER_ORIGIN = `${LAUNCHER_SCHEME}://launcher`;
const HEALTH_TIMEOUT_MS = 3000;

function parseUrl(value) {
  try {
    return new URL(value);
  } catch {
    return null;
  }
}

// 接続先は http(s) のオリジンだけを受け付ける（パス・クエリ・資格情報は持たせない）。
function normalizeServerUrl(input) {
  const text = typeof input === 'string' ? input.trim() : '';
  if (!text) return { ok: false, error: '接続先が空です。' };
  const url = parseUrl(text);
  if (!url || (url.protocol !== 'http:' && url.protocol !== 'https:')) {
    return { ok: false, error: '接続先は http:// または https:// で始まる URL を指定してください。' };
  }
  if (url.username || url.password) {
    return { ok: false, error: '接続先の URL にユーザー名やパスワードを含めないでください。' };
  }
  return { ok: true, origin: url.origin };
}

// allow: そのまま遷移 / external: 既定ブラウザで開く / block: 何もしない
function classifyNavigation(target, serverOrigin) {
  const url = parseUrl(target);
  if (!url) return 'block';
  if (url.protocol === `${LAUNCHER_SCHEME}:` && url.host === 'launcher') return 'allow';
  if (url.protocol === 'http:' || url.protocol === 'https:') {
    return url.origin === serverOrigin ? 'allow' : 'external';
  }
  return 'block';
}

function classifyNewWindow(target) {
  const url = parseUrl(target);
  return url && (url.protocol === 'http:' || url.protocol === 'https:') ? 'external' : 'block';
}

function describeHealthError(error) {
  if (error && error.name === 'TimeoutError') {
    return `${HEALTH_TIMEOUT_MS / 1000} 秒以内に応答がありませんでした。`;
  }
  const code = error && error.cause && error.cause.code;
  switch (code) {
    case 'ECONNREFUSED':
      return '接続を拒否されました。Magi が起動していないか、ポート番号が違う可能性があります。';
    case 'ENOTFOUND':
    case 'EAI_AGAIN':
      return 'ホスト名を解決できませんでした。接続先の綴りを確認してください。';
    case 'ECONNRESET':
      return '接続が途中で切断されました。';
    case 'EHOSTUNREACH':
    case 'ENETUNREACH':
      return 'ホストに到達できませんでした。';
    default:
      if (code && (code.startsWith('ERR_TLS') || code.includes('CERT'))) {
        return `TLS 証明書を検証できませんでした（${code}）。`;
      }
      return `接続に失敗しました（${code || (error && error.message) || '不明なエラー'}）。`;
  }
}

// /health が {"status":"ok"} を返すことを確かめる。失敗時は理由を日本語で返す。
async function checkHealth(origin, fetchImpl = fetch) {
  let response;
  try {
    response = await fetchImpl(`${origin}/health`, {
      cache: 'no-store',
      redirect: 'error',
      signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS),
    });
  } catch (error) {
    return { ok: false, reason: describeHealthError(error) };
  }
  if (!response.ok) {
    return { ok: false, reason: `/health が HTTP ${response.status} を返しました。` };
  }
  let body;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (!body || body.status !== 'ok') {
    return { ok: false, reason: '/health の応答が Magi のものではありません。接続先が別のサービスを指している可能性があります。' };
  }
  return { ok: true };
}

module.exports = {
  DEFAULT_SERVER_URL,
  LAUNCHER_SCHEME,
  LAUNCHER_ORIGIN,
  HEALTH_TIMEOUT_MS,
  normalizeServerUrl,
  classifyNavigation,
  classifyNewWindow,
  describeHealthError,
  checkHealth,
};
