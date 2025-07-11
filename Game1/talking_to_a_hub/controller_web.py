import asyncio
import time
import json

await w.feed_rate(40)

async def grab(message):
    # value = message['IMU']['yaw']
    controller_data = { 'x': message['x'], 'y': message['y'] }
    if myChannel.is_connected:
        # await myChannel.post('/SPIKE/yaw',value)
        await myChannel.post('/Controller/data', controller_data)

w.final_callback = grab
