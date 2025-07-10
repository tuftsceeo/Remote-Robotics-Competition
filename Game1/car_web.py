import json

controller_data = {"x": 0, "y": 0}
print("Starting...")

async def fred(message):
    payload = message['payload']
    payload_dict = json.loads(payload)
    topic = payload_dict['topic']
    value = payload_dict['value']
    
    if topic == "/Controller/data":
        controller_data["x"] = value.get("x", 0)
        controller_data["y"] = value.get("y", 0)
        
        if "s" in value:
            controller_data["s"] = value["s"]
    elif topic == "/Controller/Peel":
        controller_data["s"] = value
    
    combined_data = json.dumps(controller_data)
    await myBle.send_str(combined_data)
    
myChannel.callback = fred
