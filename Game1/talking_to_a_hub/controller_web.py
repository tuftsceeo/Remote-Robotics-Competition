import asyncio
import time
import json

await w.feed_rate(40)

async def grab(message):
    controller_data = { 'x': message['IMU']['roll'], 'y': message['IMU']['pitch'] }
    if myChannel.is_connected:
        await myChannel.post('/Controller/data', controller_data)

w.final_callback = grab
