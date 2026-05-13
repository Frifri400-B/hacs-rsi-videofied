# coding: utf-8

import logging
from datetime import datetime, timezone

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN, CONF_ALARM_NAME, DEFAULT_ALARM_NAME,
    ALARM_SENSORS, PANEL_SENSORS,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    shared = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for s in PANEL_SENSORS:
        entities.append(RSIPanelInfoSensor(entry, shared, s))

    for s in ALARM_SENSORS:
        if s["entity_type"] == "sensor":
            entities.append(RSIAlarmSensor(entry, shared, s))

    async_add_entities(entities)

class RSIBaseSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, shared: dict, definition: dict):
        self._entry      = entry
        self._shared     = shared
        self._definition = definition
        alarm_name = entry.data.get(CONF_ALARM_NAME, DEFAULT_ALARM_NAME)

        self._attr_unique_id   = f"{DOMAIN}_{entry.entry_id}_{definition['key']}"
        self._attr_name        = definition["name"]
        self._attr_icon        = definition.get("icon")
        self._attr_device_info = DeviceInfo(
            identifiers  = {(DOMAIN, entry.entry_id)},
            name         = alarm_name,
            manufacturer = "RSI Video Technologies",
            model        = "Videofied XT",
        )
        if definition.get("device_class"):
            self._attr_device_class = definition["device_class"]
        if definition.get("unit"):
            self._attr_native_unit_of_measurement = definition["unit"]

    async def async_added_to_hass(self) -> None:
        @callback
        def _on_update():
            self.async_write_ha_state()
        self._shared["listeners"].append(_on_update)
        self.async_on_remove(lambda: self._shared["listeners"].remove(_on_update))

class RSIPanelInfoSensor(RSIBaseSensor):
    
    @property
    def native_value(self):
        key = self._definition["key"]

        if key == "panel_serial":
            return self._shared.get("serial") or "Unknown"

        if key == "panel_firmware":
            return self._shared.get("firmware") or "Unknown"

        if key == "panel_last_connection":
            last = self._shared.get("last_connection")
            return last

        if key == "panel_uptime":
            since = self._shared.get("connected_since")
            if not since:
                return None
            delta = datetime.now(timezone.utc) - since
            return int(delta.total_seconds())

        return None

    @property
    def available(self) -> bool:
        key = self._definition["key"]
        if key == "panel_uptime":
            return self._shared.get("connected", False)
        return True

    @property
    def extra_state_attributes(self):
        if self._definition["key"] == "panel_uptime":
            since = self._shared.get("connected_since")
            if since:
                delta = datetime.now(timezone.utc) - since
                h, rem = divmod(int(delta.total_seconds()), 3600)
                m, s   = divmod(rem, 60)
                return {"formatted": f"{h}h {m}m {s}s"}
        return {}

class RSIAlarmSensor(RSIBaseSensor):
    
    @property
    def native_value(self):
        key = self._definition["key"]
        val = self._shared["sensors"].get(key, "Nothing")
        return val

    @property
    def icon(self):
        key = self._definition["key"]
        icons = {
            "alarm_last_test":         "mdi:clipboard-check-outline",
            "alarm_radio_loss_source": "mdi:radio-tower",
            "alarm_ping":              "mdi:lan-pending",
            "alarm_arm_source":        "mdi:account-key",
            "alarm_alert_source":      "mdi:alert-circle",
            "alarm_autoprotection_source": "mdi:shield-alert",
        }
        return icons.get(key, "mdi:information-outline")

    @property
    def available(self) -> bool:
        return True
