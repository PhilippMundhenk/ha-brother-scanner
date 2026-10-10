"""Diagnostics download: the last poll, without the token."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import ScannerConfigEntry
from .const import CONF_TOKEN

TO_REDACT = {CONF_TOKEN}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ScannerConfigEntry) -> dict[str, Any]:
    coordinator = entry.runtime_data
    data = coordinator.data
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "state": data.state if data else None,
        "status": data.status if data else None,
        "jobs": data.jobs if data else None,
        "newest_file": data.newest_file if data else None,
        "actions": data.actions if data else None,
        "selected": coordinator.selected,
    }
