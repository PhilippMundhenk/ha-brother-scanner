"""Polls the container and derives the scanner state, fires events on job changes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ScannerApi, ScannerApiError, ScannerAuthError, ScannerCannotConnect
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    DOWNLOAD_URL_BASE,
    EVENT_OCR_DONE,
    EVENT_SCAN_DONE,
    EVENT_SCAN_FAILED,
    EVENT_SCAN_STARTED,
    EVENT_WAITING_FOR_REAR,
    STATE_CONVERTING,
    STATE_IDLE,
    STATE_OCR,
    STATE_SCANNING,
    STATE_UNREACHABLE,
    STATE_WAITING_FOR_REAR,
)

_LOGGER = logging.getLogger(__name__)

ACTIONS_REFRESH = timedelta(minutes=10)
JOBS_LIMIT = 10


@dataclass
class ScannerData:
    """One poll of the container."""

    status: dict[str, Any] = field(default_factory=dict)
    jobs: list[dict[str, Any]] = field(default_factory=list)
    newest_file: dict[str, Any] | None = None
    actions: dict[str, Any] = field(default_factory=dict)

    @property
    def latest_job(self) -> dict[str, Any] | None:
        return self.jobs[0] if self.jobs else None

    @property
    def waiting_job(self) -> dict[str, Any] | None:
        """The newest job that waits for rear pages, if any."""
        for job in self.jobs:
            if job.get("state") == "waiting_for_rear":
                return job
        return None

    @property
    def reachable(self) -> bool | None:
        return self.status.get("reachable")

    @property
    def queue(self) -> dict[str, Any]:
        return self.status.get("queue") or {}

    @property
    def device(self) -> dict[str, Any]:
        return self.actions.get("device") or {}

    @property
    def capabilities(self) -> dict[str, Any]:
        return self.device.get("capabilities") or {}

    @property
    def enabled_actions(self) -> list[dict[str, Any]]:
        return [a for a in self.actions.get("actions", []) if a.get("enabled")]

    @property
    def state(self) -> str:
        """idle / scanning / waiting_for_rear / converting / ocr / unreachable."""
        status = self.status
        latest = self.latest_job or {}
        if status.get("waiting") or latest.get("state") == "waiting_for_rear":
            return STATE_WAITING_FOR_REAR
        if status.get("scan") or latest.get("state") in ("queued", "scanning", "scanning_rear"):
            return STATE_SCANNING
        if latest.get("state") == "converting":
            return STATE_CONVERTING
        if status.get("ocr") or self.queue.get("in_progress"):
            return STATE_OCR
        if status.get("reachable") is False:
            return STATE_UNREACHABLE
        return STATE_IDLE


class ScannerCoordinator(DataUpdateCoordinator[ScannerData]):
    """Fetches status, jobs and the newest file every few seconds; actions every ten minutes."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: ScannerApi) -> None:
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {entry.title}",
            update_interval=timedelta(seconds=interval),
            config_entry=entry,
        )
        self.api = api
        self.entry = entry
        self._actions: dict[str, Any] = {}
        self._actions_age: timedelta | None = None
        self._actions_polls = 0
        self._last_job: dict[str, Any] | None = None
        # values chosen through the select entities, used by the buttons
        self.selected: dict[str, Any] = {"resolution": None, "mode": None, "source": None}

    @property
    def device_name(self) -> str:
        return self.data.device.get("name") or self.entry.title if self.data else self.entry.title

    def proxy_download_url(self, file_name: str) -> str:
        """Download through Home Assistant (authenticated, token stays server side)."""
        from urllib.parse import quote

        return f"{DOWNLOAD_URL_BASE}/{self.entry.entry_id}/download/{quote(file_name)}"

    async def _async_update_data(self) -> ScannerData:
        try:
            if not self._actions or self._actions_polls <= 0:
                self._actions = await self.api.get_actions()
                interval = self.update_interval.total_seconds() if self.update_interval else DEFAULT_SCAN_INTERVAL
                self._actions_polls = max(1, int(ACTIONS_REFRESH.total_seconds() / interval))
            self._actions_polls -= 1
            status = await self.api.get_status()
            jobs = await self.api.get_jobs(JOBS_LIMIT)
            newest = await self.api.get_newest_file()
        except ScannerAuthError as err:
            raise UpdateFailed(f"API token rejected: {err}") from err
        except ScannerCannotConnect as err:
            raise UpdateFailed(f"Container not reachable: {err}") from err
        except ScannerApiError as err:
            raise UpdateFailed(str(err)) from err

        data = ScannerData(status=status, jobs=jobs if isinstance(jobs, list) else [], newest_file=newest, actions=self._actions)
        self._fire_events(data)
        return data

    def _fire_events(self, data: ScannerData) -> None:
        """Compare the newest job with the last poll and fire bus events for changes."""
        latest = data.latest_job
        previous = self._last_job
        self._last_job = dict(latest) if latest else None
        if latest is None:
            return
        if previous is None:
            # first poll after setup: remember without announcing old jobs
            return
        payload = self._event_payload(latest)
        if latest.get("job") != previous.get("job"):
            self._fire(EVENT_SCAN_STARTED, payload)
            previous = {}
        state, old_state = latest.get("state"), previous.get("state")
        if state != old_state:
            if state == "waiting_for_rear":
                self._fire(EVENT_WAITING_FOR_REAR, payload)
            elif state == "done":
                self._fire(EVENT_SCAN_DONE, payload)
            elif state == "failed":
                self._fire(EVENT_SCAN_FAILED, payload)
        if latest.get("ocr") == "done" and previous.get("ocr") != "done":
            self._fire(EVENT_OCR_DONE, payload)

    def _event_payload(self, job: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "entry_id": self.entry.entry_id,
            "device": self.device_name,
            "job": job.get("job"),
            "state": job.get("state"),
            "action": job.get("action"),
            "pages": job.get("pages"),
            "file": job.get("file"),
            "ocr_file": job.get("ocr_file"),
            "error": job.get("error"),
        }
        if job.get("file"):
            payload["download_url"] = self.proxy_download_url(job["file"])
        if job.get("ocr_file") and job.get("ocr") == "done":
            payload["ocr_download_url"] = self.proxy_download_url(job["ocr_file"])
        return payload

    def _fire(self, event: str, payload: dict[str, Any]) -> None:
        _LOGGER.debug("%s: %s", event, payload)
        self.hass.bus.async_fire(event, payload)
