# ------------------------------
# INSTRUCTIONS
# ------------------------------

# CONNECT THE OPENMV CAM:
#  - Copy the code in code_for_openMV.py
#  - Navigate to Chris's Talking On Anyone Page.
#  - Connect the OPENMV cam using serial.
#  - Connect over BLE and look for 'OPENMV'
#  - In the terminal lower on the page run this code:

# import json

# async def myCallback(message):
#     value = json.loads(message.decode())
#     await myChannel.post('/OpenMV/x', value['x'])
#     await myChannel.post('/OpenMV/y', value['y'])
#     await myBle.send_str(str(value))

# myBle.callback = myCallback        
   
# ------------------------------
# CODE
# ------------------------------

import sensor
import time
import math
import json

# Red color tracking thresholds in LAB color space
# Format: (L_min, L_max, A_min, A_max, B_min, B_max)
# These values may need tuning based on your lighting conditions
red_thresholds = (30, 100, 15, 127, 15, 127)

sensor.reset()
sensor.set_pixformat(sensor.RGB565)  # Changed to RGB565 for color detection
sensor.set_framesize(sensor.VGA)
sensor.set_auto_gain(False)  # must be turned off for color tracking
sensor.set_auto_whitebal(False)  # must be turned off for color tracking

def grabData():
    message = {"x": 0, "y": 0, "angle": 0, "area": 0}
    img = sensor.snapshot()
    
    # Find red blobs using LAB color space thresholds
    blobs = img.find_blobs([red_thresholds], 
                          pixels_threshold=200,    # Increased for better filtering
                          area_threshold=200,      # Increased for better filtering
                          merge=True)
    
    # Find the largest red blob (same logic as original code)
    for blob in blobs:
        if blob.area() > message['area']:
            message['x'], message['y'], message['angle'], message['area'] = blob.cx(), blob.cy(), int(math.degrees(blob.rotation())), blob.area()
    
    return str(json.dumps(message))

# Your original Bluetooth peripheral code - unchanged
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
         
peripheral('OPENMV')
