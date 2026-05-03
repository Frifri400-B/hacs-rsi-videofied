# coding: utf-8
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_PORT, CONF_ALARM_CODE, CONF_ALARM_NAME, DEFAULT_PORT, DEFAULT_ALARM_NAME
from .panel import RSIPanel

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["alarm_control_panel", "binary_sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    port       = entry.data.get(CONF_PORT, DEFAULT_PORT)
    alarm_name = entry.data.get(CONF_ALARM_NAME, DEFAULT_ALARM_NAME)

    shared = {
        "state":        "disarmed",
        "connected":    False,
        "serial":       None,
        "listeners":    [],
    }
    hass.data[DOMAIN][entry.entry_id] = shared

    def on_state_change(new_state: str):
        shared["state"] = new_state
        _notify_listeners(hass, shared)

    def on_connected(serial: str):
        shared["connected"] = True
        shared["serial"]    = serial
        _LOGGER.info("RSI panel connected (serial=%s)", serial)
        _notify_listeners(hass, shared)

    def on_disconnected():
        shared["connected"] = False
        _LOGGER.info("RSI panel disconnected")
        _notify_listeners(hass, shared)

    panel = RSIPanel(
        host="",
        port=port,
        on_state_change=on_state_change,
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
