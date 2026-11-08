"""The dashboard card: served by the integration and registered as a resource.

The card (``card/`` in the repository, built into ``www/``) ships with the
integration, so a dashboard never runs a card that does not match the
entities. On setup the integration serves the bundle under ``CARD_URL`` and
registers it as a dashboard resource of type module:

- storage mode (the default): one resource ``CARD_URL?v=<version>``, created
  or updated in place, so the browser fetches the new file after an update;
- YAML mode, where resources are the user's to manage: the card is loaded on
  every frontend page instead (``add_extra_js_url``), nothing to add by hand.

Removing the last config entry removes the resource again.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import CARD_FILENAME, CARD_URL, CARD_URL_BASE, DOMAIN

_LOGGER = logging.getLogger(__name__)

# hass.data key of the lovelace component (a dict before 2025.2, a dataclass since)
LOVELACE_DOMAIN = "lovelace"


def _storage_resources(hass: HomeAssistant) -> ResourceStorageCollection | None:
    """The dashboard resources when they are managed in storage mode."""
    data = hass.data.get(LOVELACE_DOMAIN)
    if data is None:
        return None
    resources = data.get("resources") if isinstance(data, dict) else getattr(data, "resources", None)
    return resources if isinstance(resources, ResourceStorageCollection) else None


async def _loaded(resources: ResourceStorageCollection) -> ResourceStorageCollection:
    if not resources.loaded:
        await resources.async_load()
        resources.loaded = True
    return resources


def _ours(item: dict[str, Any]) -> bool:
    return str(item.get("url", "")).split("?")[0] == CARD_URL


def _foreign_copies(items: list[dict[str, Any]]) -> list[str]:
    """Other resources that load a brother-scanner-card (the old HACS plugin)."""
    return [
        str(item.get("url"))
        for item in items
        if not _ours(item) and str(item.get("url", "")).split("?")[0].endswith("/" + CARD_FILENAME)
    ]


async def async_register_card(hass: HomeAssistant) -> str:
    """Serve the card and register it; returns the URL the frontend loads."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL_BASE, str(Path(__file__).parent / "www"), cache_headers=False)]
    )
    version = (await async_get_integration(hass, DOMAIN)).version
    url = f"{CARD_URL}?v={version}"

    resources = _storage_resources(hass)
    if resources is None:
        # YAML resource mode (or no lovelace): load the card with the frontend
        try:
            add_extra_js_url(hass, url)
        except KeyError:  # the frontend is not loaded: nobody to show a card to
            _LOGGER.debug("frontend not loaded, the card is served but not registered")
        return url

    await _loaded(resources)
    items = resources.async_items()
    ours = [item for item in items if _ours(item)]
    if not ours:
        await resources.async_create_item({"res_type": "module", "url": url})
    else:
        if ours[0].get("url") != url or ours[0].get("type") != "module":
            await resources.async_update_item(ours[0]["id"], {"res_type": "module", "url": url})
        for extra in ours[1:]:
            await resources.async_delete_item(extra["id"])
    for other in _foreign_copies(items):
        _LOGGER.warning(
            "The dashboard also loads %s, a separate copy of the Brother Scanner card. "
            "The card now ships with this integration: remove the old card "
            "(HACS plugin brother-scanner-card, or the resource under Settings > Dashboards > Resources)",
            other,
        )
    return url


async def async_unregister_card(hass: HomeAssistant) -> None:
    """Remove the card's dashboard resource (the integration is being removed)."""
    resources = _storage_resources(hass)
    if resources is None:
        return
    await _loaded(resources)
    for item in [item for item in resources.async_items() if _ours(item)]:
        await resources.async_delete_item(item["id"])
