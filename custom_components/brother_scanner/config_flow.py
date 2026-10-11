"""Config flow: host (or URL), port, token; options: poll interval and image."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlsplit

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .api import ScannerApi, ScannerApiError, ScannerAuthError, ScannerCannotConnect
from .const import (
    CONF_HIDE_IMAGE,
    CONF_IMAGE_URL,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    CONF_TOKEN,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SSL_PORT,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    SUPPORTED_API_VERSION,
)

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        # empty: 80, or 443 with HTTPS (a form cannot switch the port when the HTTPS box is ticked)
        vol.Optional(CONF_PORT): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
        vol.Optional(CONF_TOKEN, default=""): str,
        vol.Optional(CONF_SSL, default=False): bool,
    }
)


def normalize_input(data: dict[str, Any]) -> dict[str, Any]:
    """Resolve host, port and HTTPS from what the user typed.

    The host field also takes a URL (https://scanner.example.org,
    http://192.168.1.5:8080): its scheme and port win over the form fields.
    Without a port, HTTPS means 443 and plain HTTP means 80.
    """
    host = str(data.get(CONF_HOST, "")).strip()
    port = data.get(CONF_PORT)
    ssl = bool(data.get(CONF_SSL, False))
    if "://" in host:
        parts = urlsplit(host)
        if parts.scheme in ("http", "https") and parts.hostname:
            ssl = parts.scheme == "https"
            host = parts.hostname
            if parts.port:
                port = parts.port
    host = host.rstrip("/")
    if not port:
        port = DEFAULT_SSL_PORT if ssl else DEFAULT_PORT
    return {**data, CONF_HOST: host, CONF_PORT: int(port), CONF_SSL: ssl}


async def validate_input(hass, data: dict[str, Any]) -> dict[str, Any]:
    """Talk to the container; returns the title and the device info."""
    api = ScannerApi(
        async_get_clientsession(hass),
        data[CONF_HOST],
        data.get(CONF_PORT, DEFAULT_PORT),
        token=data.get(CONF_TOKEN) or None,
        ssl=data.get(CONF_SSL, False),
    )
    actions = await api.get_actions()
    api_version = actions.get("api_version", 1)
    if int(api_version) > SUPPORTED_API_VERSION:
        raise UnsupportedApi(str(api_version))
    device = actions.get("device") or {}
    name = device.get("name") or data[CONF_HOST]
    # The container only enforces the token on writes; a wrong token would
    # otherwise show up as 401 on the first button press. Check it now.
    if data.get(CONF_TOKEN) and "token required" in str(actions.get("authentication", "")):
        await api.get_status()
    return {"title": name, "device": device}


class UnsupportedApi(Exception):
    """The container speaks a newer API than this integration."""


class BrotherScannerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the UI setup."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {
            "detail": "",
            # hassfest forbids URLs inside translation strings
            "example_https": "https://scanner.example.org",
            "example_http": "http://192.168.1.5:8080",
        }
        if user_input is not None:
            user_input = normalize_input(user_input)
            await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()
            try:
                info = await validate_input(self.hass, user_input)
            except ScannerAuthError:
                errors["base"] = "invalid_auth"
            except ScannerCannotConnect as err:
                errors["base"] = "cannot_connect"
                placeholders["detail"] = str(err)
            except UnsupportedApi:
                errors["base"] = "unsupported_api"
            except ScannerApiError as err:
                # the address answered, but not with the container's API (a reverse
                # proxy's 404, a web server's HTML page, ...): say what came back
                _LOGGER.warning("The scanner container's API did not answer as expected: %s", err)
                errors["base"] = "api_error"
                placeholders["detail"] = str(err)
            except Exception as err:  # noqa: BLE001
                _LOGGER.exception("Unexpected error talking to the scanner container")
                errors["base"] = "unknown"
                placeholders["detail"] = f"{type(err).__name__}: {err}"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
            errors=errors,
            description_placeholders=placeholders,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """The token was rejected: ask for a new one."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            data = {**entry.data, CONF_TOKEN: user_input[CONF_TOKEN]}
            try:
                await validate_input(self.hass, data)
            except ScannerAuthError:
                errors["base"] = "invalid_auth"
            except ScannerCannotConnect:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(entry, data=data)
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return BrotherScannerOptionsFlow()


class BrotherScannerOptionsFlow(OptionsFlow):
    """Poll interval, image URL, hide image."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                ),
                vol.Optional(CONF_IMAGE_URL, default=options.get(CONF_IMAGE_URL, "")): str,
                vol.Optional(CONF_HIDE_IMAGE, default=options.get(CONF_HIDE_IMAGE, False)): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
