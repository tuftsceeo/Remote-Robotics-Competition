import json

async def myCallback(message):
    value = json.loads(message.decode())
    
    if value['detected']:
        car_location = {
            'rotation': value['rotation'],
            'x': value['x']*10,
            'y': value['y']*10
        }
        
        await myChannel.post('/Car_Location/All', car_location)
    
    else:
        await myChannel.post('/Car_Location/All', {'y': None, 'x': None, 'rotation': None})
        print("No AprilTag detected")
    
    await myBle.send_str(str(value))

myBle.callback = myCallback
