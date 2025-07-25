import asyncio

async def callback(message):
    pitch = message['pitch']
    roll = message['roll']
    adjusted_pitch = pitch/2
    adjusted_roll = roll + 900
    msg = {'x':adjusted_pitch, 'y':adjusted_roll}
    msgStr = str(msg)
    if myChannel.is_connected:
        await myChannel.post('/Controller_1/data', msg)

w.final_callback = callback