from .const import DOMAIN
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import SensorEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN]['coordinator']
    coordinator.add_sensors_cb[entry.data.get('device_key')] = async_add_entities

class TestSensor(Entity):
    def __init__(self, uniq_id):
        self.should_poll = False
        self._attr_unique_id = uniq_id

    def setval(self, value):
        self.state = value
        self.async_schedule_update_ha_state()

class ExampleSensor(SensorEntity):
    def __init__(self, uniq_id):
        self.should_poll = False
        self._attr_unique_id = uniq_id

    def setval(self, value):
        self._attr_native_value = value
        self.async_schedule_update_ha_state()
