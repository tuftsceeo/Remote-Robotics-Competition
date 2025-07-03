import json

async def myCallback(message):
    value = json.loads(message.decode())

def fred(message):
    payload = message['payload']
    payload_dict = json.loads(payload)
    topic = payload_dict['topic']
    value = payload_dict['value']
    # print('RECEIVED:', topic, value)
    if (topic == "/Will/Spike"):
        await myBle.send_str(str(value))
    
myBle.callback = myCallback        
myChannel.callback = fred
   
