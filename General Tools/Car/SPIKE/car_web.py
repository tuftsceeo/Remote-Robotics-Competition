import json

controller_data = {"x": 0, "y": 0}
print("Starting...")

async def fred(message):
    try:
        topic, value = myChannel.check('/Controller/data', message)
        if topic:
            controller_data["x"] = value.get("x", 0)
            controller_data["y"] = value.get("y", 0)
            
            combined_data = json.dumps(controller_data)
            await myBle.send_str(combined_data)
            return  # Keep the early exit?
        
        topic, value = myChannel.check('/Car_Location_1/Peeled', message)
        if topic:
            controller_data["s"] = value
            combined_data = json.dumps(controller_data)
            await myBle.send_str(combined_data)
            
    except Exception as e:
        print('Error in controller handler:', e)

myChannel.callback = fred
