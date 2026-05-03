# coding: utf-8
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_PORT, CONF_ALARM_CODE, CONF_ALARM_NAME, DEFAULT_PORT, DEFAULT_ALARM_NAME
from .panel import RSIPanel

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["alarm_control_panel", "binary_sensor", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    port       = entry.data.get(CONF_PORT, DEFAULT_PORT)
    alarm_name = entry.data.get(CONF_ALARM_NAME, DEFAULT_ALARM_NAME)

    shared = {
        "state":            "disarmed",
        "connected":        False,
        "serial":           None,
        "firmware":         None,
        "last_connection":  None,
        "connected_since":  None,
        "listeners":        [],
        "sensors": {
            "alarm_arm":                   "Unknown",
            "alarm_arm_source":            "Nothing",
            "alarm_power":                 "Unknown",
            "alarm_autoprotection":        "Unknown",
            "alarm_autoprotection_source": "Nothing",
            "alarm_alert":                 "Unknown",
            "alarm_alert_source":          "Nothing",
            "alarm_ping":                  "Nothing",
        }
    }
    hass.data[DOMAIN][entry.entry_id] = shared

    def on_state_change(new_state: str):
        shared["state"] = new_state
        _notify_listeners(hass, shared)

    def on_sensor_change(key: str, value: str):
        shared["sensors"][key] = value
        _notify_listeners(hass, shared)

    def on_connected(serial: str, firmware: str | None = None):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        shared["connected"]       = True
        shared["serial"]          = serial
        shared["firmware"]        = firmware or "Unknown"
        shared["last_connection"] = now
        shared["connected_since"] = now
        _LOGGER.info("RSI panel connected (serial=%s firmware=%s)", serial, firmware)
        _notify_listeners(hass, shared)

    def on_disconnected():
        shared["connected"]       = False
        shared["connected_since"] = None
        _LOGGER.info("RSI panel disconnected")
        _notify_listeners(hass, shared)

    panel = RSIPanel(
        host="",
        port=port,
        on_state_change=on_state_change,
        on_sensor_change=on_sensor_change,
        on_connected=on_connected,
        on_disconnected=on_disconnected,
    )
    shared["panel"] = panel

    await hass.async_add_executor_job(panel.start)
    _LOGGER.info("RSI Videofied: server started on port %s", port)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    shared = hass.data[DOMAIN].get(entry.entry_id, {})
    panel: RSIPanel = shared.get("panel")
    if panel:
        await hass.async_add_executor_job(panel.stop)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


def _notify_listeners(hass: HomeAssistant, shared: dict):
    for cb in shared.get("listeners", []):
        hass.loop.call_soon_threadsafe(cb)
