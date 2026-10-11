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
    assert result["errors"] == {"base": "api_error"}
    assert "500" in result["description_placeholders"]["detail"]
    container.fail_status = False

    # an address that answers, but not with the API (a reverse proxy's 404 page)
    container.not_found = True
    result = await hass.config_entries.flow.async_configure(result["flow_id"], entry_data)
    assert result["errors"] == {"base": "api_error"}
    assert "404 page not found" in result["description_placeholders"]["detail"]
    container.not_found = False

    # a web server's page with status 200, and some other JSON API
    container.html = True
    result = await hass.config_entries.flow.async_configure(result["flow_id"], entry_data)
    assert result["errors"] == {"base": "api_error"}
    assert "text/html instead of JSON" in result["description_placeholders"]["detail"]
    container.html = False
    container.foreign_json = True
    result = await hass.config_entries.flow.async_configure(result["flow_id"], entry_data)
    assert result["errors"] == {"base": "api_error"}
    assert "no actions list" in result["description_placeholders"]["detail"]
    container.foreign_json = False
    container.actions["api_version"] = "banana"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], entry_data)
    assert result["errors"] == {"base": "api_error"}
    assert "api_version" in result["description_placeholders"]["detail"]
    container.actions["api_version"] = 1

    container.actions["api_version"] = 99
    result = await hass.config_entries.flow.async_configure(result["flow_id"], entry_data)
    assert result["errors"] == {"base": "unsupported_api"}
    container.actions["api_version"] = 1

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {**entry_data, "port": 1})
    assert result["errors"] == {"base": "cannot_connect"}
    assert result["description_placeholders"]["detail"]


async def test_user_flow_takes_a_url_and_defaults_the_port(hass: HomeAssistant, entry_data, container: FakeContainer) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    url = f"http://{entry_data['host']}:{entry_data['port']}/"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": url, "ssl": True})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["host"] == entry_data["host"]
    assert result["data"]["port"] == entry_data["port"]
    assert result["data"]["ssl"] is False, "the URL's scheme wins over the checkbox"


def test_normalize_input() -> None:
    from custom_components.brother_scanner.config_flow import normalize_input

    assert normalize_input({"host": "scanner.local"}) == {"host": "scanner.local", "port": 80, "ssl": False}
    assert normalize_input({"host": "scanner.local", "ssl": True}) == {"host": "scanner.local", "port": 443, "ssl": True}
    assert normalize_input({"host": " scanner.local ", "port": 8080, "ssl": True}) == {"host": "scanner.local", "port": 8080, "ssl": True}
    assert normalize_input({"host": "https://scanner.example.org", "port": 80}) == {"host": "scanner.example.org", "port": 80, "ssl": True}
    assert normalize_input({"host": "https://scanner.example.org/"}) == {"host": "scanner.example.org", "port": 443, "ssl": True}
    assert normalize_input({"host": "http://192.168.1.5:8080/some/path", "ssl": True}) == {"host": "192.168.1.5", "port": 8080, "ssl": False}
    assert normalize_input({"host": "ftp://x", "port": 0}) == {"host": "ftp://x", "port": 80, "ssl": False}


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


async def test_reauth_flow_reports_errors(hass: HomeAssistant, config_entry, container: FakeContainer) -> None:
    await setup_entry(hass, config_entry)
    config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()
    flow = next(f for f in hass.config_entries.flow.async_progress() if f["context"].get("source") == config_entries.SOURCE_REAUTH)

    container.fail_status = True
    result = await hass.config_entries.flow.async_configure(flow["flow_id"], {CONF_TOKEN: "x"})
    assert result["errors"] == {"base": "api_error"}
    assert "500" in result["description_placeholders"]["detail"]
    container.fail_status = False

    container.actions["api_version"] = 99
    result = await hass.config_entries.flow.async_configure(flow["flow_id"], {CONF_TOKEN: "x"})
    assert result["errors"] == {"base": "unsupported_api"}
    container.actions["api_version"] = 1

    result = await hass.config_entries.flow.async_configure(flow["flow_id"], {CONF_TOKEN: "x"})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
