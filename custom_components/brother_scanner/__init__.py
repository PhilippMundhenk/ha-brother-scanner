"""Brother Scanner (Docker): scan buttons, state and downloads for BrotherScannerDocker."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ScannerApi, ScannerAuthError, ScannerCannotConnect
from .const import CONF_SSL, CONF_TOKEN, DEFAULT_PORT, DOMAIN, STATIC_URL_BASE
from .coordinator import ScannerCoordinator
from .http import ScannerDownloadView
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SELECT, Platform.SENSOR]

# configured through the UI only
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type ScannerConfigEntry = ConfigEntry[ScannerCoordinator]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the services and the HTTP pieces once."""
    async_setup_services(hass)
    hass.http.register_view(ScannerDownloadView())
    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL_BASE, str(Path(__file__).parent / "images"), cache_headers=True)]
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ScannerConfigEntry) -> bool:
    """Connect to one container."""
    api = ScannerApi(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data.get(CONF_PORT, DEFAULT_PORT),
        token=entry.data.get(CONF_TOKEN),
        ssl=entry.data.get(CONF_SSL, False),
    )
    coordinator = ScannerCoordinator(hass, entry, api)
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady:
        raise
    except ScannerAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except ScannerCannotConnect as err:
        raise ConfigEntryNotReady(str(err)) from err

    entry.runtime_data = coordinator
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ScannerConfigEntry) -> None:
    """Options changed (poll interval, image): reload."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ScannerConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unloaded
