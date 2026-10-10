"""Buttons: one per enabled scan action (named like the container's web UI) and rear pages."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ScannerConfigEntry
from .api import ScannerApiError
from .coordinator import ScannerCoordinator
from .entity import ScannerEntity

_LOGGER = logging.getLogger(__name__)

ICONS = {
    "file": "mdi:file-document-outline",
    "ocr": "mdi:text-recognition",
    "email": "mdi:book-open-page-variant",
    "image": "mdi:image-outline",
}


async def async_setup_entry(hass: HomeAssistant, entry: ScannerConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    entities: list[ButtonEntity] = [
        ScanButton(coordinator, action) for action in coordinator.data.actions.get("actions", []) if action.get("target")
    ]
    entities.append(RearPagesButton(coordinator))
    async_add_entities(entities)


class ScanButton(ScannerEntity, ButtonEntity):
    """Starts one action with the values of the select entities."""

    def __init__(self, coordinator: ScannerCoordinator, action: dict) -> None:
        self.target = action["target"]
        super().__init__(coordinator, f"scan_{self.target}")
        self._attr_icon = ICONS.get(self.target, "mdi:scanner")
        # the container's label (RENAME_GUI_*) is what people know from the web UI
        self._attr_name = action.get("label") or self.target
        self._attr_entity_registry_enabled_default = bool(action.get("enabled", True))

    @property
    def available(self) -> bool:
        return super().available and self._action().get("enabled", False)

    def _action(self) -> dict:
        for action in self.coordinator.data.actions.get("actions", []):
            if action.get("target") == self.target:
                return action
        return {}

    async def async_press(self) -> None:
        selected = self.coordinator.selected
        try:
            if self.target == "email":
                waiting = self.coordinator.data.waiting_job
                if waiting is not None:
                    await self.coordinator.api.scan_rear(waiting["job"])
                else:
                    await self.coordinator.api.scan("email")
            else:
                await self.coordinator.api.scan(
                    self.target,
                    resolution=selected.get("resolution"),
                    mode=selected.get("mode"),
                    source=selected.get("source"),
                )
        except ScannerApiError as err:
            raise HomeAssistantError(f"Scan could not be started: {err}") from err
        await self.coordinator.async_request_refresh()


class RearPagesButton(ScannerEntity, ButtonEntity):
    """Scan the rear pages of the job that waits for them; only available while one waits."""

    _attr_icon = "mdi:book-open-page-variant-outline"

    def __init__(self, coordinator: ScannerCoordinator) -> None:
        super().__init__(coordinator, "scan_rear")

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.waiting_job is not None

    async def async_press(self) -> None:
        waiting = self.coordinator.data.waiting_job
        if waiting is None:
            raise HomeAssistantError("No scan is waiting for rear pages")
        try:
            await self.coordinator.api.scan_rear(waiting["job"])
        except ScannerApiError as err:
            raise HomeAssistantError(f"Rear scan could not be started: {err}") from err
        await self.coordinator.async_request_refresh()
