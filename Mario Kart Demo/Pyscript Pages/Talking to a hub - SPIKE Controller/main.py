from pyscript import document, window, when
import asyncio 
import struct

python_area = document.getElementById('PC_code')

import plot
myPlot = plot.plot("plot")

import Hub 
w = Hub.Hub_PS(divName = 'all_things_hubs', hub = 0)


import channel
myChannel = channel.CEEO_Channel("hackathon", "@chrisrogers", "talking-on-a-channel", divName = 'all_things_channels', suffix='_test')

from pyscript.js_modules import files

fileName = document.getElementById('fileRead')
content = document.getElementById('file_text')

files = files.newFile()

@when("change", "#fileRead")
async def on_local_read(event): 
    path = fileName.value
    window.console.log(path)
    fred = await files.read('fileRead')
    window.console.log(fred)
    python_area.code = fred

@when("click", "#local")
async def on_save(event): 
    filename = fileName.value
    name = filename.split('\\')[-1] if filename else 'test.py'
    await files.save(python_area.code, name)
