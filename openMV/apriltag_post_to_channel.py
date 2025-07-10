import json

async def myCallback(message):
    value = json.loads(message.decode())
    
    if value['detected']:
        await myChannel.post('/OpenMV/apriltag_id', value['tag_id'])
        await myChannel.post('/OpenMV/apriltag_distance', value['distance'])
        await myChannel.post('/OpenMV/apriltag_rotation', value['rotation'])
        await myChannel.post('/OpenMV/x', value['x'])
        await myChannel.post('/OpenMV/y', value['y'])
        await myChannel.post('/OpenMV/area', value['area'])
        print(f"Tag {value['tag_id']} detected at distance {value['distance']:.2f}m")
    else:
        await myChannel.post('/OpenMV/no_tags', True)
        print("No AprilTag detected")
    
    await myBle.send_str(str(value))

myBle.callback = myCallback  
