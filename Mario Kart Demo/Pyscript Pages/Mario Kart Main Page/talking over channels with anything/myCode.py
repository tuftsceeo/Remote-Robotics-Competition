generic_code = '''from BLE_CEEO import Yell, Listen
import time
import json

def callback(data):
        print(data.decode())

def peripheral(name): 
    try:
        print('waiting ...')
        p = Yell(name, interval_us=30000, verbose = False)
        #sensor.skip_frames(time=2000)
        if p.connect_up():
            p.callback = callback
            print('Connected')
            time.sleep(1)
            while p.is_connected:
                p.send(grabData())
                time.sleep(1)
            print('lost connection')
    except Exception as e:
        print('Error: ',e)
    finally:
        p.disconnect()
        print('closing up')
         
peripheral('Maria')'''

rp2040_code = '''
import time
import machine

def grabData():
    temp_sensor = machine.ADC(4)
    temp_celsius = 27 - (temp_sensor.read_u16() * 3.3 / 65535 - 0.706) / 0.001721
    message = {"x": temp_celsius}
    return str(json.dumps(message))
    
'''
spike_code = '''
import time
from hub import motion_sensor

def grabData():
    (x,y,z)= motion_sensor.acceleration() #The values are mili G, so 1 / 1000 G
    message = {'x':x, 'y':y, 'z':z}
    return str(json.dumps(message))
    
'''

esp_code = '''import time
import machine, esp

analog_pins = [0, 1, 2, 3, 4, 5]
digital_pins = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 21]
led_pin = 15

def grabData():
    led = machine.Pin(led_pin, machine.Pin.OUT)
    
    for i in range(3):
        led.on()
        time.sleep_ms(50)
        led.off()
        time.sleep_ms(50)
    
    message = {}
        
    pin = analog_pins[0]
    adc = machine.ADC(machine.Pin(pin))
    adc.atten(machine.ADC.ATTN_11DB)  # Full 3.3V range
    raw_value = adc.read()
    voltage = raw_value * 3.3 / 4095
    message[f"A{pin}"] = {
        'pin': pin,
        'raw': raw_value,
        'voltage': round(voltage, 3)
        }
        
    pin = digital_pins[11]
    gpio = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)
    value = gpio.value()
    message[f"D{pin}"] = {
        'pin': pin,
        'value': value,
        'state': 'HIGH' if value else 'LOW'
    }
    
    message['x'] = esp32.mcu_temperature()
    return str(json.dumps(message))

'''
te_code = '''import json, asyncio, struct
 
def array(data):
    data = [d for d in data]
    asyncio.create_task(myChannel.post('/te/array',data))

def controller(data):
    message = struct.unpack('bb', data[7:9])
    asyncio.create_task(myChannel.post('/te/controller',message))

def light(data):
    message = struct.unpack('b', data[18:19])[0]
    asyncio.create_task(myChannel.post('/te/light',message))

def single_motor(data):
    message = struct.unpack('<i', data[14:18])[0]
    asyncio.create_task(myChannel.post('/te/single_motor',message))
    
myBle.callback = array 
#await myBle.ask(None)
await myBle.write([0x00])
await myBle.write([40,232,3])
'''

openmv_code = '''
import sensor
import time
import math

# Color Tracking Thresholds taken from their example
# The below grayscale threshold is set to only find extremely bright white areas.
thresholds = (245, 255)

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.VGA)
sensor.set_auto_gain(False)  # must be turned off for color tracking
sensor.set_auto_whitebal(False)  # must be turned off for color tracking

# Only blobs that with more pixels than "pixel_threshold" and more area than "area_threshold" are
# returned by "find_blobs" below. Change "pixels_threshold" and "area_threshold" if you change the
# camera resolution. "merge=True" merges all overlapping blobs in the image.

def grabData():
    message = {"x": 0, "y": 0, "angle": 0, "area": 0}
    img = sensor.snapshot()
    blobs = img.find_blobs([thresholds], pixels_threshold=100, area_threshold=100, merge=True)
    for blob in blobs:
            if blob.area() > message['area']:
                    message['x'], message['y'],message['angle'],message['area']  = blob.cx(), blob.cy(), int(math.degrees(blob.rotation())), blob.area()
    return str(json.dumps(message))
    
'''

default_code = '''import json

async def myCallback(message):
    value = json.loads(message.decode())
    await myChannel.post('/OpenMV/tracker', value['x'])
    await myBle.send_str(str(value))
    myPlot.update_chart(value['x'])

def fred(message):
    print(message['payload'])

myPlot.initialize(100, 'iteration','value', 'live feed')
myBle.callback = myCallback        
myChannel.callback = fred
   
'''
old_default = '''import json, asyncio

def channelPost(message):
    asyncio.create_task(myChannel.post('/OpenMV/tracker',message)) #since we are already within an async call, we just need to create a new task

def BlePost(message):
    asyncio.create_task(myBle.send_str(message))
    
def myCallback(message):
    value = json.loads(message.decode())
    channelPost(value['x'])
    BlePost(str(value))
    myPlot.update_chart(value['x'])

def fred(message):
    print(message['payload'])

myPlot.initialize(100, 'iteration','value', 'live feed')
myBle.callback = myCallback        
myChannel.callback = fred
   
'''

