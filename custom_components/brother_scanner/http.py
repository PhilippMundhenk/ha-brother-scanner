"""Download proxy: /api/brother_scanner/<entry_id>/download/<file>.

The card and automations download through Home Assistant, so the browser
never needs to reach the container directly and the API token stays on the
server. The view needs a logged-in user (or a signed path, which the card
requests with auth/sign_path).
"""

from __future__ import annotations

from aiohttp import web

from homeassistant.components.http import HomeAssistantView

from .api import ScannerApiError, ScannerCannotConnect
from .const import DOMAIN, DOWNLOAD_URL_BASE


class ScannerDownloadView(HomeAssistantView):
    """Streams a PDF from the container."""

    url = DOWNLOAD_URL_BASE + "/{entry_id}/download/{file_name}"
    name = f"api:{DOMAIN}:download"
    requires_auth = True

    async def get(self, request: web.Request, entry_id: str, file_name: str) -> web.StreamResponse:
        hass = request.app["hass"]
        coordinator = hass.data.get(DOMAIN, {}).get(entry_id)
        if coordinator is None:
            return web.Response(status=404, text="unknown scanner")
        if "/" in file_name or file_name in ("", ".", "..") or not file_name.lower().endswith(".pdf"):
            return web.Response(status=400, text="invalid file name")
        try:
            upstream = await coordinator.api.open_download(file_name)
        except ScannerCannotConnect:
            return web.Response(status=502, text="scanner container not reachable")
        except ScannerApiError as err:
            return web.Response(status=404, text=str(err))
        response = web.StreamResponse(status=200)
        response.content_type = "application/pdf"
        response.headers["Content-Disposition"] = f'attachment; filename="{file_name}"'
        if upstream.content_length:
            response.content_length = upstream.content_length
        await response.prepare(request)
        try:
            async for chunk in upstream.content.iter_chunked(64 * 1024):
                await response.write(chunk)
        finally:
            upstream.release()
        await response.write_eof()
        return response
