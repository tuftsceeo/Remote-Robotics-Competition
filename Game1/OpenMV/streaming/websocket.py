import network
import socket
import ssl
import time
import binascii
import json
import random
import gc

class Microwebsocket():
    def __init__(self, WS_HOST, WS_PORT, WS_PATH):
        self.ssl_sock = None
        self.WS_HOST = WS_HOST
        self.WS_PORT = WS_PORT
        self.WS_PATH = WS_PATH

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print("TCP_NODELAY enabled")
        except:
            print("TCP_NODELAY not supported")
        return sock

    def get_random_bytes(self, length):
        """Generate random bytes compatible with OpenMV"""
        return bytes([random.randint(0, 255) for _ in range(length)])

    def connect(self):
        try:
            print(f"Connecting to {self.WS_HOST}:{self.WS_PORT}...")

            sock = self.create_socket()
            sock.settimeout(10)  # Connection timeout

            # Connect
            addr_info = socket.getaddrinfo(self.WS_HOST, self.WS_PORT, 0, socket.SOCK_STREAM)
            addr = addr_info[0][-1]
            sock.connect(addr)
            sock.settimeout(2.0)

            # SSL handshake
            self.ssl_sock = ssl.wrap_socket(
                sock,
                server_side=False,
                cert_reqs=ssl.CERT_NONE,
                server_hostname=self.WS_HOST,
                do_handshake=True
            )

            print("SSL connection established")

            # WebSocket handshake
            random_bytes = self.get_random_bytes(16)
            key = binascii.b2a_base64(random_bytes).decode().strip()
            handshake = (
                f"GET {self.WS_PATH} HTTP/1.1\r\nHost: {self.WS_HOST}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\nOrigin: https://esp32-device\r\n\r\n")

            print("Sending WebSocket handshake...")
            self.ssl_sock.write(handshake.encode())

            # Read handshake response
            response_bytes = b""
            while b"\r\n\r\n" not in response_bytes:
                chunk = self.ssl_sock.read(1024)
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
                return self.ssl_sock
            else:
                print("WebSocket handshake failed")
                self.ssl_sock.close()
                return None

        except Exception as e:
            print(f"Connection error: {e}")
            return None

    def check(self):
        # Check connection
        if not self.ssl_sock or not self.ping():
            if self.ssl_sock:
                try:
                    self.ssl_sock.close()
                except:
                    pass
            print("Connecting...")
            self.ssl_sock = self.connect()

            print("Connected" if self.ssl_sock else "Connection failed, waiting...")
            time.sleep(1)
        return True if self.ssl_sock else False

    def send(self, message):
        try:
            json_data = json.dumps(message)
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
            mask = self.get_random_bytes(4)
            frame.extend(mask)

            # Mask payload
            for i, byte in enumerate(payload):
                frame.append(byte ^ mask[i % 4])

            self.ssl_sock.write(frame)
            return True

        except Exception as e:
            print(f"Send error: {e}")
            return False

    def ping(self):
        try:
            # Try to send a small ping frame
            ping_frame = bytearray([0x89, 0x80])  # Ping frame with mask bit
            ping_frame.extend(self.get_random_bytes(4))  # Mask key
            self.ssl_sock.write(ping_frame)
            return True
        except:
            return False
