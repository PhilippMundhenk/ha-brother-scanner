"""Base entity: device info shared by every platform."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_HIDE_IMAGE, CONF_IMAGE_URL, DOMAIN, IMAGE_FAMILIES, IMAGE_GENERIC, MANUFACTURER, STATIC_URL_BASE
from .coordinator import ScannerCoordinator


class ScannerEntity(CoordinatorEntity[ScannerCoordinator]):
    """One entity of the scanner device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ScannerCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_translation_key = key

    @property
    def device_info(self) -> DeviceInfo:
        data = self.coordinator.data
        device = data.device if data else {}
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            manufacturer=MANUFACTURER,
            model=device.get("model") or "Scanner",
            name=device.get("name") or self.coordinator.entry.title,
            sw_version=(data.actions.get("version") if data else None) or None,
            configuration_url=self.coordinator.api.base_url,
        )

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data is not None

    def image_url(self) -> str | None:
        """The picture for the card: configured URL, or a generic illustration by model family."""
        options = self.coordinator.entry.options
        if options.get(CONF_HIDE_IMAGE):
            return None
        if options.get(CONF_IMAGE_URL):
            return options[CONF_IMAGE_URL]
        model = (self.coordinator.data.device.get("model") or "").upper() if self.coordinator.data else ""
        for prefix, file in IMAGE_FAMILIES.items():
            if model.startswith(prefix):
                return f"{STATIC_URL_BASE}/{file}"
        return f"{STATIC_URL_BASE}/{IMAGE_GENERIC}"
