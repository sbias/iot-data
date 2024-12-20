import aiohttp
import asyncio
import ssl
import os
from .sensor import TestSensor
from .const import LOGGER

async def iotdata_dev_info(dev, sec):
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.load_verify_locations(os.path.dirname(__file__) + "/iot-data-ca.crt")
    conn = aiohttp.TCPConnector(ssl_context=ssl_ctx)
    async with aiohttp.ClientSession(connector=conn) as session:
        async with session.post(
            'https://sdk.iot-data.org/a/info',
            json={'dev': dev, 'sec': sec}
        ) as resp:
            return await resp.json()
        
class IotDataOrgCoordinator():
    def __init__(self):
        self.testsensor = None
        self.websocket = None
        self.add_sensors_cb = {}
        self.entity_map = {}
        self.subscriptions = []
    
    async def ws_session_loop(self):
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.load_verify_locations(os.path.dirname(__file__) + "/iot-data-ca.crt")
        conn = aiohttp.TCPConnector(ssl_context=ssl_ctx)
        async with aiohttp.ClientSession(connector=conn) as session:
            async with session.ws_connect('https://sdk.iot-data.org/a/wj', heartbeat=119.0) as websocket:
                self.websocket = websocket
                for subscription in self.subscriptions:
                    await self.send_subscribe(*subscription)
                async for msg in websocket:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = msg.json()

                        if data['d'] in self.add_sensors_cb:
                            uniq_id = f"{data['d']}_{data['a']}"
                            if uniq_id in self.entity_map:
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
                                    sensor.setval(state)
                            
                            else:
                                pass # unhandled data

                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print("Error receive %s" % websocket.exception())
                            await websocket.close()
                            return

    async def amain(self, hass):
      while True:
        try:
            await self.ws_session_loop()
        except aiohttp.client_exceptions.WSServerHandshakeError as ex:
            LOGGER.warn(f'HandshakeError in WS session {ex}')
        except Exception as ex:
            LOGGER.warn(f'Exception in WS session {ex}')
        finally:
            self.websocket = None

        await asyncio.sleep(180)

    async def subscribe(self, device_key, secret):
        retry_delay = 5
        while True:
            try:
                info = await iotdata_dev_info(device_key, secret)
                break
            except Exception as ex:
                print(ex)
                await asyncio.sleep(retry_delay)
                retry_delay += 5

        for attr in info['attributes']:
            uniq_id = f"{device_key}_{attr['name']}"
            if uniq_id not in self.entity_map:
                sensor = TestSensor(uniq_id)
                self.add_sensors_cb[device_key]([sensor])
                self.entity_map[uniq_id] = sensor
                sensor.unit_of_measurement = attr['uom']
                sensor.icon = attr['icon']
               # sensor.state_class = attr['state_class']

        subscription = [device_key, secret]
        self.subscriptions.append(subscription)
        await self.send_subscribe(*subscription)

    async def send_subscribe(self, device_key, secret):
        if self.websocket:
            await self.websocket.send_json({'sub': device_key, 'sec': secret})

    async def state_listener(self, device_key, attr, event):
        state = event.data.get("new_state")
        if self.websocket and state:
            try:
                await self.websocket.send_json({'d': device_key, 'a': attr, 'v': state.state})
            except aiohttp.client_exceptions.ClientConnectionResetError:
                await self.websocket.close()
#            meta =  state.attributes
#            await self.websocket.send_json({'d': device_key, 'a': attr, 'm': meta})

