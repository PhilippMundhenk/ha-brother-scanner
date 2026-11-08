"""The dashboard card: served by the integration and registered as a resource."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.components.lovelace.resources import ResourceStorageCollection, ResourceYAMLCollection
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.brother_scanner.const import CARD_URL, DOMAIN

from .conftest import setup_entry

COMPONENT = Path(__file__).parent.parent / "custom_components" / "brother_scanner"
VERSION = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))["version"]
URL = f"{CARD_URL}?v={VERSION}"
OLD_PLUGIN = "/hacsfiles/brother-scanner-card/brother-scanner-card.js?hacstag=1"


class _NoLovelaceConfig:
    """The dashboard config a fresh ResourceStorageCollection imports from: none."""

    async def async_load(self, force: bool) -> dict[str, Any]:
        raise HomeAssistantError("no config")


@dataclass
class _LovelaceData:
    """hass.data["lovelace"] since Home Assistant 2025.2 (the fields used here)."""

    resource_mode: str
    resources: Any


def storage_resources(hass: HomeAssistant, *, as_dict: bool = False) -> ResourceStorageCollection:
    """Dashboard resources in storage mode, as the lovelace component keeps them."""
    resources = ResourceStorageCollection(hass, _NoLovelaceConfig())
    hass.data["lovelace"] = {"mode": "storage", "resources": resources} if as_dict else _LovelaceData("storage", resources)
    return resources


async def items(resources: ResourceStorageCollection) -> list[dict[str, Any]]:
    if not resources.loaded:
        await resources.async_load()
        resources.loaded = True
    return resources.async_items()


@pytest.mark.parametrize("as_dict", [False, True], ids=["dataclass", "dict before 2025.2"])
async def test_the_card_is_served_and_registered_once(hass: HomeAssistant, config_entry, hass_client, as_dict: bool) -> None:
    resources = storage_resources(hass, as_dict=as_dict)
    await setup_entry(hass, config_entry)

    assert [(i["type"], i["url"]) for i in await items(resources)] == [("module", URL)]

    client = await hass_client()
    response = await client.get(CARD_URL)
    assert response.status == 200
    body = await response.text()
    assert "brother-scanner-card" in body
    # the bundle carries the integration's version (card/rollup.config.mjs)
    assert f"BROTHER-SCANNER-CARD %c {VERSION} " in body


async def test_an_older_registration_is_updated_and_duplicates_removed(hass: HomeAssistant, config_entry, caplog) -> None:
    resources = storage_resources(hass)
    await items(resources)
    await resources.async_create_item({"res_type": "js", "url": f"{CARD_URL}?v=1.0.0"})
    await resources.async_create_item({"res_type": "module", "url": f"{CARD_URL}?v=1.1.0"})
    await resources.async_create_item({"res_type": "module", "url": OLD_PLUGIN})
    await resources.async_create_item({"res_type": "module", "url": "/local/other-card.js"})

    with caplog.at_level(logging.WARNING):
        await setup_entry(hass, config_entry)

    urls = sorted(i["url"] for i in await items(resources))
    assert urls == sorted([URL, OLD_PLUGIN, "/local/other-card.js"])
    assert [i["type"] for i in await items(resources) if i["url"] == URL] == ["module"]
    # the old standalone card is the user's to remove; they are told how
    assert "separate copy of the Brother Scanner card" in caplog.text
    assert OLD_PLUGIN in caplog.text
    assert "other-card" not in caplog.text


async def test_a_current_registration_is_left_alone(hass: HomeAssistant, config_entry) -> None:
    resources = storage_resources(hass)
    await items(resources)
    created = await resources.async_create_item({"res_type": "module", "url": URL})
    with patch.object(resources, "async_update_item") as update, patch.object(resources, "async_create_item") as create:
        await setup_entry(hass, config_entry)
    update.assert_not_called()
    create.assert_not_called()
    assert [i["id"] for i in await items(resources)] == [created["id"]]


async def test_yaml_resource_mode_loads_the_card_with_the_frontend(hass: HomeAssistant, config_entry) -> None:
    hass.data["lovelace"] = _LovelaceData("yaml", ResourceYAMLCollection([]))
    with patch("custom_components.brother_scanner.frontend.add_extra_js_url") as add:
        await setup_entry(hass, config_entry)
    add.assert_called_once_with(hass, URL)


async def test_without_lovelace_and_frontend_setup_still_succeeds(hass: HomeAssistant, config_entry) -> None:
    hass.data.pop("lovelace", None)
    with patch("custom_components.brother_scanner.frontend.add_extra_js_url", side_effect=KeyError("frontend")):
        await setup_entry(hass, config_entry)
    assert hass.states.get("sensor.office_scanner_state").state == "idle"


async def test_removing_the_last_entry_removes_the_resource(hass: HomeAssistant, config_entry, entry_data) -> None:
    resources = storage_resources(hass)
    second = MockConfigEntry(domain=DOMAIN, data=entry_data, title="Second scanner", unique_id="second")
    second.add_to_hass(hass)
    await setup_entry(hass, config_entry)  # sets up every entry of the domain
    assert second.state is ConfigEntryState.LOADED
    assert [i["url"] for i in await items(resources)] == [URL]

    # another container is still configured: the card stays
    await hass.config_entries.async_remove(second.entry_id)
    await hass.async_block_till_done()
    assert [i["url"] for i in await items(resources)] == [URL]

    await hass.config_entries.async_remove(config_entry.entry_id)
    await hass.async_block_till_done()
    assert await items(resources) == []


async def test_removing_without_storage_resources_is_harmless(hass: HomeAssistant, config_entry) -> None:
    with patch("custom_components.brother_scanner.frontend.add_extra_js_url"):
        await setup_entry(hass, config_entry)
    hass.data.pop("lovelace", None)
    await hass.config_entries.async_remove(config_entry.entry_id)
    await hass.async_block_till_done()
