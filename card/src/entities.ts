import type { HomeAssistant, ScannerEntities } from './types';

/**
 * Finds the other entities of the scanner device from the state sensor: the
 * integration gives every entity a translation_key (scanner_state, last_scan,
 * ocr_queue, scan_<target>, scan_rear, resolution, mode, source), which the
 * entity registry exposes to the frontend.
 */
export function discoverEntities(hass: HomeAssistant, stateEntityId: string): ScannerEntities {
  const result: ScannerEntities = { state: stateEntityId, buttons: {}, selects: {} };
  const registry = hass.entities || {};
  const own = registry[stateEntityId];
  if (!own || !own.device_id) {
    return fallbackByName(hass, stateEntityId, result);
  }
  for (const entry of Object.values(registry)) {
    if (entry.device_id !== own.device_id || entry.hidden) continue;
    const key = entry.translation_key || '';
    const id = entry.entity_id;
    if (key === 'last_scan') result.lastScan = id;
    else if (key === 'ocr_queue') result.ocrQueue = id;
    else if (key === 'scan_rear') result.rear = id;
    else if (key.startsWith('scan_') && id.startsWith('button.')) result.buttons[key.slice(5)] = id;
    else if (['resolution', 'mode', 'source'].includes(key) && id.startsWith('select.')) result.selects[key] = id;
  }
  return result;
}

/** Older registries without translation_key: guess from the entity id prefix. */
function fallbackByName(hass: HomeAssistant, stateEntityId: string, result: ScannerEntities): ScannerEntities {
  const prefix = stateEntityId.replace(/^sensor\./, '').replace(/_state$/, '');
  const states = hass.states;
  if (states[`sensor.${prefix}_last_scan`]) result.lastScan = `sensor.${prefix}_last_scan`;
  if (states[`sensor.${prefix}_ocr_queue`]) result.ocrQueue = `sensor.${prefix}_ocr_queue`;
  if (states[`button.${prefix}_scan_rear_pages`]) result.rear = `button.${prefix}_scan_rear_pages`;
  for (const parameter of ['resolution', 'mode', 'source']) {
    if (states[`select.${prefix}_${parameter}`]) result.selects[parameter] = `select.${prefix}_${parameter}`;
  }
  const actions = (states[stateEntityId]?.attributes.actions || []) as { target: string; label: string }[];
  for (const action of actions) {
    const slug = action.label.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
    const id = `button.${prefix}_${slug}`;
    if (states[id]) result.buttons[action.target] = id;
  }
  return result;
}
