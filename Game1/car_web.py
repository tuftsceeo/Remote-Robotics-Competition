import json

# async def myCallback(message):
#     value = json.loads(message.decode())

def fred(message):
    print(message['payload'])
    try: 
        await myBle.send_str(str(message['payload']))
    except Exception as e:
        print("ERROR: ", e)
    
# myBle.callback = myCallback        
myChannel.callback = fred
   
