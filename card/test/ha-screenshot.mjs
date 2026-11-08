// Installs the built card into a running Home Assistant (as left by
// ha-brother-scanner/tests/e2e_real_ha.py --keep), creates a dashboard with
// the card and takes a screenshot. Usage:
//   node test/ha-screenshot.mjs http://localhost:18123 e2e e2e-password <ha config dir> <out.png>
import { copyFileSync, mkdirSync } from 'node:fs';
import { chromium } from '@playwright/test';

const [base, username, password, configDir, out] = process.argv.slice(2);

async function login() {
  const flow = await (await fetch(`${base}/auth/login_flow`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ client_id: base, handler: ['homeassistant', null], redirect_uri: `${base}/` }),
  })).json();
  const step = await (await fetch(`${base}/auth/login_flow/${flow.flow_id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ client_id: base, username, password }),
  })).json();
  if (!step.result) throw new Error(`login failed: ${JSON.stringify(step)}`);
  const token = await (await fetch(`${base}/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `grant_type=authorization_code&code=${step.result}&client_id=${encodeURIComponent(base)}`,
  })).json();
  return token;
}

function ws(url, token) {
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(url);
    let id = 1;
    const pending = new Map();
    socket.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.type === 'auth_required') socket.send(JSON.stringify({ type: 'auth', access_token: token }));
      else if (msg.type === 'auth_ok') resolve({
        call: (payload) => new Promise((res, rej) => {
          const myId = id++;
          pending.set(myId, { res, rej });
          socket.send(JSON.stringify({ id: myId, ...payload }));
        }),
        close: () => socket.close(),
      });
      else if (msg.type === 'auth_invalid') reject(new Error('ws auth invalid'));
      else if (msg.type === 'result' && pending.has(msg.id)) {
        const p = pending.get(msg.id);
        pending.delete(msg.id);
        msg.success ? p.res(msg.result) : p.rej(new Error(JSON.stringify(msg.error)));
      }
    };
    socket.onerror = (err) => reject(err);
  });
}

const token = await login();
mkdirSync(`${configDir}/www`, { recursive: true });
copyFileSync('dist/brother-scanner-card.js', `${configDir}/www/brother-scanner-card.js`);
const api = await ws(base.replace('http', 'ws') + '/api/websocket', token.access_token);
const resources = await api.call({ type: 'lovelace/resources' });
if (!resources.some((r) => r.url.includes('brother-scanner-card.js'))) {
  await api.call({ type: 'lovelace/resources/create', res_type: 'module', url: '/local/brother-scanner-card.js?v=1' });
}
const states = await api.call({ type: 'get_states' });
const stateEntity = states.find((s) => s.entity_id.startsWith('sensor.') && s.attributes.actions && s.attributes.web_ui_url);
if (!stateEntity) throw new Error('no scanner state sensor found');
const dashboards = await api.call({ type: 'lovelace/dashboards/list' });
if (!dashboards.some((d) => d.url_path === 'scanner-card')) {
  await api.call({ type: 'lovelace/dashboards/create', url_path: 'scanner-card', title: 'Scanner card', mode: 'storage', show_in_sidebar: true, require_admin: false, icon: 'mdi:scanner' });
}
await api.call({
  type: 'lovelace/config/save',
  url_path: 'scanner-card',
  config: {
    title: 'Home',
    views: [{ title: 'Scanner', path: 'scanner', cards: [{ type: 'custom:brother-scanner-card', entity: stateEntity.entity_id }] }],
  },
});
api.close();

const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 520, height: 640 }, deviceScaleFactor: 2 });
await context.addInitScript((tokens) => {
  // the frontend reads its tokens from localStorage; this skips the login form
  localStorage.setItem('hassTokens', JSON.stringify({ ...tokens, hassUrl: location.origin, clientId: location.origin }));
}, { access_token: token.access_token, refresh_token: token.refresh_token, token_type: 'Bearer', expires_in: token.expires_in, expires: Date.now() + token.expires_in * 1000 });
const page = await context.newPage();
await page.goto(`${base}/scanner-card/scanner`, { waitUntil: 'networkidle' });
const card = page.locator('brother-scanner-card');
try {
  await card.waitFor({ timeout: 60_000 });
} catch (err) {
  await page.screenshot({ path: out.replace('.png', '-debug.png'), fullPage: true });
  console.error('card not found; url', page.url(), 'title', await page.title());
  console.error(await page.evaluate(() => document.body.innerText.slice(0, 500)));
  throw err;
}
await page.waitForTimeout(2000);
await card.screenshot({ path: out });
console.log(`card screenshot written to ${out}`);
await browser.close();
