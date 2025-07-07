import json

async def myCallback(message):
    value = json.loads(message.decode())
    await myChannel.post('/Controller/x', value['x'])
    await myChannel.post('/Controller/y', value['y'])

myBle.callback = myCallback
