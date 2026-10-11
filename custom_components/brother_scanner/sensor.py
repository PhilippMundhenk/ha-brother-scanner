"""Sensors: scanner state, last scan, OCR queue, last job, version."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScannerConfigEntry
from .const import JOB_STATES, SCANNER_STATES
from .coordinator import ScannerCoordinator
from .entity import ScannerEntity


async def async_setup_entry(hass: HomeAssistant, entry: ScannerConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            ScannerStateSensor(coordinator),
            LastScanSensor(coordinator),
            OcrQueueSensor(coordinator),
            LastJobStateSensor(coordinator),
            LastErrorSensor(coordinator),
            VersionSensor(coordinator),
        ]
    )


class ScannerStateSensor(ScannerEntity, SensorEntity):
    """idle / scanning / waiting_for_rear / converting / ocr / unreachable, with everything the card needs as attributes."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = SCANNER_STATES

    def __init__(self, coordinator: ScannerCoordinator) -> None:
        super().__init__(coordinator, "scanner_state")

    @property
    def native_value(self) -> str:
        return self.coordinator.data.state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        latest = data.latest_job or {}
        waiting = data.waiting_job
        return {
            "job": latest.get("job"),
            "job_state": latest.get("state"),
            "pages": latest.get("pages"),
            "waiting_job": waiting.get("job") if waiting else None,
            "waiting_until": waiting.get("waiting_until") if waiting else None,
            "reachable": data.reachable,
            "queue": data.queue,
            "actions": [
                {"target": a.get("target"), "label": a.get("label"), "enabled": a.get("enabled")}
                for a in data.actions.get("actions", [])
            ],
            "capabilities": data.capabilities,
            "model": data.device.get("model"),
            "image_url": self.image_url(),
            "web_ui_url": self.coordinator.api.base_url,
            "version": data.actions.get("version"),
        }


class LastScanSensor(ScannerEntity, SensorEntity):
    """File name of the newest PDF; download URLs and size as attributes."""

    def __init__(self, coordinator: ScannerCoordinator) -> None:
        super().__init__(coordinator, "last_scan")

    @property
    def native_value(self) -> str | None:
        newest = self.coordinator.data.newest_file
        return newest.get("file") if newest else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        newest = self.coordinator.data.newest_file or {}
        latest = self.coordinator.data.latest_job or {}
        name = newest.get("file")
        # the OCR copy is a second download only while it is not the newest file itself
        # (REMOVE_ORIGINAL_AFTER_OCR leaves just the copy)
        ocr_file = latest.get("ocr_file") if latest.get("ocr") == "done" else None
        if ocr_file and ocr_file == name:
            ocr_file = None
        attributes: dict[str, Any] = {
            "size": newest.get("size"),
            "modified": _iso(newest.get("fileModificationTime")),
            "download_url": self.coordinator.proxy_download_url(name) if name else None,
            "direct_url": self.coordinator.api.download_url(name) if name else None,
            "ocr_file": ocr_file,
            "ocr_download_url": self.coordinator.proxy_download_url(ocr_file) if ocr_file else None,
            "is_ocr_copy": bool(name) and name == latest.get("ocr_file") and latest.get("ocr") == "done",
        }
        return attributes


class OcrQueueSensor(ScannerEntity, SensorEntity):
    """Scans waiting for OCR."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "scans"
    _attr_icon = "mdi:text-recognition"

    def __init__(self, coordinator: ScannerCoordinator) -> None:
        super().__init__(coordinator, "ocr_queue")

    @property
    def native_value(self) -> int:
        return int(self.coordinator.data.queue.get("pending") or 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        queue = self.coordinator.data.queue
        return {
            "in_progress": queue.get("in_progress", 0),
            "failed": queue.get("failed", 0),
            "holding": queue.get("holding", False),
        }


class LastJobStateSensor(ScannerEntity, SensorEntity):
    """State of the newest job (queued ... done / failed)."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = JOB_STATES
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: ScannerCoordinator) -> None:
        super().__init__(coordinator, "last_job_state")

    @property
    def native_value(self) -> str | None:
        latest = self.coordinator.data.latest_job
        if latest is None:
            return None
        state = latest.get("state") or "unknown"
        return state if state in JOB_STATES else "unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        latest = self.coordinator.data.latest_job or {}
        return {
            "job": latest.get("job"),
            "action": latest.get("action"),
            "pages": latest.get("pages"),
            "file": latest.get("file"),
            "ocr": latest.get("ocr"),
            "started": latest.get("started"),
            "finished": latest.get("finished"),
            "params": latest.get("params"),
        }


class LastErrorSensor(ScannerEntity, SensorEntity):
    """Error text of the newest job, empty when it succeeded."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(self, coordinator: ScannerCoordinator) -> None:
        super().__init__(coordinator, "last_error")

    @property
    def native_value(self) -> str:
        latest = self.coordinator.data.latest_job or {}
        if latest.get("state") == "failed":
            return str(latest.get("error") or "failed")[:255]
        queue = self.coordinator.data.queue
        if queue.get("failed"):
            return f"{queue['failed']} OCR job(s) failed"
        return ""


class VersionSensor(ScannerEntity, SensorEntity):
    """Image version of the container."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:docker"

    def __init__(self, coordinator: ScannerCoordinator) -> None:
        super().__init__(coordinator, "version")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.actions.get("version")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"api_version": self.coordinator.data.actions.get("api_version")}


def _iso(timestamp: Any) -> str | None:
    try:
        return datetime.fromtimestamp(int(timestamp), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return None
