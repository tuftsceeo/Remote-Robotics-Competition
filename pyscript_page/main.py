from pyscript import document, window, when
import asyncio 
import struct
import plot
from hubs import hubs
import channel
import json

myChannel = channel.CEEO_Channel("hackathon", "@chrisrogers", "talking-on-a-channel", divName = 'all_things_channels', suffix='_test')

write = document.getElementById('write')

def fred(message):
    value = json.loads(message.decode())
    print("RECEIVED: ", value)
    
myChannel.callback = fred
   
