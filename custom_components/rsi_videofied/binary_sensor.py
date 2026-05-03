# coding: utf-8
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_ALARM_NAME, DEFAULT_ALARM_NAME, ALARM_SENSORS, CONNECTIVITY_SENSOR

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    shared = hass.data[DOMAIN][entry.entry_id]
    entities = [RSIPanelConnectedSensor(entry, shared)]

    for s in ALARM_SENSORS:
        if s["entity_type"] == "binary_sensor":
            entities.append(RSIAlarmBinarySensor(entry, shared, s))

    async_add_entities(entities)


class RSIBaseBinarySensor(BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, shared: dict):
        self._entry  = entry
        self._shared = shared
        alarm_name = entry.data.get(CONF_ALARM_NAME, DEFAULT_ALARM_NAME)
        self._attr_device_info = DeviceInfo(
            identifiers  = {(DOMAIN, entry.entry_id)},
            name         = alarm_name,
            manufacturer = "RSI Video Technologies",
            model        = "Videofied XT",
        )

    async def async_added_to_hass(self) -> None:
        @callback
        def _on_update():
            self.async_write_ha_state()
        self._shared["listeners"].append(_on_update)
        self.async_on_remove(lambda: self._shared["listeners"].remove(_on_update))


class RSIPanelConnectedSensor(RSIBaseBinarySensor):

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_name         = "Panel Connected"

    def __init__(self, entry: ConfigEntry, shared: dict):
        super().__init__(entry, shared)
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_connected"

    @property
    def is_on(self) -> bool:
        return self._shared.get("connected", False)


class RSIAlarmBinarySensor(RSIBaseBinarySensor):

    def __init__(self, entry: ConfigEntry, shared: dict, definition: dict):
        super().__init__(entry, shared)
        self._definition       = definition
        self._attr_unique_id   = f"{DOMAIN}_{entry.entry_id}_{definition['key']}"
        self._attr_name        = definition["name"]
        if definition.get("device_class"):
            self._attr_device_class = definition["device_class"]

    @property
    def is_on(self) -> bool:
        val = self._shared["sensors"].get(self._definition["key"], "OFF")
        return str(val).upper() in ("ON", "TRUE", "1")

    @property
    def available(self) -> bool:
        return True
