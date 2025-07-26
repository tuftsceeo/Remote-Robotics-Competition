car_spike_code = '''
import time
from hub import motion_sensor
from BLE_CEEO import Yell, Listen
import time
import json
from hub import light_matrix, port
import motor
import ujson

def callback(data):
    try:   
        print("RECEIVED: ", data)
        decoded_data = data.decode()
        controller_data = json.loads(decoded_data)
        
        # x and y SWITCHED bc my controller is built sideways
        x_raw = float(controller_data.get("y", 0))
        y_raw = float(controller_data.get("x", 0))
        x = x_raw / 1000.0
        y = y_raw / 1000.0
        
        try:
            spin = float(controller_data.get("s", 0))
            if (spin == True):
                print("HIT BY BANANA")
                # sound.beep(440)
                motor.run(port.A, 500)
                motor.run(port.B, 500)
        except Exception as e:
            print("ERROR: ", e)
            
        # Clamp values to [-1, 1] in case of slight overshoot
        x = max(-1.0, min(1.0, x))
        y = max(-1.0, min(1.0, y))
        print("X_normalized:", x, "Y_normalized:", y)
        
        threshold = 0.05
        max_speed = 500
        left_speed = 0
        right_speed = 0
        
        if abs(x) < threshold:
            x = 0
        if abs(y) < threshold:
            y = 0
            
        base_speed = y * max_speed
        turn_adjustment = x * max_speed
        
        # Calculate individual wheel speeds
        # Positive y = forward, negative y = backward
        # Positive x = turn right, negative x = turn left
        left_speed = base_speed + turn_adjustment
        right_speed = base_speed - turn_adjustment
        
        # Clip speeds to [-100, 100]
        left_speed = max(-max_speed, min(max_speed, left_speed))
        right_speed = max(-max_speed, min(max_speed, right_speed))
        
        motor.run(port.A, int(left_speed))
        motor.run(port.B, int(right_speed))
        print("Motors: left {}, right {}".format(int(left_speed), int(right_speed)))
        
    except json.JSONDecodeError as e:
        print("JSON decode error:", e)
    except Exception as e:
        print("Callback error: {}".format(e))

def peripheral(name): 
    try:
        print('waiting ...')
        p = Yell(name, interval_us=30000, verbose = False)
        if p.connect_up():
            p.callback = callback
            print('Connected')
            time.sleep(1)
            while p.is_connected:
                p.send("I'm listening...")
                time.sleep(0.5)
            print('lost connection')
    except Exception as e:
        print('Error: ',e)
    finally:
        p.disconnect()
        print('closing up')
         
peripheral('Car')
'''

car_web_code = '''
import json
import asyncio
print("Starting...")

async def fred(message):
    topic, value = myChannel.check('/Controller_2/data', message)
    if topic:
        controller_data = {"x": 0, "y": 0}
        controller_data["x"] = value.get("x", 0)
        controller_data["y"] = value.get("y", 0)
        
        combined_data = json.dumps(controller_data)
        await myBle.send_str(combined_data)
    
    topic, value = myChannel.check('/Car_Location_2/Peeled', message)
    if topic:
        # controller_data["s"] = value
        data = json.dumps(controller_data)
        await myBle.send_str(data)

myChannel.callback = fred


'''