from pyscript import document, window, when
import asyncio 
import struct
import plot
from hubs import hubs
import channel

myPlot = plot.plot("plot")
myChannel = channel.CEEO_Channel("hackathon", "@chrisrogers", "talking-on-a-channel", divName = 'all_things_channels', suffix='_test')

from pyscript.js_modules import files

fileName = document.getElementById('fileRead')
content = document.getElementById('file_text')

files = files.newFile()
python_area = document.getElementById('PC_code')

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


w = hubs(2,myPlot, False)
