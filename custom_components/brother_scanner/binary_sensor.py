"""Binary sensors: scanning, waiting for rear pages, OCR running, reachable, problem."""

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
    ),
    ScannerBinarySensorDescription(
        key="problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: (d.latest_job or {}).get("state") == "failed" or bool(d.queue.get("failed")),
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
        if self._key == "reachable":
            # None: the container has the reachability check disabled
            return super().available and self.coordinator.data.reachable is not None
        return super().available
