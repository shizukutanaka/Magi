'use strict';

// Magi デスクトップ版: 利用者が自分で起動した Magi を開くだけのランチャー。
const fs = require('node:fs');
const path = require('node:path');
const { app, BrowserWindow, Menu, protocol, session, shell } = require('electron');
const policy = require('./policy');
const pages = require('./launcher-page');

const CONFIG_FILE = 'launcher.json';
let mainWindow = null;
let serverOrigin = policy.DEFAULT_SERVER_URL;
let lastReason = '';

protocol.registerSchemesAsPrivileged([
  { scheme: policy.LAUNCHER_SCHEME, privileges: { standard: true, secure: true } },
]);
app.enableSandbox();

function configPath() {
  return path.join(app.getPath('userData'), CONFIG_FILE);
}

function loadServerOrigin() {
  try {
    const saved = JSON.parse(fs.readFileSync(configPath(), 'utf8'));
    const result = policy.normalizeServerUrl(saved.serverUrl);
    if (result.ok) return result.origin;
  } catch {
    // 未保存または壊れた設定は既定値で起動する
  }
  return policy.DEFAULT_SERVER_URL;
}

function saveServerOrigin(origin) {
  fs.mkdirSync(path.dirname(configPath()), { recursive: true });
  const tmp = `${configPath()}.tmp`;
  fs.writeFileSync(tmp, `${JSON.stringify({ serverUrl: origin }, null, 2)}\n`);
  fs.renameSync(tmp, configPath());
}

function htmlResponse(html, status = 200) {
  return new Response(html, {
    status,
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Content-Security-Policy': pages.PAGE_CSP,
      'X-Content-Type-Options': 'nosniff',
      'Cache-Control': 'no-store',
    },
  });
}

function showLauncherPage(pathname) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.loadURL(`${policy.LAUNCHER_ORIGIN}${pathname}`);
  }
}

async function handleLauncherRequest(request) {
  const url = new URL(request.url);
  switch (url.pathname) {
    case '/connect': {
      if (url.searchParams.has('url')) {
        const result = policy.normalizeServerUrl(url.searchParams.get('url'));
        if (!result.ok) {
          return htmlResponse(pages.renderOfflinePage({ serverUrl: serverOrigin, reason: result.error }));
        }
        serverOrigin = result.origin;
        try {
          saveServerOrigin(serverOrigin);
        } catch (error) {
          return htmlResponse(pages.renderOfflinePage({
            serverUrl: serverOrigin,
            reason: `接続先を保存できませんでした（${error.message}）。`,
          }));
        }
      }
      const health = await policy.checkHealth(serverOrigin);
      if (!health.ok) {
        lastReason = health.reason;
        return htmlResponse(pages.renderOfflinePage({ serverUrl: serverOrigin, reason: health.reason }));
      }
      const target = `${serverOrigin}/`;
      setImmediate(() => mainWindow && !mainWindow.isDestroyed() && mainWindow.loadURL(target));
      return htmlResponse(pages.renderConnectingPage({ serverUrl: serverOrigin }));
    }
    case '/offline':
      return htmlResponse(pages.renderOfflinePage({ serverUrl: serverOrigin, reason: lastReason || '理由は不明です。' }));
    case '/settings':
      return htmlResponse(pages.renderSettingsPage({ serverUrl: serverOrigin }));
    default:
      return htmlResponse(pages.renderSettingsPage({ serverUrl: serverOrigin }), 404);
  }
}

function originOf(value) {
  try {
    return new URL(value).origin;
  } catch {
    return null;
  }
}

function isServerClipboardWrite(permission, requestingUrl) {
  return permission === 'clipboard-sanitized-write' && originOf(requestingUrl) === serverOrigin;
}

function hardenSession(ses) {
  ses.setPermissionRequestHandler((_wc, permission, callback, details) => {
    callback(isServerClipboardWrite(permission, details.requestingUrl));
  });
  ses.setPermissionCheckHandler((_wc, permission, requestingOrigin) =>
    isServerClipboardWrite(permission, requestingOrigin));
}

function hardenWebContents(contents) {
  contents.on('will-attach-webview', (event) => event.preventDefault());
  contents.setWindowOpenHandler(({ url }) => {
    if (policy.classifyNewWindow(url) === 'external') shell.openExternal(url);
    return { action: 'deny' };
  });
  contents.on('will-navigate', (event) => {
    const decision = policy.classifyNavigation(event.url, serverOrigin);
    if (decision === 'allow') return;
    event.preventDefault();
    if (decision === 'external') shell.openExternal(event.url);
  });
  contents.on('will-frame-navigate', (event) => {
    if (event.isMainFrame) return;
    if (policy.classifyNavigation(event.url, serverOrigin) !== 'allow') event.preventDefault();
  });
  contents.on('will-redirect', (event) => {
    if (policy.classifyNavigation(event.url, serverOrigin) === 'allow') return;
    event.preventDefault();
    if (event.isMainFrame) {
      lastReason = `接続先以外（${event.url}）へのリダイレクトを遮断しました。`;
      showLauncherPage('/offline');
    }
  });
  contents.on('did-fail-load', (_event, errorCode, errorDescription, validatedURL, isMainFrame) => {
    // -3 (ERR_ABORTED) は遷移の取り消しで、失敗ではない
    if (!isMainFrame || errorCode === -3 || originOf(validatedURL) !== serverOrigin) return;
    lastReason = `ページを読み込めませんでした（${errorDescription}）。Magi が停止した可能性があります。`;
    showLauncherPage('/offline');
  });
}

function buildMenu() {
  const isMac = process.platform === 'darwin';
  const template = [
    ...(isMac ? [{ role: 'appMenu' }] : []),
    {
      label: '接続',
      submenu: [
        { label: '接続先を変更…', accelerator: 'CmdOrCtrl+,', click: () => showLauncherPage('/settings') },
        { label: '再接続', accelerator: 'CmdOrCtrl+Shift+R', click: () => showLauncherPage('/connect') },
        ...(isMac ? [] : [{ type: 'separator' }, { role: 'quit', label: '終了' }]),
      ],
    },
    { role: 'editMenu' },
    {
      label: '表示',
      submenu: [
        { role: 'reload', label: '再読み込み' },
        { type: 'separator' },
        { role: 'resetZoom', label: '実際のサイズ' },
        { role: 'zoomIn', label: '拡大' },
        { role: 'zoomOut', label: '縮小' },
        { type: 'separator' },
        { role: 'togglefullscreen', label: 'フルスクリーン' },
      ],
    },
    { role: 'windowMenu' },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 820,
    title: 'Magi',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
      spellcheck: false,
    },
  });
  mainWindow.on('closed', () => { mainWindow = null; });
  mainWindow.loadURL(`${policy.LAUNCHER_ORIGIN}/connect`);
}

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (!mainWindow) return;
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
  });
  app.on('web-contents-created', (_event, contents) => hardenWebContents(contents));
  app.whenReady().then(() => {
    serverOrigin = loadServerOrigin();
    hardenSession(session.defaultSession);
    protocol.handle(policy.LAUNCHER_SCHEME, handleLauncherRequest);
    buildMenu();
    createWindow();
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  });
  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
  });
}
