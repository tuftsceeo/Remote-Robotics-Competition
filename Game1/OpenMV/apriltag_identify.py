import sensor
import time
import math
import json
from BLE_CEEO import Yell, Listen

# === Configuration ===
TAG_SIZE = 0.06  # Tag size in meters (6cm)

# === Camera setup ===
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
sensor.skip_frames(time=2000)

# === Distance calculation ===
def calculate_distance(tag):
    tag_width_pixels = tag.w
    tag_height_pixels = tag.h
    tag_size_pixels = (tag_width_pixels + tag_height_pixels) / 2

    if tag_size_pixels > 0:
        focal_pixels = 2.8 * (sensor.width() / 3.6)  # approximate focal length
        distance = (TAG_SIZE * focal_pixels) / tag_size_pixels
        return distance
    return 0

# === Tag Detection ===
def grabData():
    message = {
        "detected": False,
        "tag_id": 0,
        "x": 0,
        "y": 0,
        "distance": 0,
        "rotation": 0,
        "area": 0
    }

    img = sensor.snapshot()
    tags = img.find_apriltags()

    if tags:
        # Find the largest tag
        tag = max(tags, key=lambda t: t.w * t.h)

        message["detected"] = True
        message["tag_id"] = tag.id
        message["x"] = tag.cx
        message["y"] = tag.cy
        message["distance"] = calculate_distance(tag)
        message["rotation"] = int(math.degrees(tag.rotation))
        message["area"] = tag.w * tag.h

        # Draw detection visualization
        img.draw_rectangle(tag.rect, color=(255, 0, 0))
        img.draw_cross(tag.cx, tag.cy, color=(0, 255, 0))
        img.draw_string(tag.cx - 20, tag.cy - 30, "ID:" + str(tag.id), color=(255, 255, 255))
        img.draw_string(tag.cx - 20, tag.cy - 20, "{:.2f}m".format(message["distance"]), color=(255, 255, 255))

    return str(json.dumps(message))

# === BLE Peripheral Loop ===
def callback(data):
    print(data.decode())

def peripheral(name):
    try:
        print('waiting ...')
        p = Yell(name, interval_us=30000, verbose=False)
        if p.connect_up():
            p.callback = callback
            print('Connected')
            time.sleep(1)
            while p.is_connected:
                p.send(grabData())
                time.sleep(0.01)
            print('lost connection')
    except Exception as e:
        print('Error:', e)
    finally:
        p.disconnect()
        print('closing up')

# === Run ===
peripheral('OPENMV')
