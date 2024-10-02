from .const import DOMAIN
from homeassistant.const import Platform
from .coordinator import IotDataOrgCoordinator
import asyncio
from homeassistant.helpers.event import async_track_state_change_event

async def async_setup(hass, config):
    coordinator = IotDataOrgCoordinator()
    asyncio.create_task(coordinator.amain(hass))
    hass.data.setdefault(DOMAIN, {})['coordinator'] = coordinator

    return True

def async_state_listener_partial(coordinator, device_key, attr):
    async def func2(*args2):
        return await coordinator.state_listener(device_key, attr, *args2)
    return func2

async def async_setup_entry(hass, entry):
    coordinator = hass.data[DOMAIN]['coordinator']
    device_key = entry.data['device_key']
    secret = entry.data['secret']

    await coordinator.subscribe(device_key, secret)

    for attr, entity_id in entry.options.items():
        async_track_state_change_event(hass, entity_id, async_state_listener_partial(coordinator, device_key, attr))

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True

