import json

async def myCallback(message):
    value = json.loads(message.decode())
    controller_data = { 'x': value['x'], 'y': value['y'] }
    await myChannel.post('/Controller/data', controller_data)

myBle.callback = myCallback
