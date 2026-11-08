// The slice of the Home Assistant frontend objects the card uses. Kept local
// so the card has no dependency on the frontend's type packages.

export interface HassEntityState {
  entity_id: string;
  state: string;
  attributes: Record<string, any>;
  last_changed: string;
  last_updated: string;
}

export interface HassEntityRegistryEntry {
  entity_id: string;
  device_id?: string;
  translation_key?: string;
  platform?: string;
  hidden?: boolean;
  name?: string;
}

export interface HomeAssistant {
  states: Record<string, HassEntityState>;
  entities: Record<string, HassEntityRegistryEntry>;
  devices?: Record<string, { id: string; name?: string; name_by_user?: string; model?: string }>;
  language?: string;
  locale?: { language: string };
  callService: (domain: string, service: string, data?: Record<string, unknown>, target?: Record<string, unknown>) => Promise<unknown>;
  callWS: <T>(message: Record<string, unknown>) => Promise<T>;
  hassUrl?: (path?: string) => string;
  formatEntityState?: (stateObj: HassEntityState, state?: string) => string;
  formatEntityAttributeValue?: (stateObj: HassEntityState, attribute: string, value?: unknown) => string;
}

export interface ScannerAction {
  target: string;
  label: string;
  enabled: boolean;
}

export interface CardConfig {
  type: string;
  entity: string;
  name?: string;
  show_image?: boolean;
  image?: string;
  show_buttons?: boolean;
  buttons?: string[];
  show_selects?: boolean;
  show_last_scan?: boolean;
  show_link?: boolean;
  compact?: boolean;
  // the scanner's own state, read over SNMP by the container (2.2+) and
  // exposed as attributes of the state sensor; each value can be switched off
  show_device?: boolean;
  show_registered?: boolean;
  show_display?: boolean;
  show_serial?: boolean;
  show_firmware?: boolean;
  show_scan_key?: boolean;
}

export interface ScannerEntities {
  state?: string;
  lastScan?: string;
  ocrQueue?: string;
  rear?: string;
  buttons: Record<string, string>; // target -> entity_id
  selects: Record<string, string>; // parameter -> entity_id
}

// The frontend's card registry
declare global {
  interface Window {
    customCards?: { type: string; name: string; description: string; preview?: boolean; documentationURL?: string }[];
  }
}
