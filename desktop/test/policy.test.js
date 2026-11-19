'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const policy = require('../policy');
const pages = require('../launcher-page');

test('normalizeServerUrl はオリジンだけを残す', () => {
  assert.deepEqual(policy.normalizeServerUrl(' http://localhost:8000/path?q=1#x '), { ok: true, origin: 'http://localhost:8000' });
  assert.deepEqual(policy.normalizeServerUrl('https://magi.example.com'), { ok: true, origin: 'https://magi.example.com' });
});

test('normalizeServerUrl は http(s) 以外・資格情報付き・空を拒否する', () => {
  for (const bad of ['', '   ', 'localhost:8000', 'file:///etc/passwd', 'javascript:alert(1)', 'ftp://host', 'http://user:pw@host', null, 42]) {
    const result = policy.normalizeServerUrl(bad);
    assert.equal(result.ok, false, String(bad));
    assert.ok(result.error);
  }
});

test('classifyNavigation は接続先とランチャー画面だけを許可する', () => {
  const origin = 'http://localhost:8000';
  assert.equal(policy.classifyNavigation('http://localhost:8000/#engine=tarot', origin), 'allow');
  assert.equal(policy.classifyNavigation('magi-launcher://launcher/connect?url=x', origin), 'allow');
  assert.equal(policy.classifyNavigation('http://localhost:8001/', origin), 'external');
  assert.equal(policy.classifyNavigation('https://localhost:8000/', origin), 'external');
  assert.equal(policy.classifyNavigation('https://github.com/shizukutanaka/Magi', origin), 'external');
  assert.equal(policy.classifyNavigation('magi-launcher://other/', origin), 'block');
  assert.equal(policy.classifyNavigation('file:///etc/passwd', origin), 'block');
  assert.equal(policy.classifyNavigation('javascript:alert(1)', origin), 'block');
  assert.equal(policy.classifyNavigation('not a url', origin), 'block');
});

test('classifyNewWindow は http(s) だけを既定ブラウザへ回す', () => {
  assert.equal(policy.classifyNewWindow('https://example.com/'), 'external');
  assert.equal(policy.classifyNewWindow('http://localhost:8000/'), 'external');
  assert.equal(policy.classifyNewWindow('file:///tmp/x'), 'block');
  assert.equal(policy.classifyNewWindow('blob:http://localhost:8000/abc'), 'block');
});

const jsonResponse = (status, body) => ({ ok: status >= 200 && status < 300, status, json: async () => body });

test('checkHealth は {"status":"ok"} のときだけ成功する', async () => {
  let requested;
  const ok = await policy.checkHealth('http://localhost:8000', async (url, init) => {
    requested = { url, init };
    return jsonResponse(200, { status: 'ok' });
  });
  assert.deepEqual(ok, { ok: true });
  assert.equal(requested.url, 'http://localhost:8000/health');
  assert.equal(requested.init.redirect, 'error');
  assert.ok(requested.init.signal);

  const status = await policy.checkHealth('http://x', async () => jsonResponse(503, null));
  assert.match(status.reason, /HTTP 503/);
  const other = await policy.checkHealth('http://x', async () => jsonResponse(200, { hello: 'world' }));
  assert.match(other.reason, /Magi のものではありません/);
  const notJson = await policy.checkHealth('http://x', async () => ({ ok: true, status: 200, json: async () => { throw new SyntaxError('x'); } }));
  assert.equal(notJson.ok, false);
});

test('checkHealth は接続エラーの理由を説明する', async () => {
  const refused = Object.assign(new TypeError('fetch failed'), { cause: { code: 'ECONNREFUSED' } });
  const r1 = await policy.checkHealth('http://x', async () => { throw refused; });
  assert.match(r1.reason, /拒否/);
  const timeout = Object.assign(new Error('timeout'), { name: 'TimeoutError' });
  const r2 = await policy.checkHealth('http://x', async () => { throw timeout; });
  assert.match(r2.reason, /応答がありませんでした/);
  const dns = Object.assign(new TypeError('fetch failed'), { cause: { code: 'ENOTFOUND' } });
  assert.match((await policy.checkHealth('http://x', async () => { throw dns; })).reason, /ホスト名/);
  const tls = Object.assign(new TypeError('fetch failed'), { cause: { code: 'DEPTH_ZERO_SELF_SIGNED_CERT' } });
  assert.match((await policy.checkHealth('http://x', async () => { throw tls; })).reason, /TLS/);
});

test('接続できない画面は理由と compose の起動手順を示し、値をエスケープする', () => {
  const html = pages.renderOfflinePage({ serverUrl: 'http://localhost:8000', reason: '<script>alert(1)</script>' });
  assert.ok(!html.includes('<script>alert(1)</script>'));
  assert.ok(html.includes('&lt;script&gt;'));
  assert.ok(html.includes('docker compose up -d'));
  assert.ok(html.includes('action="/connect"'));
  assert.ok(!/<script/i.test(html));
  assert.ok(!html.includes('は保存されました'));
  const saved = pages.renderOfflinePage({ serverUrl: 'http://localhost:8080', reason: 'x', saved: true });
  assert.ok(saved.includes('は保存されました'));
});

test('ランチャー画面の CSP はスクリプトを許可しない', () => {
  assert.match(pages.PAGE_CSP, /default-src 'none'/);
  assert.doesNotMatch(pages.PAGE_CSP, /script-src/);
  assert.match(pages.PAGE_CSP, /form-action 'self'/);
});
