# coding: utf-8
import json
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN, CONF_PORT, CONF_ALARM_CODE, CONF_ALARM_NAME, CONF_USER_CODES,
    DEFAULT_PORT, DEFAULT_ALARM_NAME,
)

CONF_USERS   = "mapping_users"
CONF_DEVICES = "device_index"


def _validate_code(code):
    return len(str(code)) >= 4 and str(code).isdigit()


class RSIVideofiedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._data = {}

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            if not _validate_code(user_input.get(CONF_ALARM_CODE, "")):
                errors[CONF_ALARM_CODE] = "invalid_code"
            else:
                self._data.update(user_input)
                return await self.async_step_user_codes()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional(CONF_ALARM_NAME, default=DEFAULT_ALARM_NAME): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(int, vol.Range(min=1, max=65535)),
                vol.Required(CONF_ALARM_CODE): str,
            }),
            errors=errors,
            last_step=False,
        )

    async def async_step_user_codes(self, user_input=None):
        if user_input is not None:
            user_codes = {}
            for i in range(1, 11):
                code = str(user_input.get(f"ucode_{i}_code", "")).strip()
                name = str(user_input.get(f"ucode_{i}_name", "")).strip()
                if code and name:
                    if not _validate_code(code):
                        return self.async_show_form(
                            step_id="user_codes",
                            data_schema=self._user_codes_schema(user_input),
                            errors={f"ucode_{i}_code": "invalid_code"},
                            description_placeholders={"hint": "Each code must be at least 4 digits."},
                            last_step=False,
                        )
                    user_codes[code] = name
            self._data[CONF_USER_CODES] = user_codes
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self._data.get(CONF_ALARM_NAME, DEFAULT_ALARM_NAME),
                data=self._data,
            )

        return self.async_show_form(
            step_id="user_codes",
            data_schema=self._user_codes_schema(),
            description_placeholders={"hint": "Associate a PIN code to a user name. Leave empty to skip."},
            last_step=True,
        )

    def _user_codes_schema(self, prefill=None):
        prefill = prefill or {}
        fields = {}
        for i in range(1, 11):
            fields[vol.Optional(f"ucode_{i}_code", default=prefill.get(f"ucode_{i}_code", ""))] = str
            fields[vol.Optional(f"ucode_{i}_name", default=prefill.get(f"ucode_{i}_name", ""))] = str
        return vol.Schema(fields)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return RSIVideofiedOptionsFlow(config_entry)


class RSIVideofiedOptionsFlow(config_entries.OptionsFlow):

    def __init__(self, config_entry):
        self._entry   = config_entry
        self._options = dict(config_entry.options or {})
        self._data    = dict(config_entry.data or {})

    def _get(self, key, default=None):
        return self._options.get(key, self._data.get(key, default))

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            if not _validate_code(user_input.get(CONF_ALARM_CODE, "")):
                errors[CONF_ALARM_CODE] = "invalid_code"
            else:
                self._options.update(user_input)
                return await self.async_step_user_codes()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_ALARM_NAME, default=self._get(CONF_ALARM_NAME, DEFAULT_ALARM_NAME)): str,
                vol.Optional(CONF_PORT,       default=self._get(CONF_PORT, DEFAULT_PORT)): vol.All(int, vol.Range(min=1, max=65535)),
                vol.Required(CONF_ALARM_CODE, default=self._get(CONF_ALARM_CODE, "")): str,
            }),
            errors=errors,
            last_step=False,
        )

    async def async_step_user_codes(self, user_input=None):
        if user_input is not None:
            user_codes = {}
            for i in range(1, 11):
                code = str(user_input.get(f"ucode_{i}_code", "")).strip()
                name = str(user_input.get(f"ucode_{i}_name", "")).strip()
                if code and name:
                    if not _validate_code(code):
                        return self.async_show_form(
                            step_id="user_codes",
                            data_schema=self._user_codes_schema(user_input),
                            errors={f"ucode_{i}_code": "invalid_code"},
                            last_step=False,
                        )
                    user_codes[code] = name
            self._options[CONF_USER_CODES] = user_codes
            return await self.async_step_users()

        return self.async_show_form(
            step_id="user_codes",
            data_schema=self._user_codes_schema(),
            description_placeholders={"hint": "Associate a PIN code to a user name. Leave empty to skip."},
            last_step=False,
        )

    def _user_codes_schema(self, prefill=None):
        current = self._get(CONF_USER_CODES, {})
        items   = list(current.items())
        prefill = prefill or {}
        fields  = {}
        for i in range(1, 11):
            ex_code = items[i-1][0] if i-1 < len(items) else ""
            ex_name = items[i-1][1] if i-1 < len(items) else ""
            fields[vol.Optional(f"ucode_{i}_code", default=prefill.get(f"ucode_{i}_code", ex_code))] = str
            fields[vol.Optional(f"ucode_{i}_name", default=prefill.get(f"ucode_{i}_name", ex_name))] = str
        return vol.Schema(fields)

    async def async_step_users(self, user_input=None):
        if user_input is not None:
            users = {}
            for i in range(1, 11):
                raw_id   = str(user_input.get(f"user_{i}_id",   "")).strip()
                raw_name = str(user_input.get(f"user_{i}_name", "")).strip()
                if raw_id and raw_name:
                    users[raw_id] = raw_name
            self._options[CONF_USERS] = users
            return await self.async_step_devices()

        current_users = self._get(CONF_USERS, {})
        user_items    = list(current_users.items())
        fields = {}
        for i in range(1, 11):
            ex_id   = user_items[i-1][0] if i-1 < len(user_items) else ""
            ex_name = user_items[i-1][1] if i-1 < len(user_items) else ""
            fields[vol.Optional(f"user_{i}_id",   default=ex_id)]   = str
            fields[vol.Optional(f"user_{i}_name", default=ex_name)] = str

        return self.async_show_form(
            step_id="users",
            data_schema=vol.Schema(fields),
            description_placeholders={"hint": "Map badge/code IDs to names. Leave empty to skip."},
            last_step=False,
        )

    async def async_step_devices(self, user_input=None):
        if user_input is not None:
            devices = {}
            for i in range(1, 21):
                raw_id   = str(user_input.get(f"dev_{i}_id",   "")).strip()
                raw_name = str(user_input.get(f"dev_{i}_name", "")).strip()
                raw_zone = str(user_input.get(f"dev_{i}_zone", "")).strip()
                if raw_id and raw_name:
                    devices[raw_id] = {"name": raw_name, "zone": raw_zone if raw_zone else None}
            self._options[CONF_DEVICES] = devices
            return self.async_create_entry(title="", data=self._options)

        current_devices = self._get(CONF_DEVICES, {})
        dev_items       = list(current_devices.items())
        fields = {}
        for i in range(1, 21):
            ex_id   = dev_items[i-1][0]                       if i-1 < len(dev_items) else ""
            ex_name = dev_items[i-1][1].get("name", "")       if i-1 < len(dev_items) else ""
            ex_zone = dev_items[i-1][1].get("zone", "") or "" if i-1 < len(dev_items) else ""
            fields[vol.Optional(f"dev_{i}_id",   default=ex_id)]   = str
            fields[vol.Optional(f"dev_{i}_name", default=ex_name)] = str
            fields[vol.Optional(f"dev_{i}_zone", default=ex_zone)] = str

        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema(fields),
            description_placeholders={"hint": "Map peripheral IDs to names and zones. Leave empty to skip."},
            last_step=True,
        )
