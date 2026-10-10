"""Config and options flow against the fake container."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.brother_scanner.const import CONF_HIDE_IMAGE, CONF_IMAGE_URL, CONF_SCAN_INTERVAL, CONF_TOKEN, DOMAIN

from .conftest import FakeContainer, setup_entry


async def test_user_flow_creates_entry(hass: HomeAssistant, entry_data, container: FakeContainer) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], entry_data)
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Office scanner"
    assert result["data"]["host"] == entry_data["host"]
    assert hass.config_entries.async_entries(DOMAIN)[0].unique_id == f"{entry_data['host']}:{entry_data['port']}"


async def test_user_flow_errors(hass: HomeAssistant, entry_data, container: FakeContainer) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    container.fail_status = True
    result = await hass.config_entries.flow.async_configure(result["flow_id"], entry_data)
    assert result["errors"] == {"base": "unknown"}
    container.fail_status = False

    container.actions["api_version"] = 99
    result = await hass.config_entries.flow.async_configure(result["flow_id"], entry_data)
    assert result["errors"] == {"base": "unsupported_api"}
    container.actions["api_version"] = 1

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {**entry_data, "port": 1})
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_wrong_token(hass: HomeAssistant, entry_data, container: FakeContainer) -> None:
    container.token = "right"
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {**entry_data, CONF_TOKEN: "wrong"})
    # the container only enforces the token on writes; read-only validation passes
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_duplicate_is_aborted(hass: HomeAssistant, entry_data, config_entry) -> None:
    await setup_entry(hass, config_entry)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], entry_data)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow(hass: HomeAssistant, config_entry) -> None:
    await setup_entry(hass, config_entry)
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 10, CONF_IMAGE_URL: "https://example.invalid/scanner.png", CONF_HIDE_IMAGE: False}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options[CONF_SCAN_INTERVAL] == 10
    state = hass.states.get("sensor.office_scanner_state")
    assert state.attributes["image_url"] == "https://example.invalid/scanner.png"


async def test_reauth_flow(hass: HomeAssistant, config_entry, container: FakeContainer) -> None:
    await setup_entry(hass, config_entry)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_REAUTH, "entry_id": config_entry.entry_id}, data=config_entry.data
    )
    assert result["step_id"] == "reauth_confirm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_TOKEN: "new-token"})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.data[CONF_TOKEN] == "new-token"
