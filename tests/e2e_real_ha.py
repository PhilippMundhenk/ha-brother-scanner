"""End-to-end check against a real Home Assistant container and a real scanner container.

Not part of the pytest suite (needs Docker). Run from the repository root:

    python tests/e2e_real_ha.py --scanner-image brotherscanner:e2e --scanimage tests/fixtures/scanimage

What it does:
  1. starts the scanner container (simulated scanimage) and a Home Assistant
     container with this integration mounted into custom_components
  2. onboards Home Assistant through its API (user, token)
  3. adds the integration through the config flow API
  4. checks the entities, presses the scan button, waits for the job, downloads
     the PDF through the integration's proxy view, and tears everything down
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def docker(*args: str, check: bool = True) -> str:
    res = subprocess.run(["docker", *args], capture_output=True, text=True, env={**os.environ, "MSYS_NO_PATHCONV": "1"})
    if check and res.returncode != 0:
        raise RuntimeError(f"docker {' '.join(args)} failed: {res.stderr}")
    return res.stdout.strip()


def request(url: str, method: str = "GET", data: dict | None = None, token: str | None = None, raw: bool = False):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as res:
        payload = res.read()
        return payload if raw else (json.loads(payload) if payload else None)


def wait_for(fn, timeout: float, what: str):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            value = fn()
            if value:
                return value
        except Exception as err:  # noqa: BLE001
            last = err
        time.sleep(2)
    raise TimeoutError(f"timeout waiting for {what}: {last}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scanner-image", default="brotherscanner:e2e")
    parser.add_argument("--ha-image", default="ghcr.io/home-assistant/home-assistant:stable")
    parser.add_argument("--scanimage", required=True, help="path to the scanimage simulator (BrotherScannerDocker tests/e2e/fixtures/scanimage)")
    parser.add_argument("--ha-port", type=int, default=18123)
    parser.add_argument("--scanner-port", type=int, default=18180)
    parser.add_argument("--keep", action="store_true", help="leave the containers running (for a look at the UI / screenshots)")
    args = parser.parse_args()

    tag = str(os.getpid())
    scanner_name, ha_name = f"ha-e2e-scanner-{tag}", f"ha-e2e-home-assistant-{tag}"
    config_dir = ROOT / "tests" / "output" / f"ha-config-{tag}"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "configuration.yaml").write_text("default_config:\nlogger:\n  default: warning\n  logs:\n    custom_components.brother_scanner: debug\n")
    ok = False
    try:
        docker("run", "-d", "--name", scanner_name, "-p", f"{args.scanner_port}:8080",
               "-v", f"{Path(args.scanimage).resolve()}:/usr/bin/scanimage:ro",
               "-e", "WEBSERVER=true", "-e", "PORT=8080", "-e", "IPADDRESS=192.0.2.10", "-e", "KEEPALIVE=false",
               "-e", "SCANNER_PING_INTERVAL=0", "-e", "RESOLUTION=100", "-e", "REAR_PAGE_WAIT_SECONDS=3",
               "-e", "NAME=Office", "-e", "MODEL=MFC-SIMULATOR", "-e", "RENAME_GUI_SCANTOFILE=Archive",
               "-e", "API_TOKEN=e2e-token", "-e", "SIM_PAGES=1", "-e", "SIM_SCAN_SECONDS=0.5",
               args.scanner_image)
        docker("run", "-d", "--name", ha_name, "-p", f"{args.ha_port}:8123",
               "-v", f"{config_dir}:/config",
               "-v", f"{ROOT / 'custom_components'}:/config/custom_components:ro",
               "-e", "TZ=UTC", args.ha_image)
        ha = f"http://localhost:{args.ha_port}"
        scanner = f"http://localhost:{args.scanner_port}"
        wait_for(lambda: request(f"{scanner}/api/scanner/status"), 120, "scanner container")
        print("scanner container up")
        wait_for(lambda: request(f"{ha}/api/onboarding"), 300, "home assistant")
        print("home assistant up")

        # onboarding: user -> auth code -> token
        user = request(f"{ha}/api/onboarding/users", "POST", {"client_id": ha, "name": "e2e", "username": "e2e", "password": "e2e-password", "language": "en"})
        token_res = urllib.request.urlopen(urllib.request.Request(
            f"{ha}/auth/token", data=f"grant_type=authorization_code&code={user['auth_code']}&client_id={ha}".encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=60)
        token = json.loads(token_res.read())["access_token"]
        for step in ("core_config", "analytics", "integration"):
            try:
                request(f"{ha}/api/onboarding/{step}", "POST", {"client_id": ha, "redirect_uri": f"{ha}/"} if step == "integration" else {}, token)
            except urllib.error.HTTPError as err:
                print(f"onboarding {step}: {err.code} (ignored)")
        print("onboarded")

        # config flow through the API
        flow = request(f"{ha}/api/config/config_entries/flow", "POST", {"handler": "brother_scanner"}, token)
        assert flow["type"] == "form", flow
        result = request(f"{ha}/api/config/config_entries/flow/{flow['flow_id']}", "POST",
                         {"host": "host.docker.internal", "port": args.scanner_port, "token": "e2e-token", "ssl": False}, token)
        assert result["type"] == "create_entry", result
        entry_id = result["result"]["entry_id"]
        print(f"config entry created: {result['title']} ({entry_id})")

        states = {s["entity_id"]: s for s in request(f"{ha}/api/states", token=token)}
        state = states["sensor.office_state"]
        assert state["state"] == "idle", state
        assert state["attributes"]["model"] == "MFC-SIMULATOR"
        assert [a["label"] for a in state["attributes"]["actions"]][0] == "Archive"
        assert state["attributes"]["capabilities"]["resolution"]["options"] == [100, 150, 200, 300, 400, 600]
        assert "button.office_archive" in states, sorted(k for k in states if k.startswith("button."))
        assert states["button.office_scan_rear_pages"]["state"] == "unavailable"
        print("entities ok:", ", ".join(sorted(k for k in states if "office" in k)))

        # press the button, wait for the job, download through HA
        request(f"{ha}/api/services/select/select_option", "POST", {"entity_id": "select.office_resolution", "option": "100"}, token)
        request(f"{ha}/api/services/button/press", "POST", {"entity_id": "button.office_archive"}, token)

        def finished():
            s = request(f"{ha}/api/states/sensor.office_last_job", token=token)
            return s["state"] == "done" and s

        job = wait_for(finished, 120, "job to finish")
        print("job done:", job["attributes"]["file"], "params", job["attributes"].get("params"))
        last = wait_for(lambda: (lambda s: s if s["state"] == job["attributes"]["file"] else None)(request(f"{ha}/api/states/sensor.office_last_scan", token=token)), 60, "last scan sensor")
        pdf = request(f"{ha}{last['attributes']['download_url']}", token=token, raw=True)
        assert pdf.startswith(b"%PDF"), pdf[:20]
        print(f"downloaded {len(pdf)} bytes through Home Assistant")

        # the service with response data
        res = request(f"{ha}/api/services/brother_scanner/scan?return_response", "POST", {"target": "file", "resolution": 100}, token)
        assert res["service_response"]["job"], res
        print("service response:", res["service_response"])
        wait_for(lambda: request(f"{ha}/api/states/sensor.office_state", token=token)["state"] == "idle", 120, "idle again")
        ok = True
        print("ALL OK")
        if args.keep:
            print(f"containers kept: {ha} (user e2e / e2e-password), scanner {scanner}")
            return 0
    finally:
        if not (ok and args.keep):
            if not ok:
                print(docker("logs", "--tail", "60", ha_name, check=False), file=sys.stderr)
            docker("rm", "-f", scanner_name, ha_name, check=False)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
