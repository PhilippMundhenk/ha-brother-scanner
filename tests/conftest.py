"""Fixtures: a fake BrotherScannerDocker container answering the REST API."""

from __future__ import annotations

from collections.abc import AsyncGenerator
import copy
import json
import re
from typing import Any
from unittest.mock import AsyncMock, patch

from aiohttp import web
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.brother_scanner.const import CONF_SCAN_INTERVAL, CONF_TOKEN, DOMAIN

ACTIONS = {
    "api_version": 1,
    "version": "test-1",
    "device": {
        "name": "Office scanner",
        "model": "MFC-L2700DW",
        "host": "192.0.2.10",
        "capabilities": {
            "mode": {"options": ["Black & White", "True Gray", "24bit Color[Fast]"], "default": "24bit Color[Fast]"},
            "resolution": {"options": [100, 200, 300, 600], "default": 200},
            "source": {"options": ["FlatBed", "Automatic Document Feeder(left aligned)"], "default": "FlatBed"},
        },
    },
    "actions": [
        {"target": "file", "label": "Archive", "enabled": True},
        {"target": "email", "label": "Rear pages", "enabled": True},
        {"target": "ocr", "label": "Scan to OCR", "enabled": True},
        {"target": "image", "label": "Scan to image", "enabled": False},
    ],
    "parameters": {"resolution": {"default": 300}, "mode": {"default": None}, "source": {"default": None}, "wait": {"default": False}},
    "authentication": "none",
}

STATUS_IDLE = {"scan": False, "waiting": False, "ocr": False, "reachable": True, "queue": {"pending": 0, "in_progress": 0, "failed": 0, "holding": False}}

JOB_DONE = {
    "job": "2026-10-10-10-00-00",
    "state": "done",
    "action": "file",
    "pages": 2,
    "file": "2026-10-10-10-00-00.pdf",
    "ocr_file": "2026-10-10-10-00-00-ocr.pdf",
    "ocr": "done",
    "file_url": "/api/file/2026-10-10-10-00-00.pdf/download",
}

FILE_NEWEST = {"file": "2026-10-10-10-00-00.pdf", "size": 1234, "fileModificationTime": 1760090400}

# GET /api/scanner/device (container 2.2+): what openskey reads from a real MFC-L2700DW
DEVICE_STATUS = {
    "device_ip": "192.0.2.10",
    "reachable": True,
    "registered": True,
    "model": "MFC-L2700DW",
    "serial": "E73941F6N621420",
    "firmware": "Y2309112149",
    "display": "Scan:   drück",
    "net_scanner_supported": True,
    "net_scanner_enabled": True,
    "scan_key_supported": True,
    "scan_key_enabled": True,
    "checked": "2026-10-22T19:00:00+00:00",
    "cached": False,
}

PDF = b"%PDF-1.4\n%fake\n%%EOF\n"


class FakeContainer:
    """In-memory state of the fake container plus the requests it saw."""

    def __init__(self) -> None:
        self.actions: dict[str, Any] = copy.deepcopy(ACTIONS)
        self.status: dict[str, Any] = copy.deepcopy(STATUS_IDLE)
        self.jobs: list[dict[str, Any]] = [copy.deepcopy(JOB_DONE)]
        self.files: list[dict[str, Any]] = [copy.deepcopy(FILE_NEWEST)]
        self.device_status: dict[str, Any] = copy.deepcopy(DEVICE_STATUS)
        self.device_status_404 = False  # an image before 2.2, or DEVICE_STATUS=false
        self.device_status_500 = False  # the endpoint exists but could not read the device
        self.token: str | None = None
        self.requests: list[tuple[str, str, dict[str, Any]]] = []
        self.fail_status = False
        self.not_found = False  # answer like a reverse proxy without a matching route
        self.html = False  # answer like a web server's start page (200, text/html)
        self.foreign_json = False  # answer like some other JSON API
        self.token_rejects_reads = False  # a container that wants the token on every request
        self.next_job = "2026-10-10-11-00-00"

    def _authorized(self, request: web.Request) -> bool:
        if not self.token:
            return True
        return request.headers.get("X-API-Token") == self.token or request.headers.get("Authorization") == f"Bearer {self.token}"

    async def handle(self, request: web.Request) -> web.Response:
        path = request.path
        body: dict[str, Any] = {}
        if request.method == "POST":
            body = dict(await request.post())
        self.requests.append((request.method, path, body))
        if self.fail_status:
            return web.Response(status=500, text="boom")
        if self.not_found:
            return web.Response(status=404, text="404 page not found\n")
        if self.html:
            return web.Response(status=200, text="<html><body>Welcome</body></html>", content_type="text/html")
        if self.foreign_json:
            return web.json_response({"status": "ok", "version": "3.1"})
        if self.token_rejects_reads and not self._authorized(request):
            return web.json_response({"code": 401, "message": "API token required"}, status=401)
        if path == "/api/actions":
            actions = copy.deepcopy(self.actions)
            if self.token:
                actions["authentication"] = "token required for triggers (Authorization: Bearer or X-API-Token)"
            return web.json_response(actions)
        if path == "/api/scanner/status":
            return web.json_response(self.status)
        if path == "/api/scanner/device":
            if self.device_status_404:
                return web.json_response({"code": 404, "message": "Device status is disabled (DEVICE_STATUS=false)"}, status=404)
            if self.device_status_500:
                return web.json_response({"code": 500, "message": "openskey status gave no answer"}, status=500)
            return web.json_response(self.device_status)
        if path == "/api/jobs":
            return web.json_response(self.jobs)
        if m := re.fullmatch(r"/api/jobs/([^/]+)/rear", path):
            if not self._authorized(request):
                return web.json_response({"code": 401, "message": "API token required"}, status=401)
            return web.json_response({"job": m.group(1), "state": "scanning_rear", "method": "return"})
        if m := re.fullmatch(r"/api/jobs/([^/]+)", path):
            for job in self.jobs:
                if job["job"] == m.group(1):
                    return web.json_response(job)
            return web.json_response({"code": 404, "message": "Unknown job"}, status=404)
        if path == "/api/file-list":
            limit = int(request.query.get("limit", "0") or 0)
            return web.json_response(self.files[:limit] if limit else self.files)
        if path == "/api/scanner/scanto":
            if not self._authorized(request):
                return web.json_response({"code": 401, "message": "API token required"}, status=401)
            if body.get("target") not in ("file", "email", "ocr", "image"):
                return web.json_response({"code": 400, "message": "Invalid target"}, status=400)
            return web.json_response({"job": self.next_job, "state": "queued", "method": "return", "target": body["target"]})
        if m := re.fullmatch(r"/api/file/([^/]+)/download", path):
            name = m.group(1)
            if any(f["file"] == name for f in self.files) or any(j.get("ocr_file") == name for j in self.jobs):
                return web.Response(body=PDF, content_type="application/pdf")
            return web.json_response({"code": 404, "message": "File does not exist"}, status=404)
        return web.json_response({"code": 404, "message": "Not Found"}, status=404)


@pytest.fixture
def container() -> FakeContainer:
    return FakeContainer()


@pytest.fixture
async def container_server(container: FakeContainer, aiohttp_server) -> AsyncGenerator[Any, None]:
    app = web.Application()
    app.router.add_route("*", "/{tail:.*}", container.handle)
    server = await aiohttp_server(app)
    yield server


@pytest.fixture
def entry_data(container_server) -> dict[str, Any]:
    return {"host": container_server.host, "port": container_server.port, CONF_TOKEN: "", "ssl": False}


@pytest.fixture
def config_entry(hass, entry_data) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, data=entry_data, options={CONF_SCAN_INTERVAL: 5}, title="Office scanner", unique_id=f"{entry_data['host']}:{entry_data['port']}")
    entry.add_to_hass(hass)
    return entry


@pytest.fixture(autouse=True)
def enable_custom_integrations(enable_custom_integrations):
    """pytest-homeassistant-custom-component: load custom_components from the repo."""
    return enable_custom_integrations


@pytest.fixture(autouse=True)
def _allow_local_sockets(socket_enabled):
    """The fake container is a real aiohttp server on localhost; pytest-socket blocks sockets by default."""
    return socket_enabled


async def setup_entry(hass, config_entry: MockConfigEntry) -> None:
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
