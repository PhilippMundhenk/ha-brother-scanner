"""Binary sensors: scanning, waiting for rear pages, OCR running, reachable, problem,
and from the device itself (container 2.2+): Scan-to-PC registered, scan key enabled."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScannerConfigEntry
from .const import STATE_CONVERTING, STATE_SCANNING, STATE_WAITING_FOR_REAR
from .coordinator import ScannerData
from .entity import ScannerEntity


@dataclass(frozen=True, kw_only=True)
class ScannerBinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Callable[[ScannerData], bool | None]
    # None: available whenever the container answers; else only when this says so
    available_fn: Callable[[ScannerData], bool] | None = None


def _device(d: ScannerData, key: str) -> bool | None:
    return (d.device_status or {}).get(key)


def _device_has(key: str) -> Callable[[ScannerData], bool]:
    return lambda d: _device(d, key) is not None


DESCRIPTIONS: tuple[ScannerBinarySensorDescription, ...] = (
    ScannerBinarySensorDescription(
        key="scanning",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:scanner",
        value_fn=lambda d: d.state in (STATE_SCANNING, STATE_WAITING_FOR_REAR, STATE_CONVERTING),
    ),
    ScannerBinarySensorDescription(
        key="waiting_for_rear_pages",
        icon="mdi:book-open-page-variant",
        value_fn=lambda d: d.state == STATE_WAITING_FOR_REAR,
    ),
    ScannerBinarySensorDescription(
        key="ocr_running",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:text-recognition",
        value_fn=lambda d: bool(d.status.get("ocr") or d.queue.get("in_progress")),
    ),
    ScannerBinarySensorDescription(
        key="reachable",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.reachable,
        # None: the container has the reachability check disabled
        available_fn=lambda d: d.reachable is not None,
    ),
    ScannerBinarySensorDescription(
        key="problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: (d.latest_job or {}).get("state") == "failed" or bool(d.queue.get("failed")),
    ),
    # From the scanner itself (GET /api/scanner/device): does the device currently
    # list the container as a Scan-to-PC destination, i.e. do its buttons reach us?
    ScannerBinarySensorDescription(
        key="registered",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:cloud-check-outline",
        value_fn=lambda d: _device(d, "registered"),
        available_fn=_device_has("registered"),
    ),
    ScannerBinarySensorDescription(
        key="scan_key_enabled",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:gesture-tap-button",
        value_fn=lambda d: _device(d, "scan_key_enabled"),
        available_fn=_device_has("scan_key_enabled"),
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ScannerConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(ScannerBinarySensor(coordinator, description) for description in DESCRIPTIONS)


class ScannerBinarySensor(ScannerEntity, BinarySensorEntity):
    entity_description: ScannerBinarySensorDescription

    def __init__(self, coordinator, description: ScannerBinarySensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        available_fn = self.entity_description.available_fn
        return available_fn is None or available_fn(self.coordinator.data)
