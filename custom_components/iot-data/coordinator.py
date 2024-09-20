import aiohttp
import asyncio
from .sensor import TestSensor


class IotDataOrgCoordinator():
    def __init__(self):
        self.testsensor = None
        self.websocket = None
        self.add_sensors_cb = {}
        self.entity_map = {}
        self.subscriptions = []

    async def amain(self, hass):

      while True:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.ws_connect('https://www.iot-data.org/a/wj', heartbeat=119.0) as websocket:
                    self.websocket = websocket
                    for subscription in self.subscriptions:
                        await self.send_subscribe(*subscription)
                    async for msg in websocket:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = msg.json()

                            if data['d'] in self.add_sensors_cb:
                                uniq_id = f"{data['d']}_{data['e']}"
                                if uniq_id not in self.entity_map:
                                    sensor = TestSensor()
                                    sensor._attr_unique_id = uniq_id
                                    self.add_sensors_cb[data['d']]([sensor])
                                    self.entity_map[uniq_id] = sensor
                                else:
                                    sensor = self.entity_map[uniq_id]

                                if 'v' in data:
                                    v = data['v']
                                    if v == 'unavailable' or v == 'unknown':
                                        state = None                              
                                    else:
                                        try:
                                            state = float(data['v'])
                                        except ValueError:
                                            state = str(data['v'])
                                    sensor.state = state  
                                    sensor.async_schedule_update_ha_state()
                                
                                elif 'm' in data:
                                    m = data['m']
                                    if 'unit_of_measurement' in m:
                                        sensor.unit_of_measurement = m['unit_of_measurement']

                                else:
                                    pass # unhandled data

                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                print("Error receive %s" % websocket.exception())
                                await websocket.close()

            except aiohttp.client_exceptions.WSServerHandshakeError:
                pass
        self.websocket = None
        await asyncio.sleep(180)

    async def subscribe(self, device_key, secret):
        subscription = [device_key, secret]
        self.subscriptions.append(subscription)
        await self.send_subscribe(*subscription)

    async def send_subscribe(self, device_key, secret):
        if self.websocket:
            await self.websocket.send_json({'sub': device_key, 'sec': secret})

    async def state_listener(self, device_key, event):
        state = event.data.get("new_state")
        if self.websocket:
            await self.websocket.send_json({'d': device_key, 'e': state.entity_id.replace('.', '_'), 'v': state.state})
            meta =  state.attributes
            await self.websocket.send_json({'d': device_key, 'e': state.entity_id.replace('.', '_'), 'm': meta})

