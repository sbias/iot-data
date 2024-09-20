from .const import DOMAIN

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import selector

class IotDataOrgConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 0
    MINOR_VERSION = 0

    async def async_step_user(
        self, user_input
    ) -> FlowResult:
        errors: dict = {}
        if user_input is not None:
            device_key = user_input['device_key']
            publish_entities = user_input['publish_entities']            

            await self.async_set_unique_id(f"{DOMAIN}_{device_key}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=device_key, data=user_input)

        schema = {}                                                       
        schema[vol.Required('device_key')] = cv.string                    
        schema[vol.Required('secret')] = cv.string                    
        schema[vol.Optional('publish_entities')] = selector.EntitySelector(
                    selector.EntitySelectorConfig(multiple=True)   
                )

        return self.async_show_form(
            step_id="user",
            errors=errors,
            data_schema=vol.Schema(schema)
        )

