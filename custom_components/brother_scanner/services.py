"""Services: brother_scanner.scan, scan_rear, download_last_scan."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv, device_registry as dr

from .api import ScannerApiError
from .const import (
    ATTR_JOB,
    ATTR_MODE,
    ATTR_OCR,
    ATTR_PATH,
    ATTR_RESOLUTION,
    ATTR_SOURCE,
    ATTR_TARGET,
    ATTR_WAIT,
    DOMAIN,
    SERVICE_DOWNLOAD_LAST_SCAN,
    SERVICE_SCAN,
    SERVICE_SCAN_REAR,
)
from .coordinator import ScannerCoordinator

ATTR_DEVICE_ID = "device_id"

SCAN_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_TARGET, default="file"): vol.In(["file", "ocr", "email", "image"]),
        vol.Optional(ATTR_RESOLUTION): vol.All(vol.Coerce(int), vol.Range(min=50, max=9600)),
        vol.Optional(ATTR_MODE): cv.string,
        vol.Optional(ATTR_SOURCE): cv.string,
        vol.Optional(ATTR_WAIT, default=False): cv.boolean,
    }
)
SCAN_REAR_SCHEMA = vol.Schema({vol.Optional(ATTR_DEVICE_ID): cv.string, vol.Optional(ATTR_JOB): cv.string})
DOWNLOAD_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_PATH): cv.string,
        vol.Optional(ATTR_OCR, default=False): cv.boolean,
    }
)


def _coordinator_for(hass: HomeAssistant, call: ServiceCall) -> ScannerCoordinator:
    """The coordinator for device_id, or the only configured one."""
    coordinators: dict[str, ScannerCoordinator] = hass.data.get(DOMAIN, {})
    if not coordinators:
        raise ServiceValidationError("No Brother scanner configured")
    device_id = call.data.get(ATTR_DEVICE_ID)
    if device_id:
        device = dr.async_get(hass).async_get(device_id)
        if device is None:
            raise ServiceValidationError(f"Unknown device {device_id}")
        for entry_id in device.config_entries:
            if entry_id in coordinators:
                return coordinators[entry_id]
        raise ServiceValidationError(f"Device {device_id} is not a Brother scanner")
    if len(coordinators) > 1:
        raise ServiceValidationError("Several scanners configured, pass device_id")
    return next(iter(coordinators.values()))


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the three services once."""
    if hass.services.has_service(DOMAIN, SERVICE_SCAN):
        return

    async def scan(call: ServiceCall) -> ServiceResponse:
        coordinator = _coordinator_for(hass, call)
        try:
            result = await coordinator.api.scan(
                call.data[ATTR_TARGET],
                resolution=call.data.get(ATTR_RESOLUTION),
                mode=call.data.get(ATTR_MODE),
                source=call.data.get(ATTR_SOURCE),
                wait=call.data.get(ATTR_WAIT, False),
            )
        except ScannerApiError as err:
            raise HomeAssistantError(f"Scan failed: {err}") from err
        await coordinator.async_request_refresh()
        return {"job": result.get("job"), "state": result.get("state"), "target": call.data[ATTR_TARGET]}

    async def scan_rear(call: ServiceCall) -> ServiceResponse:
        coordinator = _coordinator_for(hass, call)
        job = call.data.get(ATTR_JOB)
        if not job:
            waiting = coordinator.data.waiting_job if coordinator.data else None
            if waiting is None:
                raise ServiceValidationError("No scan is waiting for rear pages")
            job = waiting["job"]
        try:
            result = await coordinator.api.scan_rear(job)
        except ScannerApiError as err:
            raise HomeAssistantError(f"Rear scan failed: {err}") from err
        await coordinator.async_request_refresh()
        return {"job": job, "state": result.get("state")}

    async def download_last_scan(call: ServiceCall) -> ServiceResponse:
        coordinator = _coordinator_for(hass, call)
        data = coordinator.data
        file_name = _last_file_name(data, call.data.get(ATTR_OCR, False))
        if not file_name:
            raise ServiceValidationError("No scan available yet")
        target = Path(call.data[ATTR_PATH])
        if not hass.config.is_allowed_path(str(target)):
            raise ServiceValidationError(f"{target} is not in allowlist_external_dirs")
        try:
            content = await coordinator.api.download(file_name)
        except ScannerApiError as err:
            raise HomeAssistantError(f"Download failed: {err}") from err

        def write() -> str:
            if target.is_dir() or str(call.data[ATTR_PATH]).endswith(("/", "\\")):
                target.mkdir(parents=True, exist_ok=True)
                destination = target / file_name
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                destination = target
            destination.write_bytes(content)
            return str(destination)

        try:
            written = await hass.async_add_executor_job(write)
        except OSError as err:
            raise HomeAssistantError(f"Could not write {file_name} to {target}: {err}") from err
        return {"file": file_name, "path": written, "size": len(content)}

    hass.services.async_register(DOMAIN, SERVICE_SCAN, scan, schema=SCAN_SCHEMA, supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, SERVICE_SCAN_REAR, scan_rear, schema=SCAN_REAR_SCHEMA, supports_response=SupportsResponse.OPTIONAL)
    hass.services.async_register(
        DOMAIN, SERVICE_DOWNLOAD_LAST_SCAN, download_last_scan, schema=DOWNLOAD_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )


def _last_file_name(data: Any, ocr: bool) -> str | None:
    """Newest file: the OCR copy of the latest job when asked and available, else the newest PDF."""
    if data is None:
        return None
    latest = data.latest_job or {}
    if ocr and latest.get("ocr") == "done" and latest.get("ocr_file"):
        return latest["ocr_file"]
    if data.newest_file:
        return data.newest_file.get("file")
    return latest.get("file")
