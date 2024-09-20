from .const import DOMAIN
from homeassistant.helpers.entity import Entity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN]['coordinator']

    coordinator.add_sensors_cb[entry.data.get('device_key')] = async_add_entities

class TestSensor(Entity):
    def __init__(self):
        self.should_poll = False


