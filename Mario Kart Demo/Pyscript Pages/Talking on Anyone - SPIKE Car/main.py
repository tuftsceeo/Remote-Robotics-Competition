from pyscript import document, window, when
import RS232
import channel
import ble
import plotly
import files

myRS232 = RS232.CEEO_RS232(divName = 'all_things_rs232', suffix = '1', myCSS = True)
myChannel = channel.CEEO_Channel("hackathon", "@chrisrogers", "talking-on-a-channel", divName = 'all_things_channels', suffix='_test')
myBle = ble.CEEO_BLE(divName = 'all_things_ble')

import audio, math
sampleRate = 48000
window = 0.3
points = int(sampleRate * window)
points = 2 ** math.ceil(math.log2(points))

python_area = document.getElementById('PC_code')

@when("click", "#loadSPIKE")
def on_loadMVcode(event):
    from myCode import car_spike_code
    myRS232.python.code = car_spike_code

@when("click", "#loadWEB")
def on_loadDefaultcode(event):
    from myCode import car_web_code
    python_area.code = car_web_code 
    
on_loadDefaultcode(None)
