import network
import time
import sensor
import ubinascii
import gc
import websocket

import secret

# WiFi credentials
WIFI_SSID = secret.wifi['username']
WIFI_PASSWORD = secret.wifi['password']

# WebSocket server details
WS_HOST = "chrisrogers.pyscriptapps.com"
WS_PORT = 443
WS_PATH = "/talking-on-a-channel/api/channels/hackathon"

wait_time = 0.1

websock = websocket.Microwebsocket(WS_HOST, WS_PORT, WS_PATH)

def init_camera():
    print("Initializing camera...")
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    
    sensor.set_auto_gain(True)  #False, gain_db=10)
    sensor.set_auto_exposure(True)  #False, exposure_us=8000)
    sensor.skip_frames(time=500)
    
def snap():
    try:
        img = sensor.snapshot()
        jpeg_bytes = img.compress(quality=45)
        base64_str = ubinascii.b2a_base64(jpeg_bytes).decode('utf-8').strip()
        
        #print(f"Image: {len(jpeg_bytes)}B -> {len(base64_str)}B base64")
        print('.',end = '')
        return base64_str
        
    except Exception as e:
        print(f"Image capture error: {e}")
        return None

wlan = network.WLAN(network.STA_IF)

def connect_wifi():
    print("Connecting to WiFi...")
    wlan.active(True)
    
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        timeout = 10000
        start_time = time.ticks_ms()
        
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), start_time) > timeout:
                print("WiFi timeout!")
                return False
            time.sleep_ms(200)
    
    print(f"WiFi connected: {wlan.ifconfig()}")
    return True

def main():
    init_camera()
    if not connect_wifi():
        print("WiFi connection failed!")
        return
    
    try:
        counter = 0
        while True:
            if not websock.check():
                continue
            
            base64_image = snap()
            if base64_image:
                image_message = {
                    "topic": "/camera",
                    "value": base64_image,
                    "timestamp": time.ticks_ms()
                }
                #print(f"Sending image ...")
                
                if not websock.send(image_message):
                    print(f"Failed to send image ")
                    websock.ssl_sock.close()
                    websock.ssl_sock = None
                    continue
            
            # Wait between images
            time.sleep(wait_time)
            counter += 1
            if not (counter % 10): # garbage collect every 10 iterations
                gc.collect()
    
    except KeyboardInterrupt:
        print("Stopping transmission...")
    
    except Exception as e:
        print(f"Main error: {e}")
    
    finally:
        if websock.ssl_sock:
            try:
                websock.ssl_sock.close()
                wlan.disconnect()
                wlan.active(False)
            except:
                pass
        print("Connection closed")
main()
