# Brother Scanner Card

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Build](https://github.com/PhilippMundhenk/brother-scanner-card/actions/workflows/build.yml/badge.svg)](https://github.com/PhilippMundhenk/brother-scanner-card/actions/workflows/build.yml)

A dashboard card for the [Brother Scanner (Docker)](https://github.com/PhilippMundhenk/ha-brother-scanner) Home Assistant integration, which drives a [BrotherScannerDocker](https://github.com/PhilippMundhenk/BrotherScannerDocker) container.

This is an independent, third-party project, not affiliated with or endorsed by Brother Industries, Ltd.; Brother is a trademark of Brother Industries, Ltd. and is used only to describe which devices the container works with. The card contains no Brother logo or artwork; the device picture is a generic drawing provided by the integration.

The card shows the scanner (a picture, the name and the state with the same icons as the container's web UI), the scan buttons with the labels configured in the container, a highlighted button while a scan waits for its rear pages (with the countdown), the OCR queue, the last scan with download buttons for the PDF and its OCR copy, and a link to the web UI. With container 2.2 or newer it also shows what the scanner itself reports: whether it currently lists the container as a Scan-to-PC destination (so the buttons on the device work), its panel display line, and on request serial number and firmware; every one of these can be switched off.

![The card in a Home Assistant dashboard](doc/card.png)

## Installation

### HACS (custom repository, until the card is in the default store)

[![Open your Home Assistant instance and open this repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=PhilippMundhenk&repository=brother-scanner-card&category=plugin)

The badge opens the repository in your HACS; by hand:

1. HACS → Frontend → menu (three dots) → **Custom repositories**
2. Repository `https://github.com/PhilippMundhenk/brother-scanner-card`, category **Dashboard** (called *Lovelace* or *Plugin* in older HACS versions), Add
3. Search for "Brother Scanner Card", Download. HACS registers the resource; reload the browser.

HACS can only register the resource when dashboard resources are managed in storage mode (the default). With `lovelace: resource_mode: yaml` you add it yourself, and you must change the URL with every update, otherwise the browser keeps the old file: `/local/community/brother-scanner-card/brother-scanner-card.js?v=1.0.1`. Removing `resource_mode: yaml` and the `resources:` list, then redownloading the card in HACS, lets HACS handle it from then on.

### Manual

Copy `dist/brother-scanner-card.js` to `config/www/brother-scanner-card.js` and add a dashboard resource `/local/brother-scanner-card.js` of type *JavaScript module* (Settings → Dashboards → menu → Resources).

## Configuration

The visual editor (Edit dashboard → Add card → Brother Scanner Card) covers every option. In YAML:

```yaml
type: custom:brother-scanner-card
entity: sensor.office_scanner_state   # the integration's "State" sensor
name: Office scanner                  # optional, default: the device name
show_image: true                      # picture from the integration (generic by model, or the configured URL)
image: /local/my-scanner.png          # optional, overrides the picture
show_buttons: true
buttons: [file, ocr]                  # optional: only these actions (file, ocr, email, image)
show_selects: false                   # resolution / mode / source dropdowns
show_last_scan: true
show_link: true                       # link to the container's web UI
compact: false
show_device: true                     # the scanner's own state (container 2.2+); each value below can be switched off
show_registered: true                 #   "Scan-to-PC registered" (the scanner lists the container; red when it does not)
show_display: true                    #   the scanner's panel display line
show_serial: false                    #   serial number
show_firmware: false                  #   firmware version
show_scan_key: true                   #   warn when the device has its network scan key switched off
```

The card finds the other entities of the scanner (buttons, selects, last scan) through the device of the state sensor, so only the state sensor needs to be configured. Disabled actions (`DISABLE_GUI_*` in the container) do not get a button; renamed actions (`RENAME_GUI_*`) show their label.

Downloads go through Home Assistant's authenticated download endpoint of the integration (the card asks for a signed URL first), so they work from outside the local network as well and the container's API token never reaches the browser.

## Development

```sh
npm install
npm run build        # dist/brother-scanner-card.js
npm test             # builds, then Playwright tests against a harness with a fake hass object
node test/ha-screenshot.mjs <ha url> <user> <password> <ha config dir> doc/card.png   # card screenshot from a real Home Assistant
```

A release tag `vX.Y.Z` must match `version` in `package.json` and the `CARD_VERSION` constant; the Build workflow checks it and attaches `brother-scanner-card.js` to the release.

## License

MIT
