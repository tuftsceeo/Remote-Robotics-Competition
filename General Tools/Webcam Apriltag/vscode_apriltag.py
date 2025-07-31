import cv2
import numpy as np
import websocket
import ssl
import json
import time
import math
import tkinter as tk
from tkinter import ttk
from threading import Thread, Event
import queue
from collections import deque
 
# WebSocket channel configuration
uri = "wss://chrisrogers.pyscriptapps.com/talking-on-a-channel/api/channels/hackathon"
 
class wss_CEEO():
    def __init__(self, url):
        self.url = url
        self.ws = None
        self.connected = False
        self.last_activity = time.time()
        self.keepalive_interval = 30  # Send keepalive every 30 seconds
        self.connection_timeout = 60  # Consider connection dead after 60 seconds of no activity
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # Initial delay between reconnection attempts
        
        # Keepalive thread management
        self.keepalive_thread = None
        self.keepalive_running = False
        self.connection_event = Event()
        
        # Connect and start keepalive
        self.connect()
        self.start_keepalive()
 
    def connect(self):
        """Establish persistent WebSocket connection with retry logic"""
        try:
            if self.ws:
                try:
                    self.ws.close()
                except:
                    pass
                    
            print(f"Attempting to connect to WebSocket... (attempt {self.reconnect_attempts + 1})")
            self.ws = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
            self.ws.settimeout(10)  # Set timeout for connection
            self.ws.connect(self.url)
            
            self.connected = True
            self.last_activity = time.time()
            self.reconnect_attempts = 0
            self.connection_event.set()
            print("✓ WebSocket connected successfully")
            
        except Exception as e:
            print(f"✗ WebSocket connection error: {e}")
            self.connected = False
            self.connection_event.clear()
            self.reconnect_attempts += 1
            
            if self.reconnect_attempts < self.max_reconnect_attempts:
                delay = min(self.reconnect_delay * self.reconnect_attempts, 60)  # Exponential backoff, max 60s
                print(f"Will retry connection in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Max reconnection attempts reached. Will continue trying with longer delays...")
                time.sleep(60)  # Wait longer before retrying
                self.reconnect_attempts = 0  # Reset counter for continued attempts

    def start_keepalive(self):
        """Start the keepalive thread"""
        if not self.keepalive_running:
            self.keepalive_running = True
            self.keepalive_thread = Thread(target=self._keepalive_worker, daemon=True)
            self.keepalive_thread.start()
            print("Keepalive thread started")

    def _keepalive_worker(self):
        """Background thread for connection monitoring and keepalive"""
        while self.keepalive_running:
            try:
                current_time = time.time()
                
                # Check if connection is stale
                if self.connected and (current_time - self.last_activity) > self.connection_timeout:
                    print("Connection appears stale, forcing reconnection...")
                    self.connected = False
                    self.connection_event.clear()
                
                # Reconnect if needed
                if not self.connected:
                    self.connect()
                
                # Send keepalive if connected and it's time
                elif (current_time - self.last_activity) > self.keepalive_interval:
                    self._send_keepalive()
                
                # Wait before next check
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"Keepalive worker error: {e}")
                time.sleep(10)  # Wait longer on error

    def _send_keepalive(self):
        """Send a keepalive message to maintain connection"""
        try:
            if self.ws and self.connected:
                keepalive_msg = {
                    'topic': '/system/keepalive',
                    'value': {'timestamp': time.time(), 'type': 'heartbeat'}
                }
                self.ws.send(json.dumps(keepalive_msg))
                self.last_activity = time.time()
                print("♥ Keepalive sent")
                return True
        except Exception as e:
            print(f"Keepalive send error: {e}")
            self.connected = False
            self.connection_event.clear()
            return False

    def is_healthy(self):
        """Check if the connection is healthy"""
        if not self.connected:
            return False
        
        # Test the connection by trying to send a ping
        try:
            if self.ws:
                # Try to get the connection state (this might fail if connection is dead)
                return True
        except:
            self.connected = False
            self.connection_event.clear()
            return False
        
        return True

    def send_message(self, message, retry_on_failure=True):
        """Send a single message using persistent connection with retry logic"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            # Ensure we're connected
            if not self.connected:
                print("Not connected, attempting to reconnect...")
                self.connect()
                if not self.connected:
                    retry_count += 1
                    continue
            
            try:
                if self.ws:
                    self.ws.send(json.dumps(message))
                    self.last_activity = time.time()
                    return True
                    
            except Exception as e:
                print(f"Send error (attempt {retry_count + 1}): {e}")
                self.connected = False
                self.connection_event.clear()
                
                if retry_on_failure and retry_count < max_retries - 1:
                    retry_count += 1
                    time.sleep(1)  # Brief delay before retry
                    continue
                else:
                    break
        
        print("Failed to send message after retries")
        return False

    def send_multiple(self, messages, retry_on_failure=True):
        """Send multiple messages using persistent connection with retry logic"""
        if not messages:
            return True
            
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            # Ensure we're connected
            if not self.connected:
                print("Not connected, attempting to reconnect...")
                self.connect()
                if not self.connected:
                    retry_count += 1
                    continue
            
            try:
                if self.ws:
                    successful_sends = 0
                    for message in messages:
                        self.ws.send(json.dumps(message))
                        successful_sends += 1
                    
                    self.last_activity = time.time()
                    print(f"✓ Successfully sent {successful_sends} messages")
                    return True
                    
            except Exception as e:
                print(f"Send multiple error (attempt {retry_count + 1}): {e}")
                self.connected = False
                self.connection_event.clear()
                
                if retry_on_failure and retry_count < max_retries - 1:
                    retry_count += 1
                    time.sleep(1)  # Brief delay before retry
                    continue
                else:
                    break
        
        print("Failed to send multiple messages after retries")
        return False

    def get_connection_status(self):
        """Get detailed connection status"""
        return {
            'connected': self.connected,
            'last_activity': self.last_activity,
            'time_since_activity': time.time() - self.last_activity,
            'reconnect_attempts': self.reconnect_attempts,
            'keepalive_running': self.keepalive_running
        }

    def close(self):
        """Close the WebSocket connection and cleanup"""
        print("Closing WebSocket connection...")
        self.keepalive_running = False
        
        if self.keepalive_thread:
            self.keepalive_thread.join(timeout=2)
            
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
            
        self.connected = False
        self.connection_event.clear()
        print("WebSocket connection closed")
 
class PerspectiveSelector:
    def __init__(self, frame_shape):
        self.points = []
        self.frame_shape = frame_shape
        self.selecting = False
        self.transform_matrix = None
        # Use same aspect ratio as original frame for better scaling
        self.output_size = (frame_shape[1], frame_shape[0])  # (width, height)
 
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse clicks for point selection"""
        if event == cv2.EVENT_LBUTTONDOWN and self.selecting:
            if len(self.points) < 4:
                self.points.append((x, y))
                print(f"Point {len(self.points)}: ({x}, {y})")
 
                if len(self.points) == 4:
                    self.calculate_transform()
                    self.selecting = False
                    print("All 4 points selected! Perspective transformation ready.")
 
    def calculate_transform(self):
        """Calculate perspective transformation matrix from selected points"""
        if len(self.points) != 4:
            return
 
        # Order points: top-left, top-right, bottom-right, bottom-left
        points = np.array(self.points, dtype=np.float32)
 
        # Simple ordering based on sum and difference of coordinates
        sum_coords = points.sum(axis=1)
        diff_coords = np.diff(points, axis=1)
 
        # Top-left has smallest sum, bottom-right has largest sum
        # Top-right has smallest difference (x-y), bottom-left has largest difference
        ordered_points = np.zeros((4, 2), dtype=np.float32)
        ordered_points[0] = points[np.argmin(sum_coords)]  # top-left
        ordered_points[2] = points[np.argmax(sum_coords)]  # bottom-right
        ordered_points[1] = points[np.argmin(diff_coords)]  # top-right
        ordered_points[3] = points[np.argmax(diff_coords)]  # bottom-left
 
        # Define destination points (rectangle)
        dst_points = np.array([
            [0, 0],
            [self.output_size[0] - 1, 0],
            [self.output_size[0] - 1, self.output_size[1] - 1],
            [0, self.output_size[1] - 1]
        ], dtype=np.float32)
 
        # Calculate transformation matrix
        self.transform_matrix = cv2.getPerspectiveTransform(ordered_points, dst_points)
        print("Perspective transformation matrix calculated")
 
    def apply_transform(self, frame):
        """Apply perspective transformation to frame"""
        if self.transform_matrix is not None:
            warped = cv2.warpPerspective(frame, self.transform_matrix, self.output_size)
            return warped
        return frame
 
    def draw_selection(self, frame):
        """Draw selection points and lines on frame"""
        # Draw points
        for i, point in enumerate(self.points):
            cv2.circle(frame, point, 8, (0, 255, 0), -1)
            cv2.putText(frame, str(i+1), (point[0] + 10, point[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
 
        # Draw lines between points
        if len(self.points) > 1:
            for i in range(len(self.points)):
                start_point = self.points[i]
                end_point = self.points[(i + 1) % len(self.points)]
                cv2.line(frame, start_point, end_point, (255, 0, 0), 2)
 
        # Draw selection instructions
        if self.selecting:
            instruction_text = f"Click {4 - len(self.points)} more corners"
            cv2.putText(frame, instruction_text, (10, frame.shape[0] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
 
        return frame
 
    def reset(self):
        """Reset selection"""
        self.points = []
        self.transform_matrix = None
        self.selecting = False
        print("Selection reset")
 
    def start_selection(self):
        """Start point selection mode"""
        self.reset()
        self.selecting = True
        print("Click 4 corners of the area you want to crop (in any order)")
 
class AprilTagDetector:
    def __init__(self, channel_client):
        # Import and initialize AprilTag detector
        try:
            from pupil_apriltags import Detector
            self.detector = Detector(families="tag36h11",
                                   nthreads=2,  # Reduced threads to prevent CPU overload
                                   quad_decimate=1.5,  # Increased to improve performance
                                   quad_sigma=0.0,
                                   refine_edges=1,
                                   decode_sharpening=0.25,
                                   debug=0)
            print("Using pupil_apriltags library")
        except ImportError:
            try:
                import apriltag
                self.detector = apriltag.Detector()
                print("Using apriltag library")
            except ImportError:
                raise ImportError("Neither pupil_apriltags nor apriltag library found. Please install one of them.")
 
        # Initialize webcam with optimized settings
        print("Initializing webcam...")
        self.cap = cv2.VideoCapture(0) # webcam index - change if necessary (index starts at 0)
        print("Webcam initialized.")
 
        # Set camera properties for better performance
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Reduced resolution
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Reduced resolution
        self.cap.set(cv2.CAP_PROP_FPS, 30)  # More realistic FPS
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to minimize lag
 
        # Get actual resolution and FPS
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"Camera resolution: {self.width}x{self.height} @ {self.fps} FPS")
 
        # Initialize perspective selector
        self.perspective_selector = PerspectiveSelector((self.height, self.width))
 
        # Pre-calculate scaling factors
        self.scale_x = 1920 / self.width
        self.scale_y = 1080 / self.height
 
        # Channel client for sending data
        self.channel_client = channel_client
 
        # Topic selection
        self.selected_topic = "Car_Location_1"
 
        # Rate limiting for WebSocket sends
        self.last_send_time = 0
        self.send_interval = 0.033  # ~30 FPS for network updates
 
        # Message queue for asynchronous sending
        self.message_queue = queue.Queue()
        self.sender_thread = None
        self.sender_running = False
 
        # Performance tracking
        self.frame_count = 0
        self.start_time = time.time()
        self.fps_history = deque(maxlen=30)  # Rolling average
 
        # Cropping mode
        self.crop_mode_enabled = False
 
        # Add running flag for main loop control
        self.running = False
        
        # Connection monitoring
        self.last_connection_check = time.time()
        self.connection_check_interval = 10  # Check connection every 10 seconds
 
    def start_sender_thread(self):
        """Start the asynchronous message sender thread"""
        self.sender_running = True
        self.sender_thread = Thread(target=self._sender_worker)
        self.sender_thread.daemon = True
        self.sender_thread.start()
        print("Sender thread started")
 
    def _sender_worker(self):
        """Background thread for sending messages with enhanced error handling"""
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        while self.sender_running:
            try:
                messages = self.message_queue.get(timeout=0.1)
                if messages:
                    print(f"Sending {len(messages)} messages")
                    success = self.channel_client.send_multiple(messages)
                    
                    if success:
                        print("✓ Messages sent successfully")
                        consecutive_failures = 0  # Reset failure counter
                    else:
                        consecutive_failures += 1
                        print(f"✗ Failed to send messages (failure #{consecutive_failures})")
                        
                        # If too many consecutive failures, wait longer
                        if consecutive_failures >= max_consecutive_failures:
                            print(f"Too many consecutive failures, waiting 30 seconds...")
                            time.sleep(30)
                            consecutive_failures = 0  # Reset counter
                            
                self.message_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Sender thread error: {e}")
                consecutive_failures += 1
                time.sleep(1)  # Brief pause on error

    def check_connection_health(self):
        """Periodically check and report connection health"""
        current_time = time.time()
        if current_time - self.last_connection_check > self.connection_check_interval:
            status = self.channel_client.get_connection_status()
            if not status['connected']:
                print(f"⚠ Connection lost - attempting reconnection...")
            elif status['time_since_activity'] > 45:
                print(f"⚠ No activity for {status['time_since_activity']:.1f}s - connection may be stale")
            
            self.last_connection_check = current_time

    def stop_sender_thread(self):
        """Stop the sender thread"""
        self.sender_running = False
        if self.sender_thread:
            self.sender_thread.join()
 
    def set_topic(self, topic):
        """Set the topic for sending data"""
        self.selected_topic = topic
        print(f"Topic changed to: {topic}")
 
    def toggle_crop_mode(self):
        """Toggle perspective crop mode"""
        self.crop_mode_enabled = not self.crop_mode_enabled
        if self.crop_mode_enabled:
            print("Crop mode enabled - cropped view will be used for detection")
            # Update scaling factors for cropped view
            # Use the actual output size of the perspective transformation
            crop_width, crop_height = self.perspective_selector.output_size
            self.scale_x = 1920 / crop_width
            self.scale_y = 1080 / crop_height
            print(f"Crop scaling factors: x={self.scale_x:.3f}, y={self.scale_y:.3f}")
            print(f"Crop output size: {crop_width}x{crop_height}")
        else:
            print("Crop mode disabled - full camera view will be used")
            # Reset scaling factors to original camera view
            self.scale_x = 1920 / self.width
            self.scale_y = 1080 / self.height
            print(f"Full view scaling factors: x={self.scale_x:.3f}, y={self.scale_y:.3f}")
 
    def calculate_rotation_fast(self, corners):
        """Optimized rotation calculation"""
        if corners is None or len(corners) < 4:
            return 0.0
 
        # Use numpy operations for speed
        top_edge = corners[2] - corners[3]  # top-right - top-left
        rotation = math.degrees(math.atan2(top_edge[1], top_edge[0]))
 
        # Normalize to 0-360 degrees
        return rotation % 360
 
    def detect_apriltags(self, frame):
        """Detect AprilTags in the frame and return their coordinates"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
 
        # Detect AprilTags
        try:
            tags = self.detector.detect(gray, estimate_tag_pose=False, 
                                       camera_params=None, tag_size=None)
        except TypeError:
            tags = self.detector.detect(gray)
 
        detected_tags = []
        for tag in tags:
            # Get center coordinates
            if hasattr(tag, 'center'):
                center_x, center_y = tag.center
            else:
                # Calculate center from corners
                corners = tag.corners if hasattr(tag, 'corners') else tag.pose_R
                center_x = np.mean(corners[:, 0])
                center_y = np.mean(corners[:, 1])
 
            # Fast scaling using pre-calculated factors
            scaled_x = int(center_x * self.scale_x)
            scaled_y = int(center_y * self.scale_y)
 
            # Clamp coordinates
            scaled_x = max(0, min(1920, scaled_x))
            scaled_y = max(0, min(1080, scaled_y))
 
            # Get tag ID
            tag_id = getattr(tag, 'tag_id', getattr(tag, 'id', 0))
 
            # Get corners and calculate rotation
            corners = tag.corners if hasattr(tag, 'corners') else None
            rotation = self.calculate_rotation_fast(corners) if corners is not None else 0.0
 
            detected_tags.append({
                'tag_id': tag_id,
                'x': scaled_x,
                'y': scaled_y,
                'rotation': round(rotation, 1),  # Less precision for performance
                'center_actual': (int(center_x), int(center_y)),
                'corners': corners
            })
 
        return detected_tags
 
    def send_tag_coordinates(self, tags):
        """Send tag coordinates with rate limiting - NO MOVEMENT FILTERING"""
        current_time = time.time()
 
        # Rate limiting
        if current_time - self.last_send_time < self.send_interval:
            return
 
        messages = []
        for tag in tags:
            # Send ALL tags regardless of movement
            message = {
                'topic': f'/{self.selected_topic}/All',
                'value': {'x': tag['x'], 'y': tag['y'], 'rotation': tag['rotation']}
            }
            messages.append(message)
 
        # Send messages asynchronously
        if messages:
            try:
                self.message_queue.put_nowait(messages)
                print(f"Queued {len(messages)} messages")
                self.last_send_time = current_time
            except queue.Full:
                print("Message queue full, dropping messages")
 
    def draw_detections(self, frame, tags):
        """Draw detected AprilTags on the frame"""
        def draw_text_with_outline(img, text, pos, font, scale, color, thickness):
            # Draw black outline
            cv2.putText(img, text, pos, font, scale, (0, 0, 0), thickness + 1)
            # Draw colored text on top
            cv2.putText(img, text, pos, font, scale, color, thickness)
 
        for tag in tags:
            center = tag['center_actual']
 
            # Draw tag corners if available
            if tag['corners'] is not None:
                corners = tag['corners'].astype(int)
                cv2.polylines(frame, [corners], True, (0, 255, 0), 2)
 
                # Draw rotation indicator
                top_center = ((corners[2] + corners[3]) / 2).astype(int)
                cv2.arrowedLine(frame, center, tuple(top_center), (255, 0, 0), 2)
 
            # Draw center point
            cv2.circle(frame, center, 3, (0, 0, 255), -1)
 
            # Draw tag ID with outline for visibility
            draw_text_with_outline(frame, f"ID: {tag['tag_id']}", 
                                 (center[0] - 15, center[1] - 25),
                                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
 
            # Draw scaled coordinates with outline
            coord_text = f"({tag['x']}, {tag['y']})"
            draw_text_with_outline(frame, coord_text,
                                 (center[0] - 30, center[1] + 15),
                                 cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
 
            # Draw rotation with outline
            rotation_text = f"R: {tag['rotation']:.0f}°"
            draw_text_with_outline(frame, rotation_text,
                                 (center[0] - 30, center[1] + 30),
                                 cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
 
        return frame
 
    def calculate_fps(self):
        """Calculate smoothed FPS"""
        current_time = time.time()
        if hasattr(self, 'last_frame_time'):
            frame_time = current_time - self.last_frame_time
            if frame_time > 0:
                instant_fps = 1.0 / frame_time
                self.fps_history.append(instant_fps)
 
        self.last_frame_time = current_time
 
        # Return smoothed FPS
        if self.fps_history:
            return sum(self.fps_history) / len(self.fps_history)
        return 0
 
    def start_detection(self):
        """Start the detection process - now runs on main thread"""
        print("Starting AprilTag detection...")
        print("Controls:")
        print("  'q' - Quit")
        print("  's' - Start area selection")
        print("  'r' - Reset selection")
        print("  'c' - Toggle crop mode")
        print("  'f' - Toggle fullscreen")
 
        # Set up OpenCV window and mouse callback - MUST BE ON MAIN THREAD
        cv2.namedWindow('AprilTag Detection', cv2.WINDOW_NORMAL)
        cv2.setMouseCallback('AprilTag Detection', self.perspective_selector.mouse_callback)
 
        # Start the sender thread
        self.start_sender_thread()
        self.running = True
 
    def process_frame(self):
        """Process a single frame - called from main thread"""
        if not self.running:
            return False
 
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to capture frame")
            return False
            
        # Check connection health periodically
        self.check_connection_health()
 
        # Store original frame for selection overlay
        display_frame = frame.copy()
        detection_frame = frame.copy()
 
        # Apply perspective transformation if enabled and available
        if self.crop_mode_enabled and self.perspective_selector.transform_matrix is not None:
            detection_frame = self.perspective_selector.apply_transform(frame)
            # For display, we'll use the cropped frame
            display_frame = detection_frame.copy()
 
        # Detect AprilTags (on appropriate frame)
        tags = self.detect_apriltags(detection_frame)
 
        # Send coordinates (rate limited but NO movement filtering)
        if tags:
            self.send_tag_coordinates(tags)
 
        # Draw detections on the display frame
        display_frame = self.draw_detections(display_frame, tags)
 
        # If not in crop mode, draw selection overlay on original frame
        if not self.crop_mode_enabled:
            display_frame = self.perspective_selector.draw_selection(display_frame)
 
        # Calculate FPS
        current_fps = self.calculate_fps()
 
        # Add info overlay with black outline for better visibility
        def draw_text_with_outline(img, text, pos, font, scale, color, thickness):
            # Draw black outline
            cv2.putText(img, text, pos, font, scale, (0, 0, 0), thickness + 2)
            # Draw colored text on top
            cv2.putText(img, text, pos, font, scale, color, thickness)
 
        draw_text_with_outline(display_frame, f"FPS: {current_fps:.1f}", 
                             (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        draw_text_with_outline(display_frame, f"Tags: {len(tags)}", 
                             (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        draw_text_with_outline(display_frame, f"Topic: /{self.selected_topic}/All", 
                             (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
 
        # Add connection status indicator
        status = self.channel_client.get_connection_status()
        if status['connected']:
            connection_color = (0, 255, 0)  # Green
            connection_text = f"Connected ({status['time_since_activity']:.1f}s ago)"
        else:
            connection_color = (0, 0, 255)  # Red
            connection_text = f"Disconnected (attempt #{status['reconnect_attempts']})"
        
        draw_text_with_outline(display_frame, connection_text, 
                             (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, connection_color, 1)
 
        # Add crop mode status with dimensions
        if self.crop_mode_enabled:
            mode_text = f"CROP MODE ({display_frame.shape[1]}x{display_frame.shape[0]})"
            mode_color = (0, 255, 0)
        else:
            mode_text = f"FULL VIEW ({display_frame.shape[1]}x{display_frame.shape[0]})"
            mode_color = (0, 255, 255)
        draw_text_with_outline(display_frame, mode_text, 
                             (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, mode_color, 1)
 
        # Add scaling info
        scale_text = f"Scale: X={self.scale_x:.2f}, Y={self.scale_y:.2f}"
        draw_text_with_outline(display_frame, scale_text, 
                             (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
 
        # Add selection status
        if self.perspective_selector.selecting:
            draw_text_with_outline(display_frame, "SELECTING AREA - Click 4 corners", 
                                 (10, display_frame.shape[0] - 50), 
                                 cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        elif self.perspective_selector.transform_matrix is not None:
            draw_text_with_outline(display_frame, "Area selected - Press 'c' to toggle crop", 
                                 (10, display_frame.shape[0] - 50), 
                                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
 
        # Display frame
        cv2.imshow('AprilTag Detection', display_frame)
 
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            return False
        elif key == ord('s'):
            self.perspective_selector.start_selection()
        elif key == ord('r'):
            self.perspective_selector.reset()
            self.crop_mode_enabled = False
            # Reset scaling factors
            self.scale_x = 1920 / self.width
            self.scale_y = 1080 / self.height
        elif key == ord('c'):
            if self.perspective_selector.transform_matrix is not None:
                self.toggle_crop_mode()
            else:
                print("No area selected! Press 's' to start selection.")
        elif key == ord('f'):
            # Toggle fullscreen
            try:
                current_prop = cv2.getWindowProperty('AprilTag Detection', cv2.WND_PROP_FULLSCREEN)
                if current_prop == cv2.WINDOW_FULLSCREEN:
                    cv2.setWindowProperty('AprilTag Detection', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                else:
                    cv2.setWindowProperty('AprilTag Detection', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            except cv2.error:
                # Fullscreen toggle might not work on all systems
                pass
 
        return True
 
    def stop_detection(self):
        """Stop the detection process"""
        print("\nStopping detection...")
        self.running = False
        self.stop_sender_thread()
        self.cap.release()
        cv2.destroyAllWindows()
 
class DetectorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AprilTag Detector Control")
        self.root.geometry("300x320")  # Slightly larger to accommodate connection status
 
        # Create detector and channel client
        self.channel_client = wss_CEEO(uri)
        self.detector = AprilTagDetector(self.channel_client)
 
        # Create GUI elements
        self.setup_gui()
 
        # Start detector on main thread
        self.detector.start_detection()
 
    def setup_gui(self):
        # Title
        title_label = tk.Label(self.root, text="AprilTag Detector", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
 
        # Topic selection
        topic_frame = tk.Frame(self.root)
        topic_frame.pack(pady=10)
 
        tk.Label(topic_frame, text="Select Topic:", font=("Arial", 12)).pack()
 
        self.topic_var = tk.StringVar(value="Car_Location_1")
        topic_combo = ttk.Combobox(topic_frame, textvariable=self.topic_var,
                                  values=["Car_Location_1", "Car_Location_2"],
                                  state="readonly")
        topic_combo.pack(pady=5)
        topic_combo.bind('<<ComboboxSelected>>', self.on_topic_change)
 
        # Control buttons frame
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)
 
        # Area selection button
        select_button = tk.Button(control_frame, text="Select Area (S)", 
                                 command=self.start_selection,
                                 bg="blue", fg="white", font=("Arial", 10))
        select_button.pack(side=tk.LEFT, padx=5)
 
        # Reset button
        reset_button = tk.Button(control_frame, text="Reset (R)", 
                                command=self.reset_selection,
                                bg="orange", fg="white", font=("Arial", 10))
        reset_button.pack(side=tk.LEFT, padx=5)
 
        # Toggle crop button
        self.crop_button = tk.Button(control_frame, text="Toggle Crop (C)", 
                                    command=self.toggle_crop,
                                    bg="green", fg="white", font=("Arial", 10))
        self.crop_button.pack(side=tk.LEFT, padx=5)
 
        # Status
        self.status_label = tk.Label(self.root, text="Status: Running - Full View", 
                                    font=("Arial", 10))
        self.status_label.pack(pady=5)
 
        # Connection status
        self.connection_label = tk.Label(self.root, text="Connection: Connecting...", 
                                        font=("Arial", 10), fg="orange")
        self.connection_label.pack(pady=2)
 
        # Current topic display
        self.topic_label = tk.Label(self.root, text="Current Topic: /Car_Location_1/All", 
                                   font=("Arial", 10))
        self.topic_label.pack(pady=5)
 
        # Instructions
        instructions = tk.Label(self.root, 
                               text="1. Press 'Select Area' or 'S' key\n2. Click 4 corners in camera view\n3. Press 'Toggle Crop' or 'C' key", 
                               font=("Arial", 9), justify=tk.LEFT)
        instructions.pack(pady=5)
 
        # Quit button
        quit_button = tk.Button(self.root, text="Quit", command=self.quit_app,
                               bg="red", fg="white", font=("Arial", 12))
        quit_button.pack(pady=10)
 
    def on_topic_change(self, event):
        selected_topic = self.topic_var.get()
        self.detector.set_topic(selected_topic)
        self.topic_label.config(text=f"Current Topic: /{selected_topic}/All")
 
    def start_selection(self):
        self.detector.perspective_selector.start_selection()
        self.update_status()
 
    def reset_selection(self):
        self.detector.perspective_selector.reset()
        self.detector.crop_mode_enabled = False
        # Reset scaling factors
        self.detector.scale_x = 1920 / self.detector.width
        self.detector.scale_y = 1080 / self.detector.height
        print(f"Reset - Full view scaling factors: x={self.detector.scale_x:.3f}, y={self.detector.scale_y:.3f}")
        self.update_status()
 
    def toggle_crop(self):
        if self.detector.perspective_selector.transform_matrix is not None:
            self.detector.toggle_crop_mode()
        else:
            print("No area selected! Press 'Select Area' first.")
        self.update_status()
 
    def update_status(self):
        if self.detector.perspective_selector.selecting:
            status = "Status: Selecting area - click 4 corners"
        elif self.detector.crop_mode_enabled:
            status = "Status: Running - Crop View"
        else:
            status = "Status: Running - Full View"
        self.status_label.config(text=status)
        
        # Update connection status
        conn_status = self.channel_client.get_connection_status()
        if conn_status['connected']:
            self.connection_label.config(text="Connection: ✓ Connected", fg="green")
        else:
            self.connection_label.config(text=f"Connection: ✗ Reconnecting... (#{conn_status['reconnect_attempts']})", fg="red")
 
    def quit_app(self):
        self.detector.stop_detection()
        self.channel_client.close()
        self.root.quit()
 
    def run(self):
        # Process frames and update GUI on main thread
        def process_and_update():
            if self.detector.running:
                # Process one frame
                continue_running = self.detector.process_frame()
                if not continue_running:
                    self.quit_app()
                    return
 
                # Update GUI status
                self.update_status()
 
            # Schedule next frame processing
            self.root.after(1, process_and_update)  # Process as fast as possible
 
        # Start the processing loop
        process_and_update()
 
        # Start the Tkinter main loop
        self.root.mainloop()
 
def main():
    # Create and run the GUI application
    app = DetectorGUI()
    app.run()
 
if __name__ == "__main__":
    main()