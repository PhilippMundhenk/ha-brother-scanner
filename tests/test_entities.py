"""Entities, buttons, selects, events and the download view."""

from __future__ import annotations

from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.brother_scanner.const import DOMAIN, EVENT_OCR_DONE, EVENT_SCAN_DONE, EVENT_SCAN_STARTED, EVENT_WAITING_FOR_REAR

from .conftest import PDF, FakeContainer, setup_entry


async def poll(hass: HomeAssistant, entry) -> None:
    """One coordinator refresh, as the timer would trigger it."""
    await hass.data[DOMAIN][entry.entry_id].async_refresh()
    await hass.async_block_till_done()


async def test_entities_and_device(hass: HomeAssistant, config_entry, container: FakeContainer) -> None:
    await setup_entry(hass, config_entry)

    state = hass.states.get("sensor.office_scanner_state")
    assert state.state == "idle"
    assert state.attributes["model"] == "MFC-L2700DW"
    assert state.attributes["image_url"] == "/brother_scanner/static/mfc.svg"
    assert state.attributes["web_ui_url"].startswith("http://")
    assert [a["label"] for a in state.attributes["actions"]] == ["Archive", "Rear pages", "Scan to OCR", "Scan to image"]

    last = hass.states.get("sensor.office_scanner_last_scan")
    assert last.state == "2026-10-10-10-00-00.pdf"
    assert last.attributes["download_url"] == f"/api/brother_scanner/{config_entry.entry_id}/download/2026-10-10-10-00-00.pdf"
    assert last.attributes["ocr_file"] == "2026-10-10-10-00-00-ocr.pdf"
    assert hass.states.get("sensor.office_scanner_ocr_queue").state == "0"
    assert hass.states.get("sensor.office_scanner_last_job").state == "done"
    assert hass.states.get("sensor.office_scanner_last_error").state == ""
    assert hass.states.get("sensor.office_scanner_container_version").state == "test-1"
    assert hass.states.get("binary_sensor.office_scanner_scanning").state == "off"
    assert hass.states.get("binary_sensor.office_scanner_scanner_reachable").state == "on"
    assert hass.states.get("binary_sensor.office_scanner_problem").state == "off"

    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, config_entry.entry_id)})
    assert device.manufacturer == "Brother"
    assert device.model == "MFC-L2700DW"
    assert device.sw_version == "test-1"

    registry = er.async_get(hass)
    assert registry.async_get("button.office_scanner_archive") is not None
    disabled = registry.async_get("button.office_scanner_scan_to_image")
    assert disabled is not None and disabled.disabled_by is er.RegistryEntryDisabler.INTEGRATION
    # the email action ("Rear pages") is enabled, so no second rear-pages button
    assert hass.states.get("button.office_scanner_scan_rear_pages") is None


async def test_state_derivation_and_events(hass: HomeAssistant, config_entry, container: FakeContainer) -> None:
    await setup_entry(hass, config_entry)
    events: list[Event] = []
    for name in (EVENT_SCAN_STARTED, EVENT_WAITING_FOR_REAR, EVENT_SCAN_DONE, EVENT_OCR_DONE):
        hass.bus.async_listen(name, events.append)

    # a new job starts and scans
    container.status["scan"] = True
    container.jobs.insert(0, {"job": "2026-10-10-11-00-00", "state": "scanning", "action": "file"})
    await poll(hass, config_entry)
    assert hass.states.get("sensor.office_scanner_state").state == "scanning"
    assert hass.states.get("binary_sensor.office_scanner_scanning").state == "on"
    assert [e.event_type for e in events] == [EVENT_SCAN_STARTED]

    # waits for rear pages: the rear button becomes available
    container.status["scan"] = False
    container.status["waiting"] = True
    container.jobs[0].update(state="waiting_for_rear", pages=1, waiting_until="2026-10-10T11:02:00+0000")
    await poll(hass, config_entry)
    assert hass.states.get("sensor.office_scanner_state").state == "waiting_for_rear"
    assert hass.states.get("sensor.office_scanner_state").attributes["waiting_job"] == "2026-10-10-11-00-00"
    assert events[-1].event_type == EVENT_WAITING_FOR_REAR

    # done, then the OCR copy appears
    container.status["waiting"] = False
    container.jobs[0].update(state="done", pages=2, file="2026-10-10-11-00-00.pdf", ocr_file="2026-10-10-11-00-00-ocr.pdf")
    container.files.insert(0, {"file": "2026-10-10-11-00-00.pdf", "size": 10, "fileModificationTime": 1760094000})
    await poll(hass, config_entry)
    assert events[-1].event_type == EVENT_SCAN_DONE
    assert events[-1].data["download_url"].endswith("/download/2026-10-10-11-00-00.pdf")
    assert hass.states.get("sensor.office_scanner_last_scan").state == "2026-10-10-11-00-00.pdf"
    container.jobs[0]["ocr"] = "done"
    await poll(hass, config_entry)
    assert events[-1].event_type == EVENT_OCR_DONE

    # OCR queue and failures
    container.status["queue"] = {"pending": 3, "in_progress": 1, "failed": 1, "holding": True}
    await poll(hass, config_entry)
    assert hass.states.get("sensor.office_scanner_ocr_queue").state == "3"
    assert hass.states.get("sensor.office_scanner_state").state == "ocr"
    assert hass.states.get("binary_sensor.office_scanner_problem").state == "on"
    assert hass.states.get("sensor.office_scanner_last_error").state == "1 OCR job(s) failed"

    # scanner unreachable, container still answers
    container.status = {"scan": False, "waiting": False, "ocr": False, "reachable": False, "queue": {}}
    await poll(hass, config_entry)
    assert hass.states.get("sensor.office_scanner_state").state == "unreachable"
    assert hass.states.get("binary_sensor.office_scanner_scanner_reachable").state == "off"

    # container gone: entities unavailable, back when it answers again
    container.fail_status = True
    await poll(hass, config_entry)
    assert hass.states.get("sensor.office_scanner_state").state == "unavailable"
    container.fail_status = False
    await poll(hass, config_entry)
    assert hass.states.get("sensor.office_scanner_state").state == "unreachable"


async def test_buttons_and_selects(hass: HomeAssistant, config_entry, container: FakeContainer) -> None:
    await setup_entry(hass, config_entry)

    select = hass.states.get("select.office_scanner_resolution")
    assert select.state == "default"
    assert select.attributes["options"] == ["default", "100", "200", "300", "600"]
    await hass.services.async_call("select", "select_option", {"entity_id": "select.office_scanner_resolution", "option": "600"}, blocking=True)
    await hass.services.async_call("select", "select_option", {"entity_id": "select.office_scanner_mode", "option": "True Gray"}, blocking=True)

    await hass.services.async_call("button", "press", {"entity_id": "button.office_scanner_archive"}, blocking=True)
    await hass.async_block_till_done()
    posts = [r for r in container.requests if r[0] == "POST"]
    assert posts[-1][1] == "/api/scanner/scanto"
    assert posts[-1][2] == {"target": "file", "resolution": "600", "mode": "True Gray"}

    # the rear-pages action attaches to the waiting job when there is one
    container.status["waiting"] = True
    container.jobs.insert(0, {"job": "2026-10-10-11-00-00", "state": "waiting_for_rear"})
    await poll(hass, config_entry)
    await hass.services.async_call("button", "press", {"entity_id": "button.office_scanner_rear_pages"}, blocking=True)
    posts = [r for r in container.requests if r[0] == "POST"]
    assert posts[-1][1] == "/api/jobs/2026-10-10-11-00-00/rear"


async def test_token_is_sent(hass: HomeAssistant, config_entry, container: FakeContainer) -> None:
    container.token = "secret"
    hass.config_entries.async_update_entry(config_entry, data={**config_entry.data, "token": "secret"})
    await setup_entry(hass, config_entry)
    await hass.services.async_call("button", "press", {"entity_id": "button.office_scanner_archive"}, blocking=True)
    assert [r for r in container.requests if r[0] == "POST"][-1][1] == "/api/scanner/scanto"


async def test_download_view(hass: HomeAssistant, config_entry, hass_client) -> None:
    await setup_entry(hass, config_entry)
    client = await hass_client()
    res = await client.get(f"/api/brother_scanner/{config_entry.entry_id}/download/2026-10-10-10-00-00.pdf")
    assert res.status == 200
    assert res.content_type == "application/pdf"
    assert await res.read() == PDF
    assert (await client.get(f"/api/brother_scanner/{config_entry.entry_id}/download/missing.pdf")).status == 404
    assert (await client.get(f"/api/brother_scanner/{config_entry.entry_id}/download/notes.txt")).status == 400
    assert (await client.get("/api/brother_scanner/nope/download/x.pdf")).status == 404
    assert (await client.get("/brother_scanner/static/mfc.svg")).status == 200


async def test_unload(hass: HomeAssistant, config_entry) -> None:
    await setup_entry(hass, config_entry)
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.office_scanner_state").state == "unavailable"


async def test_rear_button_only_without_email_action(hass: HomeAssistant, config_entry, container: FakeContainer) -> None:
    container.actions["actions"][1]["enabled"] = False  # DISABLE_GUI_SCANTOEMAIL in the container
    await setup_entry(hass, config_entry)
    rear = hass.states.get("button.office_scanner_scan_rear_pages")
    assert rear is not None and rear.state == "unavailable", "nothing waits for rear pages yet"

    container.status["waiting"] = True
    container.jobs.insert(0, {"job": "2026-10-10-11-00-00", "state": "waiting_for_rear"})
    await poll(hass, config_entry)
    assert hass.states.get("button.office_scanner_scan_rear_pages").state != "unavailable"
    await hass.services.async_call("button", "press", {"entity_id": "button.office_scanner_scan_rear_pages"}, blocking=True)
    await hass.async_block_till_done()
    posts = [r for r in container.requests if r[0] == "POST"]
    assert posts[-1][1] == "/api/jobs/2026-10-10-11-00-00/rear"
