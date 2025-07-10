import time
from hub import motion_sensor
from BLE_CEEO import Yell, Listen
import time
import json

def grabData():
    (x,y,z)= motion_sensor.acceleration() #The values are mili G, so 1 / 1000 G
    message = {'x':x, 'y':y}
    return str(json.dumps(message))

def peripheral(name): 
    try:
        print('waiting ...')
        p = Yell(name, interval_us=30000, verbose = False)
        if p.connect_up():
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
         
peripheral('Controller_spike')
