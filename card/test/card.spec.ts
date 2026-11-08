import { expect, test, type Page } from '@playwright/test';

// The card is rendered in a bare page with a fake `hass` object (see
// harness.html): no Home Assistant needed to check what it shows and which
// services it calls.

declare global {
  interface Window {
    mountCard: (config: Record<string, unknown>, hass?: unknown) => HTMLElement;
    makeHass: (overrides?: Record<string, unknown>) => Record<string, any>;
    setState: (entityId: string, state?: string | null, attributes?: Record<string, unknown>) => void;
    serviceCalls: { domain: string; service: string; data: Record<string, unknown> }[];
    wsCalls: Record<string, unknown>[];
    opened?: string;
    harnessReady?: boolean;
    card: any;
  }
}

async function mount(page: Page, config: Record<string, unknown> = { type: 'custom:brother-scanner-card', entity: 'sensor.office_state' }) {
  await page.goto('/test/harness.html');
  await page.waitForFunction(() => window.harnessReady && customElements.get('brother-scanner-card'));
  await page.evaluate((cfg) => window.mountCard(cfg), config);
  const card = page.locator('brother-scanner-card');
  await expect(card.locator('.name')).toBeVisible();
  return card;
}

test('shows name, state, picture, enabled buttons and the last scan', async ({ page }) => {
  const card = await mount(page);
  await expect(card.locator('.name')).toHaveText('Office');
  await expect(card.locator('.state span')).toHaveText('Ready');
  await expect(card.locator('img.image')).toHaveAttribute('src', '/images/mfc.svg');
  await expect(card.locator('button.action')).toHaveText(['Archive', 'Rear pages', 'Scan to OCR']);
  await expect(card.locator('.file-name')).toHaveText('2026-10-10-10-00-00.pdf');
  await expect(card.locator('.file-meta')).toContainText('338 kB');
  await expect(card.locator('.footer a')).toHaveAttribute('href', 'http://scanner.local:8080');
});

test('pressing a button presses the matching HA button entity', async ({ page }) => {
  const card = await mount(page);
  await card.locator('button.action', { hasText: 'Scan to OCR' }).click();
  const calls = await page.evaluate(() => window.serviceCalls);
  expect(calls).toEqual([{ domain: 'button', service: 'press', data: { entity_id: 'button.office_scan_to_ocr' } }]);
  await expect(card.locator('button.action', { hasText: 'Scan to OCR' }).locator('ha-icon')).toHaveAttribute('icon', 'mdi:loading');
});

test('download asks for a signed path and opens it', async ({ page }) => {
  const card = await mount(page);
  await card.locator('button.icon[title="Download"]').click();
  await expect.poll(() => page.evaluate(() => window.opened)).toBe('http://ha.local:8123/api/brother_scanner/abc/download/2026-10-10-10-00-00.pdf?authSig=signed');
  const ws = await page.evaluate(() => window.wsCalls);
  expect(ws[0]).toMatchObject({ type: 'auth/sign_path', path: '/api/brother_scanner/abc/download/2026-10-10-10-00-00.pdf' });
  await card.locator('button.icon[title="Download OCR copy"]').click();
  await expect.poll(() => page.evaluate(() => window.opened)).toContain('-ocr.pdf');
});

test('states: scanning disables buttons, waiting highlights rear pages with a countdown, queue and problems show chips', async ({ page }) => {
  const card = await mount(page);
  await page.evaluate(() => window.setState('sensor.office_state', 'scanning', { pages: 1 }));
  await expect(card.locator('.state span')).toHaveText('Scanning…');
  await expect(card.locator('button.action', { hasText: 'Archive' })).toBeDisabled();
  await expect(card.locator('.chip')).toContainText(['1 page']);

  const until = new Date(Date.now() + 90_000).toISOString();
  await page.evaluate((u) => window.setState('sensor.office_state', 'waiting_for_rear', { waiting_until: u, pages: 2 }), until);
  await expect(card.locator('.state span')).toHaveText('Waiting for rear pages');
  await expect(card.locator('button.action.highlight')).toHaveText('Rear pages');
  await expect(card.locator('button.action', { hasText: 'Archive' })).toBeEnabled();
  await expect(card.locator('.chip.timer')).toContainText(/\d+s/);

  await page.evaluate(() => window.setState('sensor.office_state', 'ocr', { queue: { pending: 2, in_progress: 1, failed: 1 } }));
  await expect(card.locator('.state span')).toHaveText('OCR running');
  await expect(card.locator('.chip').first()).toContainText('OCR queue 3');
  await expect(card.locator('.chip.problem')).toContainText('1 OCR failed');

  await page.evaluate(() => window.setState('sensor.office_state', 'unreachable', { queue: {} }));
  await expect(card.locator('.state span')).toHaveText('Scanner unreachable');

  await page.evaluate(() => window.setState('sensor.office_state', 'unavailable'));
  await expect(card.locator('.state span')).toHaveText('Container unavailable');
  await expect(card.locator('button.action', { hasText: 'Archive' })).toBeDisabled();
});

test('config options: hide picture, subset of buttons, selects, no last scan, no link, custom name', async ({ page }) => {
  const card = await mount(page, {
    type: 'custom:brother-scanner-card',
    entity: 'sensor.office_state',
    name: 'Scanner in the study',
    show_image: false,
    buttons: ['file'],
    show_selects: true,
    show_last_scan: false,
    show_link: false,
  });
  await expect(card.locator('.name')).toHaveText('Scanner in the study');
  await expect(card.locator('img.image')).toHaveCount(0);
  await expect(card.locator('button.action')).toHaveText(['Archive']);
  await expect(card.locator('.last-scan')).toHaveCount(0);
  await expect(card.locator('.footer')).toHaveCount(0);
  await expect(card.locator('.select span')).toHaveText(['resolution']);
  await card.locator('.select select').selectOption('300');
  const calls = await page.evaluate(() => window.serviceCalls);
  expect(calls).toEqual([{ domain: 'select', service: 'select_option', data: { entity_id: 'select.office_resolution', option: '300' } }]);
});

test('missing entity and no scans yet are reported, config without entity is rejected', async ({ page }) => {
  await page.goto('/test/harness.html');
  await page.waitForFunction(() => window.harnessReady && customElements.get('brother-scanner-card'));
  const error = await page.evaluate(() => {
    try {
      window.mountCard({ type: 'custom:brother-scanner-card' });
      return null;
    } catch (err: any) {
      return err.message;
    }
  });
  expect(error).toContain('entity');
  await page.evaluate(() => window.mountCard({ type: 'custom:brother-scanner-card', entity: 'sensor.nope' }));
  await expect(page.locator('brother-scanner-card .warning')).toContainText('sensor.nope');
  await page.evaluate(() => {
    const hass = window.makeHass();
    hass.states['sensor.office_last_scan'].state = 'unknown';
    window.mountCard({ type: 'custom:brother-scanner-card', entity: 'sensor.office_state' }, hass);
  });
  await expect(page.locator('brother-scanner-card .last-scan.empty')).toContainText('No scans yet');
});

test('stub config picks the state sensor and the editor emits config-changed', async ({ page }) => {
  await page.goto('/test/harness.html');
  await page.waitForFunction(() => window.harnessReady && customElements.get('brother-scanner-card'));
  const stub = await page.evaluate(() => (customElements.get('brother-scanner-card') as any).getStubConfig(window.makeHass()));
  expect(stub).toEqual({ entity: 'sensor.office_state' });
  const emitted = await page.evaluate(() => {
    const editor = (customElements.get('brother-scanner-card') as any).getConfigElement();
    editor.setConfig({ type: 'custom:brother-scanner-card', entity: 'sensor.office_state' });
    editor.hass = window.makeHass();
    document.body.appendChild(editor);
    let result: unknown = null;
    editor.addEventListener('config-changed', (ev: CustomEvent) => (result = ev.detail.config));
    editor.dispatchEvent(new CustomEvent('value-changed', { detail: { value: { entity: 'sensor.office_state', name: '', buttons: [], compact: true } } }));
    // the editor listens on its ha-form child; call the handler directly as the form would
    (editor as any).valueChanged(new CustomEvent('value-changed', { detail: { value: { entity: 'sensor.office_state', name: '', buttons: [], compact: true } } }));
    return result;
  });
  expect(emitted).toEqual({ entity: 'sensor.office_state', compact: true });
});

test('the OCR copy is a second download button only while it is a second file', async ({ page }) => {
  const card = await mount(page);
  await expect(card.locator('.last-scan button.icon')).toHaveCount(2);

  // the original was removed after OCR: the newest file is the OCR copy itself
  await page.evaluate(() => window.setState('sensor.office_last_scan', '2026-10-10-10-00-00-ocr.pdf', {
    size: 12345, download_url: '/api/brother_scanner/abc/download/2026-10-10-10-00-00-ocr.pdf', ocr_download_url: null, is_ocr_copy: true,
  }));
  await expect(card.locator('.last-scan button.icon')).toHaveCount(1);
  await expect(card.locator('.last-scan button.icon')).toHaveAttribute('title', 'Download (OCR copy)');

  // an older integration that still reports the same file twice
  await page.evaluate(() => window.setState('sensor.office_last_scan', '2026-10-10-10-00-00-ocr.pdf', {
    size: 12345, download_url: '/api/brother_scanner/abc/download/2026-10-10-10-00-00-ocr.pdf', ocr_download_url: '/api/brother_scanner/abc/download/2026-10-10-10-00-00-ocr.pdf',
  }));
  await expect(card.locator('.last-scan button.icon')).toHaveCount(1);
});

test("the scanner's own state: registration and display chips by default, serial/firmware on request, warnings, and all of it switchable", async ({ page }) => {
  const card = await mount(page);
  await expect(card.locator('.device .chip')).toHaveCount(2);
  await expect(card.locator('.device .chip.ok')).toContainText('Scan-to-PC registered');
  await expect(card.locator('.device .chip.display')).toContainText('Scan:   drück');

  const full = await mount(page, { type: 'custom:brother-scanner-card', entity: 'sensor.office_state', show_serial: true, show_firmware: true });
  await expect(full.locator('.device .chip')).toContainText(['registered', 'Scan:', 'S/N E73941F6N621420', 'FW Y2309112149']);

  // the device dropped the registration and has its scan key switched off
  await page.evaluate(() => window.setState('sensor.office_state', null, { registered: false, scan_key_enabled: false }));
  await expect(full.locator('.device .chip.problem')).toContainText(['not registered on the scanner', 'scan key disabled on the device']);
  await expect(full.locator('.device .chip.ok')).toHaveCount(0);

  const some = await mount(page, { type: 'custom:brother-scanner-card', entity: 'sensor.office_state', show_registered: false, show_display: false, show_scan_key: false });
  await expect(some.locator('.device')).toHaveCount(0);
  const none = await mount(page, { type: 'custom:brother-scanner-card', entity: 'sensor.office_state', show_device: false, show_serial: true });
  await expect(none.locator('.device')).toHaveCount(0);

  // an older integration or container: no device state in the attributes, no row
  await page.evaluate(() => {
    const hass = window.makeHass();
    for (const key of ['registered', 'serial', 'firmware', 'display', 'scan_key_enabled']) delete hass.states['sensor.office_state'].attributes[key];
    window.mountCard({ type: 'custom:brother-scanner-card', entity: 'sensor.office_state' }, hass);
  });
  await expect(page.locator('brother-scanner-card .device')).toHaveCount(0);
  await expect(page.locator('brother-scanner-card .name')).toHaveText('Office');
});
