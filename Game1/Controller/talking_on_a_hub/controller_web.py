import asyncio
import json

await w.feed_rate(100)

async def grab(message):
    value1 = message.get('IMU', {}).get('roll')
    value2 = message.get('IMU', {}).get('yaw')
    controller_data = {'x': value1, 'y': value2}
    if myChannel.is_connected:
        await myChannel.post('/Controller/data', controller_data)

w.final_callback = grab
