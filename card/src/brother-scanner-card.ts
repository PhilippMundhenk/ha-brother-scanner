import { LitElement, css, html, nothing } from 'lit';
import { property, state } from 'lit/decorators.js';
import { discoverEntities } from './entities';
import './brother-scanner-card-editor';
import type { CardConfig, HassEntityState, HomeAssistant, ScannerAction, ScannerEntities } from './types';

const CARD_VERSION = '1.1.1';

const STATE_ICONS: Record<string, string> = {
  idle: 'mdi:emoticon-happy-outline',
  scanning: 'mdi:scanner',
  waiting_for_rear: 'mdi:timer-sand',
  converting: 'mdi:cog-outline',
  ocr: 'mdi:brain',
  unreachable: 'mdi:lan-disconnect',
  unavailable: 'mdi:cloud-off-outline',
  unknown: 'mdi:help-circle-outline',
};

const STATE_LABELS: Record<string, string> = {
  idle: 'Ready',
  scanning: 'Scanning…',
  waiting_for_rear: 'Waiting for rear pages',
  converting: 'Converting…',
  ocr: 'OCR running',
  unreachable: 'Scanner unreachable',
  unavailable: 'Container unavailable',
  unknown: 'Unknown',
};

const ACTION_ICONS: Record<string, string> = {
  file: 'mdi:file-document-outline',
  ocr: 'mdi:text-recognition',
  email: 'mdi:book-open-page-variant',
  image: 'mdi:image-outline',
};

export class BrotherScannerCard extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @state() private config!: CardConfig;
  @state() private busy: string | null = null;
  @state() private error: string | null = null;
  @state() private now = Date.now();
  private ticker?: number;

  public static getConfigElement(): HTMLElement {
    return document.createElement('brother-scanner-card-editor');
  }

  public static getStubConfig(hass: HomeAssistant): Partial<CardConfig> {
    const entity = Object.values(hass.entities || {}).find((e) => e.translation_key === 'scanner_state' && e.platform === 'brother_scanner');
    return { entity: entity?.entity_id || '' };
  }

  public setConfig(config: CardConfig): void {
    if (!config || !config.entity) {
      throw new Error('Pick the scanner state sensor (entity)');
    }
    this.config = {
      show_image: true,
      show_buttons: true,
      show_selects: false,
      show_last_scan: true,
      show_link: true,
      compact: false,
      show_device: true,
      show_registered: true,
      show_display: true,
      show_serial: false,
      show_firmware: false,
      show_scan_key: true,
      ...config,
    };
  }

  public getCardSize(): number {
    return this.config?.compact ? 3 : 5;
  }

  public connectedCallback(): void {
    super.connectedCallback();
    this.ticker = window.setInterval(() => (this.now = Date.now()), 1000);
  }

  public disconnectedCallback(): void {
    super.disconnectedCallback();
    if (this.ticker) window.clearInterval(this.ticker);
  }

  private get stateObj(): HassEntityState | undefined {
    return this.hass?.states[this.config.entity];
  }

  private get entities(): ScannerEntities {
    return discoverEntities(this.hass, this.config.entity);
  }

  protected render() {
    if (!this.hass || !this.config) return nothing;
    const stateObj = this.stateObj;
    if (!stateObj) {
      return html`<ha-card><div class="warning">Entity ${this.config.entity} not found</div></ha-card>`;
    }
    const attrs = stateObj.attributes;
    const scannerState = stateObj.state;
    const entities = this.entities;
    const name = this.config.name || attrs.friendly_name?.replace(/ State$/, '') || 'Scanner';
    const image = this.config.image || attrs.image_url;
    const showImage = this.config.show_image !== false && !!image;
    const queue = attrs.queue || {};

    return html`
      <ha-card class=${this.config.compact ? 'compact' : ''}>
        <div class="header">
          ${showImage ? html`<img class="image" src=${image} alt="" />` : nothing}
          <div class="title">
            <div class="name">${name}</div>
            <div class="state ${scannerState}">
              <ha-icon icon=${STATE_ICONS[scannerState] || STATE_ICONS.unknown}></ha-icon>
              <span>${this.stateLabel(stateObj)}</span>
            </div>
            ${this.renderDetail(scannerState, attrs, queue)}
          </div>
        </div>
        ${this.config.show_device !== false ? this.renderDevice(attrs) : nothing}
        ${this.config.show_buttons !== false ? this.renderButtons(scannerState, attrs, entities) : nothing}
        ${this.config.show_selects ? this.renderSelects(entities) : nothing}
        ${this.config.show_last_scan !== false ? this.renderLastScan(entities) : nothing}
        ${this.error ? html`<div class="error">${this.error}</div>` : nothing}
        ${this.config.show_link !== false && attrs.web_ui_url
          ? html`<div class="footer"><a href=${attrs.web_ui_url} target="_blank" rel="noopener"><ha-icon icon="mdi:open-in-new"></ha-icon> Web UI</a></div>`
          : nothing}
      </ha-card>
    `;
  }

  private stateLabel(stateObj: HassEntityState): string {
    if (this.hass.formatEntityState && !['unavailable', 'unknown'].includes(stateObj.state)) {
      const formatted = this.hass.formatEntityState(stateObj);
      if (formatted && formatted !== stateObj.state) return formatted;
    }
    return STATE_LABELS[stateObj.state] || stateObj.state;
  }

  private renderDetail(scannerState: string, attrs: Record<string, any>, queue: Record<string, any>) {
    const parts: unknown[] = [];
    if (scannerState === 'waiting_for_rear' && attrs.waiting_until) {
      const remaining = Math.max(0, Math.round((new Date(attrs.waiting_until).getTime() - this.now) / 1000));
      parts.push(html`<span class="chip timer"><ha-icon icon="mdi:timer-outline"></ha-icon> ${remaining}s</span>`);
    }
    if (scannerState === 'scanning' && attrs.pages) {
      parts.push(html`<span class="chip">${attrs.pages} page${attrs.pages === 1 ? '' : 's'}</span>`);
    }
    if (queue.pending > 0 || queue.in_progress > 0) {
      parts.push(html`<span class="chip"><ha-icon icon="mdi:tray-full"></ha-icon> OCR queue ${queue.pending + (queue.in_progress || 0)}</span>`);
    }
    if (queue.failed > 0) {
      parts.push(html`<span class="chip problem"><ha-icon icon="mdi:alert-circle-outline"></ha-icon> ${queue.failed} OCR failed</span>`);
    }
    if (attrs.reachable === false && scannerState !== 'unreachable') {
      parts.push(html`<span class="chip problem"><ha-icon icon="mdi:lan-disconnect"></ha-icon> device offline</span>`);
    }
    return parts.length ? html`<div class="detail">${parts}</div>` : nothing;
  }

  /**
   * What the scanner itself reports (container 2.2+, attributes of the state
   * sensor): whether it lists the container as a Scan-to-PC destination, the
   * panel display line, serial, firmware, and a warning when the device has
   * its scan key switched off. Nothing with an older integration or container.
   */
  private renderDevice(attrs: Record<string, any>) {
    const parts: unknown[] = [];
    if (this.config.show_registered !== false) {
      if (attrs.registered === true) {
        parts.push(html`<span class="chip ok" title="The scanner lists this container as a Scan-to-PC destination"><ha-icon icon="mdi:cloud-check-outline"></ha-icon> Scan-to-PC registered</span>`);
      } else if (attrs.registered === false) {
        parts.push(html`<span class="chip problem" title="The scanner does not list this container; its buttons will not reach it"><ha-icon icon="mdi:cloud-off-outline"></ha-icon> not registered on the scanner</span>`);
      }
    }
    if (this.config.show_display !== false && attrs.display) {
      parts.push(html`<span class="chip display" title="Panel display"><ha-icon icon="mdi:monitor-small"></ha-icon> ${attrs.display}</span>`);
    }
    if (this.config.show_serial && attrs.serial) {
      parts.push(html`<span class="chip" title="Serial number">S/N ${attrs.serial}</span>`);
    }
    if (this.config.show_firmware && attrs.firmware) {
      parts.push(html`<span class="chip" title="Firmware">FW ${attrs.firmware}</span>`);
    }
    if (this.config.show_scan_key !== false && attrs.scan_key_enabled === false) {
      parts.push(html`<span class="chip problem" title="The device has its network Scan-to-PC key switched off"><ha-icon icon="mdi:gesture-tap-button"></ha-icon> scan key disabled on the device</span>`);
    }
    return parts.length ? html`<div class="device">${parts}</div>` : nothing;
  }

  private renderButtons(scannerState: string, attrs: Record<string, any>, entities: ScannerEntities) {
    const actions = ((attrs.actions || []) as ScannerAction[]).filter((a) => a.enabled);
    const wanted = this.config.buttons;
    const visible = actions.filter((a) => entities.buttons[a.target] && (!wanted || wanted.includes(a.target)));
    const waiting = scannerState === 'waiting_for_rear';
    const disabled = ['unavailable', 'unknown'].includes(scannerState) || scannerState === 'scanning' || scannerState === 'converting';
    return html`
      <div class="buttons">
        ${visible.map((action) => {
          const entityId = entities.buttons[action.target];
          const entityState = this.hass.states[entityId]?.state;
          const isRear = action.target === 'email';
          return html`
            <button
              class="action ${isRear && waiting ? 'highlight' : ''}"
              ?disabled=${disabled || entityState === 'unavailable' || this.busy !== null}
              @click=${() => this.press(entityId, action.target)}
              title=${action.label}
            >
              <ha-icon icon=${this.busy === action.target ? 'mdi:loading' : ACTION_ICONS[action.target] || 'mdi:scanner'} class=${this.busy === action.target ? 'spin' : ''}></ha-icon>
              <span>${action.label}</span>
            </button>
          `;
        })}
        ${waiting && entities.rear && !visible.some((a) => a.target === 'email')
          ? html`<button class="action highlight" ?disabled=${this.busy !== null} @click=${() => this.press(entities.rear!, 'rear')}>
              <ha-icon icon="mdi:book-open-page-variant"></ha-icon><span>Scan rear pages</span>
            </button>`
          : nothing}
      </div>
    `;
  }

  private renderSelects(entities: ScannerEntities) {
    const selects = Object.entries(entities.selects);
    if (!selects.length) return nothing;
    return html`
      <div class="selects">
        ${selects.map(([parameter, entityId]) => {
          const stateObj = this.hass.states[entityId];
          if (!stateObj) return nothing;
          const options = (stateObj.attributes.options || []) as string[];
          return html`<label class="select">
            <span>${parameter}</span>
            <select @change=${(ev: Event) => this.select(entityId, (ev.target as HTMLSelectElement).value)}>
              ${options.map((o) => html`<option value=${o} ?selected=${o === stateObj.state}>${o === 'default' ? 'Container default' : o}</option>`)}
            </select>
          </label>`;
        })}
      </div>
    `;
  }

  private renderLastScan(entities: ScannerEntities) {
    if (!entities.lastScan) return nothing;
    const last = this.hass.states[entities.lastScan];
    if (!last || ['unavailable', 'unknown', ''].includes(last.state)) {
      return html`<div class="last-scan empty"><ha-icon icon="mdi:file-outline"></ha-icon><span>No scans yet</span></div>`;
    }
    const attrs = last.attributes;
    return html`
      <div class="last-scan">
        <ha-icon icon="mdi:file-pdf-box"></ha-icon>
        <div class="file">
          <div class="file-name" title=${last.state}>${last.state}</div>
          <div class="file-meta">${this.formatSize(attrs.size)}${attrs.modified ? ` · ${this.formatTime(attrs.modified)}` : ''}</div>
        </div>
        ${attrs.download_url
          ? html`<button class="icon" title=${attrs.is_ocr_copy ? 'Download (OCR copy)' : 'Download'} @click=${() => this.download(attrs.download_url)}>
              <ha-icon icon=${attrs.is_ocr_copy ? 'mdi:text-recognition' : 'mdi:download'}></ha-icon></button>`
          : nothing}
        ${attrs.ocr_download_url && attrs.ocr_download_url !== attrs.download_url
          ? html`<button class="icon" title="Download OCR copy" @click=${() => this.download(attrs.ocr_download_url)}><ha-icon icon="mdi:text-recognition"></ha-icon></button>`
          : nothing}
      </div>
    `;
  }

  private async press(entityId: string, target: string): Promise<void> {
    this.busy = target;
    this.error = null;
    try {
      await this.hass.callService('button', 'press', { entity_id: entityId });
    } catch (err: any) {
      this.error = err?.message || String(err);
    } finally {
      window.setTimeout(() => (this.busy = null), 1500);
    }
  }

  private async select(entityId: string, option: string): Promise<void> {
    this.error = null;
    try {
      await this.hass.callService('select', 'select_option', { entity_id: entityId, option });
    } catch (err: any) {
      this.error = err?.message || String(err);
    }
  }

  /** Downloads through Home Assistant: the proxy view needs auth, so ask for a signed path first. */
  private async download(path: string): Promise<void> {
    this.error = null;
    try {
      const signed = await this.hass.callWS<{ path: string }>({ type: 'auth/sign_path', path, expires: 60 });
      const url = this.hass.hassUrl ? this.hass.hassUrl(signed.path) : signed.path;
      window.open(url, '_blank', 'noopener');
    } catch (err: any) {
      this.error = `Download failed: ${err?.message || err}`;
    }
  }

  private formatSize(bytes?: number): string {
    if (!bytes && bytes !== 0) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} kB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  }

  private formatTime(iso: string): string {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return '';
    const language = this.hass.locale?.language || this.hass.language || undefined;
    return date.toLocaleString(language, { dateStyle: 'medium', timeStyle: 'short' });
  }

  static styles = css`
    ha-card {
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .header {
      display: flex;
      gap: 16px;
      align-items: center;
    }
    .image {
      width: 112px;
      height: 84px;
      object-fit: contain;
      flex-shrink: 0;
      border-radius: 8px;
      background: #fff; /* the device drawings are made for a white background */
    }
    .compact .image {
      width: 72px;
      height: 54px;
    }
    .title {
      min-width: 0;
      flex: 1;
    }
    .name {
      font-size: 1.25rem;
      font-weight: 500;
      color: var(--primary-text-color);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .state {
      display: flex;
      align-items: center;
      gap: 6px;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }
    .state ha-icon {
      --mdc-icon-size: 22px;
    }
    .state.idle ha-icon {
      color: var(--success-color, #2e7d32);
    }
    .state.scanning ha-icon,
    .state.converting ha-icon,
    .state.ocr ha-icon {
      color: var(--info-color, #0288d1);
    }
    .state.waiting_for_rear ha-icon {
      color: var(--warning-color, #f9a825);
    }
    .state.unreachable ha-icon,
    .state.unavailable ha-icon {
      color: var(--error-color, #c62828);
    }
    .detail {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 6px;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 0.8rem;
      padding: 2px 8px;
      border-radius: 12px;
      background: var(--secondary-background-color, #f3f4f6);
      color: var(--secondary-text-color);
    }
    .chip ha-icon {
      --mdc-icon-size: 16px;
    }
    .chip.problem {
      background: rgba(198, 40, 40, 0.12);
      color: var(--error-color, #c62828);
    }
    .chip.timer {
      font-variant-numeric: tabular-nums;
    }
    .chip.ok {
      background: rgba(46, 125, 50, 0.12);
      color: var(--success-color, #2e7d32);
    }
    .chip.display {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      white-space: pre;
    }
    .device {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .buttons {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      gap: 8px;
    }
    button.action {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 10px 12px;
      border-radius: 8px;
      border: 1px solid var(--divider-color, #ddd);
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color);
      font: inherit;
      cursor: pointer;
      min-height: 44px;
    }
    button.action:hover:not(:disabled) {
      border-color: var(--primary-color);
      color: var(--primary-color);
    }
    button.action:disabled {
      opacity: 0.5;
      cursor: default;
    }
    button.action.highlight {
      border-color: var(--warning-color, #f9a825);
      background: rgba(249, 168, 37, 0.12);
    }
    .spin {
      animation: spin 1s linear infinite;
    }
    @keyframes spin {
      to {
        transform: rotate(360deg);
      }
    }
    .selects {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 8px;
    }
    .select {
      display: flex;
      flex-direction: column;
      gap: 2px;
      font-size: 0.8rem;
      color: var(--secondary-text-color);
      text-transform: capitalize;
    }
    .select select {
      font: inherit;
      padding: 6px;
      border-radius: 6px;
      border: 1px solid var(--divider-color, #ddd);
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color);
    }
    .last-scan {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 10px;
      border-radius: 8px;
      background: var(--secondary-background-color, #f3f4f6);
    }
    .last-scan.empty {
      color: var(--secondary-text-color);
    }
    .last-scan > ha-icon {
      color: var(--error-color, #c62828);
      --mdc-icon-size: 28px;
    }
    .file {
      flex: 1;
      min-width: 0;
    }
    .file-name {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .file-meta {
      font-size: 0.8rem;
      color: var(--secondary-text-color);
    }
    button.icon {
      border: none;
      background: transparent;
      color: var(--primary-color);
      cursor: pointer;
      padding: 6px;
      border-radius: 50%;
    }
    button.icon:hover {
      background: rgba(0, 0, 0, 0.06);
    }
    .footer {
      display: flex;
      justify-content: flex-end;
      font-size: 0.85rem;
    }
    .footer a {
      color: var(--primary-color);
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .footer ha-icon {
      --mdc-icon-size: 16px;
    }
    .error,
    .warning {
      color: var(--error-color, #c62828);
      font-size: 0.85rem;
    }
  `;
}

customElements.define('brother-scanner-card', BrotherScannerCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'brother-scanner-card',
  name: 'Brother Scanner Card',
  description: 'Scan buttons, status and the last scan of a BrotherScannerDocker container',
  preview: true,
  documentationURL: 'https://github.com/PhilippMundhenk/brother-scanner-card',
});

console.info(`%c BROTHER-SCANNER-CARD %c ${CARD_VERSION} `, 'color: white; background: #0ea5e9; font-weight: 700;', 'color: #0ea5e9; background: white; font-weight: 700;');
