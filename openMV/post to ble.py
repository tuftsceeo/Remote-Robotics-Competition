import json

async def myCallback(message):
    value = json.loads(message.decode())
    # what do we want to post?
    await myChannel.post('/OpenMV/x', value['x'])
    await myChannel.post('/OpenMV/y', value['y'])
    await myBle.send_str(str(value))
    # myPlot.update_chart(value['x'])

# def fred(message):
    # Do we want to listen for anything from the channel?
    # print("Channel time!")

myBle.callback = myCallback        
# myChannel.callback = fred
   
