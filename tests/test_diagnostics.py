"""Diagnostics download."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.components.diagnostics import get_diagnostics_for_config_entry

from .conftest import setup_entry


async def test_diagnostics(hass: HomeAssistant, config_entry, hass_client) -> None:
    hass.config_entries.async_update_entry(config_entry, data={**config_entry.data, "token": "secret"})
    await setup_entry(hass, config_entry)
    result = await get_diagnostics_for_config_entry(hass, hass_client, config_entry)
    assert result["entry"]["token"] == "**REDACTED**"
    assert result["state"] == "idle"
    assert result["actions"]["device"]["model"] == "MFC-L2700DW"
    assert result["jobs"][0]["job"] == "2026-10-10-10-00-00"
