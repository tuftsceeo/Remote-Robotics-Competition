
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
        msg = ujson.loads(data.decode())
        x = msg.get('x', 0)
        y = msg.get('y', 0)
        print("Received x: {:.2f}, y: {:.2f}, z: {:.2f}".format(x, y, msg.get('z', 0)))

        threshold = 0.2  # minimum tilt to start moving (adjust as needed)
        max_speed = 100

        left_speed = 0
        right_speed = 0

        # Forward/backward: Y-axis
        if abs(y) > threshold:
            speed = min(abs(y) * max_speed, max_speed)
            if y > 0:
                # Tilt forward → move forward
                left_speed = speed
                right_speed = -speed
            else:
                # Tilt backward → move backward
                left_speed = -speed
                right_speed = speed

        # Turning: X-axis adds differential to left/right speeds
        if abs(x) > threshold:
            turn_speed = min(abs(x) * max_speed, max_speed)
            if x > 0:
                # Tilt right → turn right by speeding up left motor
                left_speed += turn_speed
                right_speed -= turn_speed
            else:
                # Tilt left → turn left by speeding up right motor
                left_speed -= turn_speed
                right_speed += turn_speed

        # Clip speeds to [-100, 100]
        left_speed = max(-max_speed, min(max_speed, left_speed))
        right_speed = max(-max_speed, min(max_speed, right_speed))

        # Send commands to motors
        motor.run(port.A, int(left_speed))
        motor.run(port.B, int(right_speed))
        print("Motors: left {}, right {}".format(int(left_speed), int(right_speed)))

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
                time.sleep(1)
            print('lost connection')
    except Exception as e:
        print('Error: ',e)
    finally:
        p.disconnect()
        print('closing up')
         
peripheral('Car')
