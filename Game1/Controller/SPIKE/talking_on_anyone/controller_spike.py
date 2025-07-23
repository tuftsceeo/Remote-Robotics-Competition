import time
from hub import motion_sensor
from BLE_CEEO import Yell, Listen
import time
import json

# === Configuration ===
SAMPLES_PER_SEND = 5  # Number of samples to average before sending (over 0.25s)

# === Global variables ===
x_buffer = []
y_buffer = []

def sample_and_average():
    """Take multiple samples over ~0.25s and return averaged values"""
    global x_buffer, y_buffer
    
    # Clear buffers
    x_buffer = []
    y_buffer = []
    
    # Take multiple samples over the available time (before BLE send)
    for i in range(SAMPLES_PER_SEND):
        try:
            (x, y, z) = motion_sensor.acceleration()
            x_buffer.append(x)
            y_buffer.append(y)
            time.sleep(0.05)  # 5 samples × 0.05s = 0.25s total
        except Exception as e:
            print("IMU sampling error:", e)
    
    # Calculate averages
    if len(x_buffer) > 0:
        x_avg = sum(x_buffer) / len(x_buffer)
        y_avg = sum(y_buffer) / len(y_buffer)
        return int(x_avg), int(y_avg)
    else:
        return 0, 0

def grabData():
    """Get averaged IMU data"""
    x_avg, y_avg = sample_and_average()
    message = {'x': x_avg, 'y': y_avg}
    return str(json.dumps(message))

def peripheral(name): 
    try:
        print('waiting ...')
        p = Yell(name, interval_us=30000, verbose=False)
        if p.connect_up():
            print('Connected')
            time.sleep(1)
            while p.is_connected:
                data = grabData()
                p.send(data)
                print("Sent:", data)
                time.sleep(0.3)
            print('lost connection')
    except Exception as e:
        print('Error:', e)
    finally:
        p.disconnect()
        print('closing up')
         
peripheral('Controller_spike')
