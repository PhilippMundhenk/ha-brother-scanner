"""Constants for the Brother Scanner (Docker) integration."""

from __future__ import annotations

DOMAIN = "brother_scanner"
MANUFACTURER = "Brother"

CONF_TOKEN = "token"
CONF_SSL = "ssl"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_IMAGE_URL = "image_url"
CONF_HIDE_IMAGE = "hide_image"
# poll GET /api/scanner/device (the scanner's own state over SNMP; container 2.2+)
CONF_DEVICE_STATUS = "device_status"

DEFAULT_PORT = 80
DEFAULT_SSL_PORT = 443
DEFAULT_SCAN_INTERVAL = 5
MIN_SCAN_INTERVAL = 2
MAX_SCAN_INTERVAL = 300

# The container's API version this integration was written against
# (GET /api/actions -> api_version). A newer major version is refused by the
# config flow so the user gets a clear message instead of broken entities.
SUPPORTED_API_VERSION = 1

# Scanner states derived from /api/scanner/status and the newest job
STATE_IDLE = "idle"
STATE_SCANNING = "scanning"
STATE_WAITING_FOR_REAR = "waiting_for_rear"
STATE_CONVERTING = "converting"
STATE_OCR = "ocr"
STATE_UNREACHABLE = "unreachable"
SCANNER_STATES = [
    STATE_IDLE,
    STATE_SCANNING,
    STATE_WAITING_FOR_REAR,
    STATE_CONVERTING,
    STATE_OCR,
    STATE_UNREACHABLE,
]

JOB_STATES = [
    "queued",
    "scanning",
    "waiting_for_rear",
    "scanning_rear",
    "converting",
    "done",
    "failed",
    "unknown",
]

# Events fired on the HA bus when the newest job changes state
EVENT_SCAN_STARTED = f"{DOMAIN}_scan_started"
EVENT_SCAN_DONE = f"{DOMAIN}_scan_done"
EVENT_SCAN_FAILED = f"{DOMAIN}_scan_failed"
EVENT_OCR_DONE = f"{DOMAIN}_ocr_done"
EVENT_WAITING_FOR_REAR = f"{DOMAIN}_waiting_for_rear"
# a scan was started with a Scan-to-PC button on the device itself (job trigger "button");
# the payload carries "function" and, when the daemon reports them, "button" (seq, params)
EVENT_BUTTON_PRESSED = f"{DOMAIN}_button_pressed"

SERVICE_SCAN = "scan"
SERVICE_SCAN_REAR = "scan_rear"
SERVICE_DOWNLOAD_LAST_SCAN = "download_last_scan"

ATTR_TARGET = "target"
ATTR_RESOLUTION = "resolution"
ATTR_MODE = "mode"
ATTR_SOURCE = "source"
ATTR_WAIT = "wait"
ATTR_JOB = "job"
ATTR_PATH = "path"
ATTR_OCR = "ocr"

# Generic illustrations shipped with the integration, chosen by model prefix
IMAGE_FAMILIES = {
    "ADS": "ads.svg",
    "DS": "ds.svg",
    "MFC": "mfc.svg",
    "DCP": "mfc.svg",
}
IMAGE_GENERIC = "generic.svg"
STATIC_URL_BASE = f"/{DOMAIN}/static"
DOWNLOAD_URL_BASE = f"/api/{DOMAIN}"
