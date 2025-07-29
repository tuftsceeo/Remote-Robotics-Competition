import network
import socket
import ssl
import time
import hashlib
import binascii
import os
import json
import sensor
import image
import ubinascii
import gc

# WiFi credentials
WIFI_SSID = ""
WIFI_PASSWORD = ""

# WebSocket server details
WS_HOST = "chrisrogers.pyscriptapps.com"
WS_PORT = 443
WS_PATH = "/talking-on-a-channel/api/channels/hackathon"

def init_camera_optimized():
    print("Initializing camera...")
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    
    sensor.set_auto_gain(False, gain_db=10)
    sensor.set_auto_exposure(False, exposure_us=8000)
    sensor.skip_frames(time=500)
    
def connect_wifi_simple():
    print("Connecting to WiFi...")
    wlan = network.WLAN(network.STA_IF)
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

def create_optimized_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        print("TCP_NODELAY enabled")
    except:
        print("TCP_NODELAY not supported")
    
    return sock

def connect_websocket():
    try:
        print(f"Connecting to {WS_HOST}:{WS_PORT}...")
        
        sock = create_optimized_socket()
        sock.settimeout(10)  # Connection timeout
        
        # Connect
        addr_info = socket.getaddrinfo(WS_HOST, WS_PORT, 0, socket.SOCK_STREAM)
        addr = addr_info[0][-1]
        sock.connect(addr)
        sock.settimeout(2.0)
        
        # SSL handshake
        ssl_sock = ssl.wrap_socket(
            sock,
            server_side=False,
            cert_reqs=ssl.CERT_NONE,
            server_hostname=WS_HOST,
            do_handshake=True
        )
        
        print("SSL connection established")
        
        # WebSocket handshake
        key = binascii.b2a_base64(os.urandom(16)).decode().strip()
        handshake = (
            f"GET {WS_PATH} HTTP/1.1\r\n"
            f"Host: {WS_HOST}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "Origin: https://esp32-device\r\n"
            "\r\n"
        )
        
        print("Sending WebSocket handshake...")
        ssl_sock.write(handshake.encode())
        
        # Read handshake response
        response_bytes = b""
        while b"\r\n\r\n" not in response_bytes:
            chunk = ssl_sock.read(1024)
            if not chunk:
                break
            response_bytes += chunk
        
        # Decode response safely
        try:
            response = response_bytes.decode('utf-8')
        except:
            response = ''.join([chr(b) if 32 <= b <= 126 else '?' for b in response_bytes])
        
        if "101 Switching Protocols" in response:
            print("WebSocket connected successfully!")
            return ssl_sock
        else:
            print("WebSocket handshake failed")
            ssl_sock.close()
            return None
            
    except Exception as e:
        print(f"Connection error: {e}")
        return None

def capture_image_optimized():
    try:
        img = sensor.snapshot()
        jpeg_bytes = img.compress(quality=45)
        base64_str = ubinascii.b2a_base64(jpeg_bytes).decode('utf-8').strip()
        
        print(f"Image: {len(jpeg_bytes)}B -> {len(base64_str)}B base64")
        return base64_str
        
    except Exception as e:
        print(f"Image capture error: {e}")
        return None

def send_websocket_message(ssl_sock, message_dict):
    try:
        json_data = json.dumps(message_dict)
        payload = json_data.encode('utf-8')
        length = len(payload)
        
        if length > 50000:
            print(f"Message too large: {length} bytes")
            return False
        
        # Create WebSocket frame
        frame = bytearray()
        frame.append(0x81)  # FIN bit set + text frame opcode
        
        # Add payload length with mask bit
        if length <= 125:
            frame.append(0x80 | length)
        elif length < 65536:
            frame.append(0x80 | 126)
            frame.extend(length.to_bytes(2, 'big'))
        else:
            frame.append(0x80 | 127)
            frame.extend(length.to_bytes(8, 'big'))
        
        # Add masking key
        mask = os.urandom(4)
        frame.extend(mask)
        
        # Mask payload
        for i, byte in enumerate(payload):
            frame.append(byte ^ mask[i % 4])
        
        ssl_sock.write(frame)
        return True
        
    except Exception as e:
        print(f"Send error: {e}")
        return False

def send_heartbeat(ssl_sock, connection_count):
    heartbeat = {
        "topic": "/camera/heartbeat",
        "value": "alive",
        "connection": connection_count,
        "memory": gc.mem_free()
    }
    return send_websocket_message(ssl_sock, heartbeat)

def is_socket_alive(ssl_sock):
    try:
        # Try to send a small ping frame
        ping_frame = bytearray([0x89, 0x80])  # Ping frame with mask bit
        ping_frame.extend(os.urandom(4))  # Mask key
        ssl_sock.write(ping_frame)
        return True
    except:
        return False

def main_simplified():
    init_camera_optimized()
    
    # Connect to WiFi
    if not connect_wifi_simple():
        print("WiFi connection failed!")
        return
    
    ssl_sock = None
    image_count = 0
    connection_count = 0
    last_heartbeat = 0
    
    try:
        while True:
            # Check connection
            if not ssl_sock or not is_socket_alive(ssl_sock):
                if ssl_sock:
                    try:
                        ssl_sock.close()
                    except:
                        pass
                
                print("Connecting...")
                ssl_sock = connect_websocket()
                
                if ssl_sock:
                    connection_count += 1
                    print(f"Connected! Connection #{connection_count}")
                    time.sleep(1)
                    last_heartbeat = time.ticks_ms()
                else:
                    print("Connection failed, waiting...")
                    time.sleep(3)
                    continue
            
            # Send heartbeat every 30 seconds
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_heartbeat) > 30000:
                print("Sending heartbeat...")
                if send_heartbeat(ssl_sock, connection_count):
                    last_heartbeat = current_time
                else:
                    print("Heartbeat failed")
                    ssl_sock.close()
                    ssl_sock = None
                    continue
            
            # Capture and send image
            base64_image = capture_image_optimized()
            
            if base64_image:
                image_message = {
                    "topic": "/camera",
                    "value": base64_image,
                    "image_id": image_count,
                    "connection": connection_count,
                    "timestamp": time.ticks_ms()
                }
                
                print(f"Sending image #{image_count}...")
                
                if send_websocket_message(ssl_sock, image_message):
                    print(f"Image #{image_count} sent! (Conn #{connection_count})")
                    image_count += 1
                else:
                    print(f"Failed to send image #{image_count}")
                    ssl_sock.close()
                    ssl_sock = None
                    continue
            
            # Wait between images
            # time.sleep(0.05)
            
            # Periodic cleanup
            if image_count % 5 == 0:
                gc.collect()
    
    except KeyboardInterrupt:
        print("Stopping transmission...")
    
    except Exception as e:
        print(f"Main error: {e}")
        import sys
        sys.print_exception(e)
    
    finally:
        if ssl_sock:
            try:
                ssl_sock.close()
            except:
                pass
        print("Connection closed")

if __name__ == "__main__":
    main_simplified()
