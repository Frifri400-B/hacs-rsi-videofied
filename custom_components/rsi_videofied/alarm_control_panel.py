# coding: utf-8
import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    CodeFormat,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_ALARM_CODE, CONF_ALARM_NAME, DEFAULT_ALARM_NAME,
    STATE_DISARMED, STATE_ARMING, STATE_ARMED_AWAY,
    STATE_ARMED_HOME, STATE_ARMED_NIGHT, STATE_TRIGGERED,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    shared = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RSIAlarmPanel(hass, entry, shared)])


class RSIAlarmPanel(AlarmControlPanelEntity):

    _attr_has_entity_name = True
    _attr_name            = None

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, shared: dict):
        self._hass   = hass
        self._entry  = entry
        self._shared = shared
        self._panel  = shared["panel"]

        alarm_name = entry.data.get(CONF_ALARM_NAME, DEFAULT_ALARM_NAME)

        self._attr_unique_id  = f"{DOMAIN}_{entry.entry_id}_alarm"
        self._attr_code_format = CodeFormat.NUMBER
        self._attr_supported_features = (
            AlarmControlPanelEntityFeature.ARM_AWAY |
            AlarmControlPanelEntityFeature.ARM_HOME |
            AlarmControlPanelEntityFeature.ARM_NIGHT
        )
        self._attr_device_info = DeviceInfo(
            identifiers  = {(DOMAIN, entry.entry_id)},
            name         = alarm_name,
            manufacturer = "RSI Video Technologies",
            model        = "Videofied XT",
            sw_version   = "2.0",
        )


    async def async_added_to_hass(self) -> None:
        @callback
        def _on_update():
            self.async_write_ha_state()

        self._shared["listeners"].append(_on_update)
        self.async_on_remove(lambda: self._shared["listeners"].remove(_on_update))


    @property
    def state(self) -> str:
        return self._shared.get("state", STATE_DISARMED)

    @property
    def available(self) -> bool:
        return True

    @property
    def extra_state_attributes(self):
        return {
            "panel_connected": self._shared.get("connected", False),
            "panel_serial":    self._shared.get("serial"),
        }


    async def async_alarm_disarm(self, code: str | None = None) -> None:
        if not self._check_code(code):
            _LOGGER.warning("RSI: disarm rejected — wrong code")
            return
        self._shared["state"] = STATE_DISARMED
        self.async_write_ha_state()
        await self._hass.async_add_executor_job(self._panel.disarm)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        if not self._check_code(code):
            _LOGGER.warning("RSI: arm_away rejected — wrong code")
            return
        self._shared["state"] = STATE_ARMING
        self.async_write_ha_state()
        await self._hass.async_add_executor_job(self._panel.arm)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        if not self._check_code(code):
            _LOGGER.warning("RSI: arm_home rejected — wrong code")
            return
        self._shared["state"] = STATE_ARMING
        self.async_write_ha_state()
        await self._hass.async_add_executor_job(self._panel.arm)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        if not self._check_code(code):
            _LOGGER.warning("RSI: arm_night rejected — wrong code")
            return
        self._shared["state"] = STATE_ARMING
        self.async_write_ha_state()
        await self._hass.async_add_executor_job(self._panel.arm)


    def _check_code(self, code: str | None) -> bool:
        expected = self._entry.data.get(CONF_ALARM_CODE)
        if not expected:
            return True
        return str(code) == str(expected)
