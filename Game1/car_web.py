import json

# async def myCallback(message):
#     value = json.loads(message.decode())

def fred(message):
    payload = message['payload']
    payload_dict = json.loads(payload)
    topic = payload_dict['topic']
    value = payload_dict['value']
    if (topic == "/Controller/x"):
        # await myBle.send_str({'x':str(value)})
        await myBle.send_str(str(value))
    if (topic == "/Controller/y"):
        # await myBle.send_str({'y':str(value)})
        await myBle.send_str(str(value))
    
# myBle.callback = myCallback        
myChannel.callback = fred
   
