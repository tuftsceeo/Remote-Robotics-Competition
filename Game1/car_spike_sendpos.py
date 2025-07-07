import time
from hub import motion_sensor
from BLE_CEEO import Yell, Listen
import json
from hub import light_matrix, port
import motor
import ujson

position_x = 0.0
position_y = 0.0
velocity_x = 0.0
velocity_y = 0.0
last_time = 0
last_accel_x = 0.0
last_accel_y = 0.0
orientation_offset = 0.0

def sendData():
    global position_x, position_y, velocity_x, velocity_y, last_time, last_accel_x, last_accel_y, orientation_offset
    (x_accel, y_accel, z_accel) = motion_sensor.acceleration()
    
    try:
        (yaw, pitch, roll) = motion_sensor.tilt_angles()
    except:
        print("NOT AVAILABLE")
        yaw = motion_sensor.get_yaw_angle() if hasattr(motion_sensor, 'get_yaw_angle') else 0
        pitch = motion_sensor.get_pitch_angle() if hasattr(motion_sensor, 'get_pitch_angle') else 0
        roll = motion_sensor.get_roll_angle() if hasattr(motion_sensor, 'get_roll_angle') else 0
    
    # Convert acceleration from milli-G to m/s²
    # 1G = 9.81 m/s², so milli-G to m/s² = (value/1000) * 9.81
    accel_x_ms2 = (x_accel / 1000.0) * 9.81
    accel_y_ms2 = (y_accel / 1000.0) * 9.81
    accel_z_ms2 = (z_accel / 1000.0) * 9.81
    
    threshold = 0.1  # m/s² threshold to ignore small accelerations
    if abs(accel_x_ms2) < threshold:
        accel_x_ms2 = 0
    if abs(accel_y_ms2) < threshold:
        accel_y_ms2 = 0
    
    # Get current time
    current_time = time.ticks_ms()
    
    if last_time > 0:
        # Calculate time difference in seconds
        dt = (current_time - last_time) / 1000.0
        
        if dt > 0 and dt < 1.0:  # Sanity check for reasonable time intervals
            # Integrate acceleration to get velocity (v = v0 + a*dt)
            velocity_x += accel_x_ms2 * dt
            velocity_y += accel_y_ms2 * dt
            
            # Apply velocity damping to reduce drift
            damping_factor = 0.95  # Reduces velocity over time to account for friction
            velocity_x *= damping_factor
            velocity_y *= damping_factor
            
            # Integrate velocity to get position (s = s0 + v*dt)
            position_x += velocity_x * dt
            position_y += velocity_y * dt
    
    # Update last values
    last_time = current_time
    last_accel_x = accel_x_ms2
    last_accel_y = accel_y_ms2

    # SEND IT!
    final_x = round(position_x, 3)
    final_y = round(position_y, 3)
    message = {'x': final_x, 'y': final_y, 'yaw': yaw}    
    return str(json.dumps(message))

def reset_position():
    """Reset position tracking to origin"""
    global position_x, position_y, velocity_x, velocity_y, last_time
    position_x = 0.0
    position_y = 0.0
    velocity_x = 0.0
    velocity_y = 0.0
    last_time = 0
    print("Position reset to origin")

def callback(data):
    try:   
        print("RECEIVED: ", data)
        decoded_data = data.decode()
        controller_data = json.loads(decoded_data)
        
        # Check if this is a reset command
        if 'reset_position' in controller_data and controller_data['reset_position']:
            reset_position()
            return
        
        # x and y SWITCHED bc my controller is built sideways
        x_raw = float(controller_data.get("y", 0))
        y_raw = float(controller_data.get("x", 0))
        x = x_raw / 1000.0
        y = y_raw / 1000.0
        
        # Clamp values to [-1, 1] in case of slight overshoot
        x = max(-1.0, min(1.0, x))
        y = max(-1.0, min(1.0, y))
        
        print("X_normalized:", x, "Y_normalized:", y)
        
        threshold = 0.05
        max_speed = 1000
        
        if abs(x) < threshold:
            x = 0
        if abs(y) < threshold:
            y = 0
        
        base_speed = y * max_speed
        turn_adjustment = x * max_speed
        
        # Calculate individual wheel speeds
        left_speed = base_speed + turn_adjustment
        right_speed = base_speed - turn_adjustment
        
        # Clip speeds to [-max_speed, max_speed]
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
        reset_position()
        
        p = Yell(name, interval_us=30000, verbose=False)
        if p.connect_up():
            p.callback = callback
            print('Connected')
            time.sleep(1)
            
            while p.is_connected:
                p.send(sendData())
                time.sleep(0.1)  # Send data every 100ms for better position tracking
                
            print('lost connection')
    except Exception as e:
        print('Error: ', e)
    finally:
        p.disconnect()
        print('closing up')
         
peripheral('Car')
