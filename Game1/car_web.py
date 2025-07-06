import json

controller_data = {"x": 0, "y": 0}
print("Starting...")

async def fred(message):
    payload = message['payload']
    payload_dict = json.loads(payload)
    topic = payload_dict['topic']
    value = payload_dict['value']
    
    if topic == "/Controller/x":
        controller_data["x"] = value
    elif topic == "/Controller/y":
        controller_data["y"] = value
    
    combined_data = json.dumps(controller_data)
    await myBle.send_str(combined_data)
    
myChannel.callback = fred
