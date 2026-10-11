"""The three services."""

from __future__ import annotations

from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr
import pytest

from custom_components.brother_scanner.const import DOMAIN

from .conftest import PDF, FakeContainer, setup_entry


async def test_scan_service_returns_job(hass: HomeAssistant, config_entry, container: FakeContainer) -> None:
    await setup_entry(hass, config_entry)
    response = await hass.services.async_call(
        DOMAIN, "scan", {"target": "ocr", "resolution": 300, "source": "FlatBed"}, blocking=True, return_response=True
    )
    assert response == {"job": "2026-10-10-11-00-00", "state": "queued", "target": "ocr"}
    post = [r for r in container.requests if r[0] == "POST"][-1]
    assert post[2] == {"target": "ocr", "resolution": "300", "source": "FlatBed"}

    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, config_entry.entry_id)})
    response = await hass.services.async_call(DOMAIN, "scan", {"device_id": device.id, "target": "file", "wait": True}, blocking=True, return_response=True)
    assert response["job"] == "2026-10-10-11-00-00"
    assert [r for r in container.requests if r[0] == "POST"][-1][2] == {"target": "file", "wait": "true"}

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "scan", {"device_id": "nope", "target": "file"}, blocking=True)


async def test_scan_service_error(hass: HomeAssistant, config_entry, container: FakeContainer) -> None:
    await setup_entry(hass, config_entry)
    container.token = "secret"  # the integration has none configured: 401
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(DOMAIN, "scan", {"target": "file"}, blocking=True)


async def test_scan_rear_service(hass: HomeAssistant, config_entry, container: FakeContainer) -> None:
    await setup_entry(hass, config_entry)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "scan_rear", {}, blocking=True)
    response = await hass.services.async_call(DOMAIN, "scan_rear", {"job": "2026-10-10-10-00-00"}, blocking=True, return_response=True)
    assert response == {"job": "2026-10-10-10-00-00", "state": "scanning_rear"}

    container.jobs.insert(0, {"job": "2026-10-10-12-00-00", "state": "waiting_for_rear"})
    await hass.data[DOMAIN][config_entry.entry_id].async_refresh()
    response = await hass.services.async_call(DOMAIN, "scan_rear", {}, blocking=True, return_response=True)
    assert response["job"] == "2026-10-10-12-00-00"


async def test_download_last_scan(hass: HomeAssistant, config_entry, container: FakeContainer, tmp_path: Path) -> None:
    await setup_entry(hass, config_entry)
    hass.config.allowlist_external_dirs = {str(tmp_path)}

    response = await hass.services.async_call(DOMAIN, "download_last_scan", {"path": str(tmp_path) + "/"}, blocking=True, return_response=True)
    assert response["file"] == "2026-10-10-10-00-00.pdf"
    assert (tmp_path / "2026-10-10-10-00-00.pdf").read_bytes() == PDF

    response = await hass.services.async_call(
        DOMAIN, "download_last_scan", {"path": str(tmp_path / "sub" / "latest.pdf"), "ocr": True}, blocking=True, return_response=True
    )
    assert response["file"] == "2026-10-10-10-00-00-ocr.pdf"
    assert (tmp_path / "sub" / "latest.pdf").read_bytes() == PDF

    # a path that cannot be written is reported, not a traceback
    blocked = tmp_path / "blocked"
    blocked.write_text("a file, not a directory")
    with pytest.raises(HomeAssistantError, match="Could not write"):
        await hass.services.async_call(DOMAIN, "download_last_scan", {"path": str(blocked / "x.pdf")}, blocking=True, return_response=True)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "download_last_scan", {"path": "/etc/scan.pdf"}, blocking=True)

    container.files = []
    container.jobs = []
    await hass.data[DOMAIN][config_entry.entry_id].async_refresh()
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "download_last_scan", {"path": str(tmp_path) + "/"}, blocking=True)
