import asyncio
import json

flag = False

async def myCallback(message):
    value = json.loads(message.decode())

async def fred(message):
    global flag
    topic, value = myChannel.check('/Controller_1/data', message)
    topic2, value2 = myChannel.check('/Car_Location_1/Peeled', message)
    if (topic2):
        try:
            spin = (value2 == "True")
            if (spin == True):
                await w.motor_speed(1, 100)
                await w.motor_speed(2, 100)
                flag = True
            else:
                flag = False
                await w.motor_speed(3, 0)
                
                    
        except Exception as e:
            print('ERROR: ', e)
    
    if (topic and not flag):
        # x and y SWITCHED bc my controller is built sideways
        x_raw = float(value.get('y', 0))
        y_raw = float(value.get('x', 0))
        x = x_raw / 1000.0
        y = y_raw / 1000.0


        


        # Clamp values to [-1, 1] in case of slight overshoot
        x = max(-1.0, min(1.0, x))
        y = max(-1.0, min(1.0, y))
        
        threshold = 0.05
        max_speed = 100
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

        await w.motor_speed(1, int(left_speed))
        await w.motor_speed(2, int(right_speed))
        await w.motor_run(1, 0)
        await w.motor_run(2, 0)

await w.motor_run(3, 0)
myChannel.callback = fred