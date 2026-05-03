# coding: utf-8
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN, CONF_PORT, CONF_ALARM_CODE, CONF_ALARM_NAME,
    DEFAULT_PORT, DEFAULT_ALARM_NAME,
)


class RSIVideofiedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            code = str(user_input.get(CONF_ALARM_CODE, ""))
            if len(code) < 4 or not code.isdigit():
                errors[CONF_ALARM_CODE] = "invalid_code"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input.get(CONF_ALARM_NAME, DEFAULT_ALARM_NAME),
                    data=user_input,
                )

        schema = vol.Schema({
            vol.Optional(CONF_ALARM_NAME, default=DEFAULT_ALARM_NAME): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(int, vol.Range(min=1, max=65535)),
            vol.Required(CONF_ALARM_CODE): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return RSIVideofiedOptionsFlow(config_entry)


class RSIVideofiedOptionsFlow(config_entries.OptionsFlow):

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            code = str(user_input.get(CONF_ALARM_CODE, ""))
            if len(code) < 4 or not code.isdigit():
                errors[CONF_ALARM_CODE] = "invalid_code"
            else:
                return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.data
        schema = vol.Schema({
            vol.Optional(CONF_ALARM_NAME,  default=current.get(CONF_ALARM_NAME, DEFAULT_ALARM_NAME)): str,
            vol.Optional(CONF_PORT,        default=current.get(CONF_PORT, DEFAULT_PORT)): vol.All(int, vol.Range(min=1, max=65535)),
            vol.Required(CONF_ALARM_CODE,  default=current.get(CONF_ALARM_CODE, "")): str,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
