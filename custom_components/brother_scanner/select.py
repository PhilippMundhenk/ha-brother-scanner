"""Selects: resolution, mode and source for the next scan, from the device capabilities."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import ScannerConfigEntry
from .coordinator import ScannerCoordinator
from .entity import ScannerEntity

DEFAULT_OPTION = "default"
ICONS = {"resolution": "mdi:image-size-select-large", "mode": "mdi:palette", "source": "mdi:tray-arrow-down"}


async def async_setup_entry(hass: HomeAssistant, entry: ScannerConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(ScanParameterSelect(coordinator, parameter) for parameter in ("resolution", "mode", "source"))


class ScanParameterSelect(ScannerEntity, SelectEntity, RestoreEntity):
    """'default' means: do not send the parameter, the container's setting applies."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: ScannerCoordinator, parameter: str) -> None:
        super().__init__(coordinator, parameter)
        self.parameter = parameter
        self._attr_icon = ICONS[parameter]
        self._attr_current_option = DEFAULT_OPTION

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state in self.options:
            self._attr_current_option = last.state
        self._publish()

    @property
    def options(self) -> list[str]:
        caps = self.coordinator.data.capabilities.get(self.parameter) or {}
        values: Any = caps.get("options") or []
        if isinstance(values, dict):
            # a range (min..max): offer the usual steps inside it
            lo, hi = int(values.get("min", 75)), int(values.get("max", 600))
            values = [v for v in (75, 100, 150, 200, 300, 400, 600, 1200) if lo <= v <= hi]
        options = [DEFAULT_OPTION] + [str(v) for v in values]
        if self._attr_current_option not in options:
            options.append(self._attr_current_option)
        return options

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        caps = self.coordinator.data.capabilities.get(self.parameter) or {}
        default = (self.coordinator.data.actions.get("parameters") or {}).get(self.parameter, {}).get("default")
        return {"container_default": default, "device_default": caps.get("default")}

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self._publish()
        self.async_write_ha_state()

    def _publish(self) -> None:
        value = None if self._attr_current_option == DEFAULT_OPTION else self._attr_current_option
        if self.parameter == "resolution" and value is not None:
            value = int(value)
        self.coordinator.selected[self.parameter] = value
