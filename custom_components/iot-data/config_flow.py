from .const import DOMAIN

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import selector
from homeassistant import config_entries
from homeassistant.core import callback
from aiohttp import ClientSession

async def iotdata_dev_info(dev, sec):
    async with ClientSession() as session:
        async with session.post(
            'https://www.iot-data.org/a/info',
            json={'dev': dev, 'sec': sec}
        ) as resp:
            return await resp.json()



class IotDataOrgConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 0
    MINOR_VERSION = 0

    async def async_step_user(
        self, user_input
    ) -> FlowResult:
        errors: dict = {}
        if user_input is not None:
            device_key = user_input['device_key']

            await self.async_set_unique_id(f"{DOMAIN}_{device_key}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=device_key, data=user_input)

        schema = {}
        schema[vol.Required('device_key')] = cv.string
        schema[vol.Required('secret')] = cv.string
       
        return self.async_show_form(
            step_id="user",
            errors=errors,
            data_schema=vol.Schema(schema)
        )


    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> FlowResult:
       info = await iotdata_dev_info(self.config_entry.data.get("device_key"), self.config_entry.data.get("secret"))

       if user_input is not None:
            return self.async_create_entry(title=self.config_entry.data.get("device_key"), data=user_input)

       schema = {}
       for attr in info['attributes']:
            schema[
                    vol.Optional(
                        attr,
                        description={
                            "suggested_value": self.config_entry.options.get(attr, "")
                        }
                    )
                ] = selector.EntitySelector(selector.EntitySelectorConfig(multiple=False))

       return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
       )
