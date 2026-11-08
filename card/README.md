# Brother Scanner Card (sources)

The dashboard card of the [Brother Scanner (Docker)](../README.md#dashboard-card) integration. It ships with the integration: the build writes the bundle to `custom_components/brother_scanner/www/brother-scanner-card.js`, which the integration serves and registers as a dashboard resource. Configuration and screenshots are in the [main README](../README.md#dashboard-card).

## Development

```sh
npm install
npm run lint         # tsc --noEmit
npm run build        # ../custom_components/brother_scanner/www/brother-scanner-card.js
npm test             # builds, then Playwright tests against a harness with a fake hass object
node test/ha-screenshot.mjs <ha url> <user> <password> <ha config dir> doc/card.png   # card screenshot from a real Home Assistant with the integration installed
```

The card's version is the integration's (`version` in `manifest.json`), put in at build time. Commit the rebuilt bundle with every change to `src/`; CI fails when it is not current.
