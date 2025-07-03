import json

async def myCallback(message):
    value = json.loads(message.decode())
    await myChannel.post('/Will/Spike', value)
    await myBle.send_str(str(value))

# def fred(message):
#     print(message['payload'])

myBle.callback = myCallback        
# myChannel.callback = fred
   
