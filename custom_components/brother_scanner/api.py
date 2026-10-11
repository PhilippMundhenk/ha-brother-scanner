"""Client for the REST API of BrotherScannerDocker (doc/swagger.yaml in that repository)."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.parse import quote

import aiohttp


class ScannerApiError(Exception):
    """The container answered with an error or could not be reached."""


class ScannerCannotConnect(ScannerApiError):
    """The container did not answer at all."""


class ScannerAuthError(ScannerApiError):
    """The container wants an API token that is missing or wrong."""


class ScannerApi:
    """Thin async wrapper around the container's JSON endpoints."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int = 80,
        token: str | None = None,
        ssl: bool = False,
        timeout: float = 10,
    ) -> None:
        self._session = session
        self._token = token or ""
        scheme = "https" if ssl else "http"
        default_port = 443 if ssl else 80
        self.base_url = f"{scheme}://{host}" if int(port) == default_port else f"{scheme}://{host}:{port}"
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    @property
    def headers(self) -> dict[str, str]:
        """Headers for a request: the token when one is configured."""
        return {"X-API-Token": self._token} if self._token else {}

    async def _request(self, method: str, path: str, *, timeout: float | None = None, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        client_timeout = aiohttp.ClientTimeout(total=timeout) if timeout else self._timeout
        try:
            async with self._session.request(method, url, headers=self.headers, timeout=client_timeout, **kwargs) as res:
                if res.status == 401:
                    raise ScannerAuthError("API token required or wrong")
                if res.status >= 400:
                    message = await _error_message(res)
                    raise ScannerApiError(f"{method} {path}: {res.status} {message}")
                if res.content_type != "application/json":
                    # a reverse proxy's or web server's page instead of the API
                    raise ScannerApiError(
                        f"{method} {path}: {res.status} answered with {res.content_type or 'no content type'} instead of JSON "
                        "(is this the container's web interface?)"
                    )
                try:
                    return await res.json()
                except (json.JSONDecodeError, aiohttp.ContentTypeError) as err:
                    raise ScannerApiError(f"{method} {path}: {res.status} answered with invalid JSON ({err})") from err
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise ScannerCannotConnect(f"{self.base_url}: {err}") from err

    async def get_actions(self) -> dict[str, Any]:
        """Actions, parameters, version and device (name, model, capabilities)."""
        return await self._request("GET", "/api/actions")

    async def get_status(self) -> dict[str, Any]:
        """scan / waiting / ocr / reachable / queue."""
        return await self._request("GET", "/api/scanner/status")

    async def get_jobs(self, limit: int = 10) -> list[dict[str, Any]]:
        """Recent jobs, newest first."""
        return await self._request("GET", f"/api/jobs?limit={int(limit)}")

    async def get_job(self, job_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/jobs/{quote(job_id)}")

    async def get_newest_file(self) -> dict[str, Any] | None:
        """The newest PDF in the scan folder, or None when the folder is empty."""
        files = await self._request("GET", "/api/file-list?limit=1")
        return files[0] if isinstance(files, list) and files else None

    async def get_settings(self) -> dict[str, Any]:
        return await self._request("GET", "/api/settings")

    async def scan(
        self,
        target: str,
        *,
        resolution: int | None = None,
        mode: str | None = None,
        source: str | None = None,
        wait: bool = False,
    ) -> dict[str, Any]:
        """Start a scan; returns the container's answer with the job id."""
        form: dict[str, str] = {"target": target}
        if resolution:
            form["resolution"] = str(int(resolution))
        if mode:
            form["mode"] = mode
        if source:
            form["source"] = source
        if wait:
            form["wait"] = "true"
        # a waiting scan may take minutes (rear page wait + conversion)
        return await self._request("POST", "/api/scanner/scanto", data=form, timeout=900 if wait else None)

    async def scan_rear(self, job_id: str) -> dict[str, Any]:
        """Scan the rear pages of the job that waits for them."""
        return await self._request("POST", f"/api/jobs/{quote(job_id)}/rear")

    def download_url(self, file_name: str) -> str:
        """Direct download URL on the container (no token needed for reads)."""
        return f"{self.base_url}/api/file/{quote(file_name)}/download"

    async def download(self, file_name: str) -> bytes:
        """The PDF's bytes."""
        url = self.download_url(file_name)
        try:
            async with self._session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=120)) as res:
                if res.status == 401:
                    raise ScannerAuthError("API token required or wrong")
                if res.status == 404:
                    raise ScannerApiError(f"{file_name}: not found")
                if res.status >= 400:
                    raise ScannerApiError(f"download {file_name}: {res.status}")
                return await res.read()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise ScannerCannotConnect(f"{self.base_url}: {err}") from err

    async def open_download(self, file_name: str) -> aiohttp.ClientResponse:
        """A streaming response for the PDF; the caller releases it."""
        url = self.download_url(file_name)
        try:
            res = await self._session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=300))
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise ScannerCannotConnect(f"{self.base_url}: {err}") from err
        if res.status == 401:
            res.release()
            raise ScannerAuthError("API token required or wrong")
        if res.status >= 400:
            res.release()
            raise ScannerApiError(f"download {file_name}: {res.status}")
        return res


async def _error_message(res: aiohttp.ClientResponse) -> str:
    try:
        body = await res.json()
        if isinstance(body, dict):
            return str(body.get("message") or body.get("errors") or body)
    except Exception:  # noqa: BLE001 - any body shape is fine for a message
        pass
    return (await res.text())[:200]
