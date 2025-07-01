from pyscript import document, window, when
import asyncio 
import struct
import plot
from hubs import hubs
import channel
import json

myChannel = channel.CEEO_Channel("hackathon", "@chrisrogers", "talking-on-a-channel", 
                                 divName = 'all_things_channels', suffix='_test')
write = document.getElementById('write')

async def fred(message):
    try:
        if message['type'] == 'data' and 'payload' in message:
            payload_data = json.loads(message['payload'])
            topic = payload_data['topic']
            value = payload_data['value']
            
            if topic == '/OpenMV/x':
                write.innerHTML = f"X coordinate: {value}"
            elif topic == '/OpenMV/y':
                write.innerHTML = f"Y coordinate: {value}"
                
    except Exception as e:
        print(f"Error processing message: {e}")
        print(f"Message received: {message}")

myChannel.callback = fred
