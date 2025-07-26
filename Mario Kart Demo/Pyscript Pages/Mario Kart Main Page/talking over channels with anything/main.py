from pyscript import document, window, when
import RS232
import channel
import ble
import plotly
import files

myRS232 = RS232.CEEO_RS232(divName = 'all_things_rs232', suffix = '1', myCSS = True)
myRS2322 = RS232.CEEO_RS232(divName = 'all_things_rs232_2', suffix = '2', myCSS = True)
myChannel = channel.CEEO_Channel("hackathon", "@chrisrogers", "talking-on-a-channel", divName = 'all_things_channels', suffix='_test')
myBle = ble.CEEO_BLE(divName = 'all_things_ble')

import audio, math
sampleRate = 48000
window = 0.3
points = int(sampleRate * window)
points = 2 ** math.ceil(math.log2(points))
myAudio = audio.CEEO_Audio('all_things_audio', points, sampleRate)

import video
myVideo = video.CEEO_Video('all_things_video')

myPlot = plotly.CEEO_Plotly(divName = 'all_things_plotly')
myFiles = files.CEEO_Files(divName = 'all_things_files')

python_area = document.getElementById('PC_code')

from myCode import generic_code

@when("click", "#loadopenmv")
def on_loadMVcode(event):
    from myCode import openmv_code
    myRS232.python.code = openmv_code + generic_code
    
@when("click", "#loadrp2040")
def on_loadRPcode(event):
    from myCode import rp2040_code
    myRS232.python.code = rp2040_code + generic_code
    
@when("click", "#loadspike")
def on_loadSPIKEcode(event):
    from myCode import spike_code
    myRS232.python.code = spike_code + generic_code
    
@when("click", "#loadesp")
def on_loadESPcode(event):
    from myCode import esp_code
    myRS232.python.code = esp_code + generic_code

@when("click", "#loadte")
def on_loadTEcode(event):
    from myCode import te_code
    python_area.code = te_code 
    
@when("click", "#loaddefault")
def on_loadDefaultcode(event):
    from myCode import default_code
    python_area.code = default_code 
    
on_loadDefaultcode(None)
