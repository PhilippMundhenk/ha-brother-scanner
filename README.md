# Brother Scanner (Docker) for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/PhilippMundhenk/ha-brother-scanner/actions/workflows/validate.yml/badge.svg)](https://github.com/PhilippMundhenk/ha-brother-scanner/actions/workflows/validate.yml)

A Home Assistant integration for [BrotherScannerDocker](https://github.com/PhilippMundhenk/BrotherScannerDocker): the container that drives a network Brother scanner and turns scans into PDFs, with optional OCR. The integration talks to the container's REST API, so Home Assistant can start scans, show what the scanner is doing and hand out the finished PDFs.

A matching dashboard card lives in [brother-scanner-card](https://github.com/PhilippMundhenk/brother-scanner-card).

This is an independent, third-party project. It is not affiliated with or endorsed by Brother Industries, Ltd.; Brother is a trademark of Brother Industries, Ltd. and is used only to describe which devices the container works with. No Brother logo or artwork is included.

## What you get

One device per container, with these entities:

| Entity | Type | Content |
| --- | --- | --- |
| State | sensor (enum) | `idle`, `scanning`, `waiting_for_rear`, `converting`, `ocr`, `unreachable`. Attributes: current job, pages, waiting job, OCR queue, the actions with their labels, device capabilities, picture URL, web UI URL |
| Last scan | sensor | Name of the newest PDF. Attributes: size, time, download URL through Home Assistant, direct URL, OCR copy |
| OCR queue | sensor | Scans waiting for OCR; attributes: in progress, failed, holding |
| Last job, Last error, Container version | diagnostic sensors | State of the newest job, its error text, the image version |
| Scanning, Waiting for rear pages, OCR running, Scanner reachable, Problem | binary sensors | What the web UI shows with its icons |
| One button per scan action | button | Named like the container's buttons (`RENAME_GUI_*`), disabled actions (`DISABLE_GUI_*`) are created disabled |
| Scan rear pages | button | Only available while a scan waits for its rear pages |
| Resolution, Mode, Source | select (config) | Options from the device (`scanimage -A` at container start); `Container default` leaves the container's setting in charge |

Services (all return response data):

- `brother_scanner.scan` with `target` (`file`, `ocr`, `email`, `image`), optional `resolution`, `mode`, `source`, `wait`; returns the job id
- `brother_scanner.scan_rear` with optional `job`
- `brother_scanner.download_last_scan` with `path` (a file, or a directory with a trailing slash) and optional `ocr: true`; the path must be inside `allowlist_external_dirs`

Events on the bus, each with job id, state, file names and download URLs: `brother_scanner_scan_started`, `brother_scanner_waiting_for_rear`, `brother_scanner_scan_done`, `brother_scanner_scan_failed`, `brother_scanner_ocr_done`.

Downloads go through Home Assistant (`/api/brother_scanner/<entry>/download/<file>`), so the browser only needs to reach Home Assistant and the container's API token stays on the server.

## Requirements

- BrotherScannerDocker from October 2026 or newer (`GET /api/actions` answers with `api_version`), running with `WEBSERVER=true`
- Home Assistant 2024.8 or newer

## Installation

### HACS (custom repository, until the integration is in the default store)

1. HACS → Integrations → menu (three dots) → **Custom repositories**
2. Repository `https://github.com/PhilippMundhenk/ha-brother-scanner`, category **Integration**, Add
3. Search for "Brother Scanner (Docker)", Download, restart Home Assistant

### Manual

Copy `custom_components/brother_scanner` into your `config/custom_components/` folder and restart Home Assistant.

## Setup

Settings → Devices & services → Add integration → **Brother Scanner (Docker)**. Enter the host and port of the container's web interface. The API token is only needed when the container runs with `API_TOKEN`.

Options (gear icon on the integration): poll interval (default 5 s), a picture URL for the card, or hide the picture. Without a URL the card shows a generic illustration chosen by the model family (MFC/DCP, ADS, DS).

## Automations

Move every finished scan to a folder Paperless watches:

```yaml
alias: Scan to Paperless
triggers:
  - trigger: event
    event_type: brother_scanner_ocr_done
actions:
  - action: brother_scanner.download_last_scan
    data:
      path: /media/paperless/consume/
      ocr: true
```

Start a gray 300 dpi scan from a button on the wall and announce the result:

```yaml
actions:
  - action: brother_scanner.scan
    data:
      target: file
      resolution: 300
      mode: True Gray
    response_variable: scan
  - action: notify.mobile_app_phone
    data:
      message: "Scan {{ scan.job }} started"
```

## Without this integration

The container's API also works with Home Assistant's built-in `rest` sensor and `rest_command`; see the "Home Assistant" section of the [container README](https://github.com/PhilippMundhenk/BrotherScannerDocker#home-assistant). This integration adds the config flow, the dynamic buttons, the capabilities, events, the download proxy and the card.

## Publishing to the HACS default store

The repository is prepared for the default store. The remaining steps need the repository owner:

1. Publish a release `vX.Y.Z` whose tag matches `version` in `manifest.json` (the Release workflow checks this).
2. The Validate workflow must be green: hassfest, HACS validation and the tests.
3. Add the icon to [home-assistant/brands](https://github.com/home-assistant/brands): copy `brands/brother_scanner/` from this repository to `custom_integrations/brother_scanner/` in a fork and open a pull request. The icon is a generic multifunction printer drawing (`tools/make_icons.py`), not a Brother logo; there is no `logo.png`, so Home Assistant shows the icon in its place.
4. Open a pull request against [hacs/default](https://github.com/hacs/default) adding `PhilippMundhenk/ha-brother-scanner` to the `integration` file (one line, alphabetical order). The HACS bot checks the repository: description, topics (`home-assistant`, `hacs`, `brother`, `scanner`), a release, `hacs.json`, the manifest and the brands entry.
5. Until that is merged, users add the repository as a custom repository as described above.

## Development

```sh
pip install -r requirements_test.txt
pytest
```

The tests run a fake container (an aiohttp server speaking the container's API) and exercise the config flow, entities, services, events and the download view. For a test against the real thing, start the container's end-to-end image (`tests/e2e` in BrotherScannerDocker) and add it through the UI.

## License

MIT, like the container.
