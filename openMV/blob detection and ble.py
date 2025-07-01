import sensor
import time
import math
import json

red_thresholds = (30, 100, 15, 127, 15, 127)

sensor.reset()
sensor.set_pixformat(sensor.RGB565)  # RGB565 for color detection
sensor.set_framesize(sensor.VGA)
sensor.set_auto_gain(False)  # must be turned off for color tracking
sensor.set_auto_whitebal(False)  # must be turned off for color tracking

def grabData():
    message = {"x": 0, "y": 0, "angle": 0, "area": 0}
    img = sensor.snapshot()
    
    blobs = img.find_blobs([red_thresholds], 
                          pixels_threshold=200,
                          area_threshold=200,
                          merge=True)
    
    # Find the largest red blob
    for blob in blobs:
        if blob.area() > message['area']:
            message['x'], message['y'], message['angle'], message['area'] = blob.cx(), blob.cy(), int(math.degrees(blob.rotation())), blob.area()
    
    return str(json.dumps(message))

from BLE_CEEO import Yell, Listen

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
         
peripheral('Maria')
