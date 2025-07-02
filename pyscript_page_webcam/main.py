from pyscript import document, window
import asyncio
import channel
import json
import time

# Initialize channel for sending robot data
myChannel = channel.CEEO_Channel("robotics-competition", "@your-username", "robot-tracking", 
                                 divName='all_things_channels', suffix='_tracker')

class RobotTracker:
    def __init__(self):
        self.video = document.getElementById('video')
        self.canvas = document.getElementById('canvas')
        self.ctx = self.canvas.getContext('2d')
        self.tracking = False
        self.camera_stream = None
        self.available_cameras = []
        self.selected_camera_id = None
        
        # Get UI elements
        self.detect_cameras_btn = document.getElementById('detect-cameras-btn')
        self.camera_select = document.getElementById('camera-select')
        self.test_camera_btn = document.getElementById('test-camera-btn')
        self.start_btn = document.getElementById('start-btn')
        self.stop_btn = document.getElementById('stop-btn')
        self.calibrate_btn = document.getElementById('calibrate-btn')
        self.snapshot_btn = document.getElementById('snapshot-btn')
        
        # Status displays
        self.camera_status = document.getElementById('camera-status')
        self.camera_details = document.getElementById('camera-details')
        self.debug_log = document.getElementById('debug-log')
        self.position_display = document.getElementById('position')
        self.rotation_display = document.getElementById('rotation')
        self.timestamp_display = document.getElementById('timestamp')
        self.fps_display = document.getElementById('fps')
        self.tags_display = document.getElementById('tags-detected')
        self.status_display = document.getElementById('tracking-status')
        self.connection_status = document.getElementById('connection-status')
        
        # Tracking variables
        self.last_detection_time = 0
        self.fps_counter = 0
        self.fps_time = time.time()
        
        # Field calibration parameters
        self.field_corners = None
        self.pixels_to_meters = 1.0
        self.field_width_meters = 3.66
        self.field_height_meters = 3.66
        
        # Setup event handlers
        self.setup_events()
        self.log_debug("Robot Tracker initialized")
        
    def setup_events(self):
        """Setup button event handlers"""
        self.detect_cameras_btn.onclick = self.detect_cameras
        self.test_camera_btn.onclick = self.test_camera
        self.start_btn.onclick = self.start_tracking
        self.stop_btn.onclick = self.stop_tracking
        self.calibrate_btn.onclick = self.calibrate_field
        self.snapshot_btn.onclick = self.take_snapshot
        self.camera_select.onchange = self.on_camera_select
        
    def log_debug(self, message):
        """Add debug message to log"""
        timestamp = time.strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}<br>"
        self.debug_log.innerHTML = log_entry + self.debug_log.innerHTML
        print(f"Debug: {message}")
    
    async def detect_cameras(self, event=None):
        """Detect available cameras"""
        self.log_debug("Detecting cameras...")
        self.camera_status.innerText = "Detecting cameras..."
        
        try:
            # Request permission first
            await window.navigator.mediaDevices.getUserMedia({'video': True})
            self.log_debug("Camera permission granted")
            
            # Get list of devices
            devices = await window.navigator.mediaDevices.enumerateDevices()
            self.available_cameras = []
            
            # Clear previous options
            self.camera_select.innerHTML = '<option value="">Select a camera...</option>'
            
            camera_count = 0
            for device in devices:
                if device.kind == 'videoinput':
                    camera_count += 1
                    self.available_cameras.append(device)
                    
                    # Create option element
                    option = document.createElement('option')
                    option.value = device.deviceId
                    camera_name = device.label if device.label else f"Camera {camera_count}"
                    option.text = camera_name
                    self.camera_select.appendChild(option)
                    
                    self.log_debug(f"Found camera: {camera_name} (ID: {device.deviceId[:8]}...)")
            
            if camera_count > 0:
                self.camera_status.innerText = f"Found {camera_count} camera(s)"
                self.camera_details.innerHTML = f"Select a camera from the dropdown to test"
                self.test_camera_btn.disabled = False
            else:
                self.camera_status.innerText = "No cameras found"
                self.camera_details.innerHTML = "Make sure your USB camera is connected"
                self.log_debug("No video input devices found")
                
        except Exception as e:
            error_msg = f"Error detecting cameras: {e}"
            self.camera_status.innerText = "Camera detection failed"
            self.camera_details.innerHTML = error_msg
            self.log_debug(error_msg)
    
    def on_camera_select(self, event):
        """Handle camera selection"""
        self.selected_camera_id = self.camera_select.value
        if self.selected_camera_id:
            selected_name = self.camera_select.options[self.camera_select.selectedIndex].text
            self.log_debug(f"Selected camera: {selected_name}")
            self.camera_details.innerHTML = f"Selected: {selected_name}<br>Click 'Test Selected Camera' to connect"
        else:
            self.selected_camera_id = None
    
    async def test_camera(self, event=None):
        """Test the selected camera"""
        if not self.selected_camera_id:
            self.log_debug("No camera selected")
            return
            
        self.log_debug("Testing camera connection...")
        self.camera_status.innerText = "Connecting to camera..."
        
        try:
            # Stop any existing stream
            await self.stop_camera()
            
            # Configure camera constraints
            constraints = {
                'video': {
                    'deviceId': {'exact': self.selected_camera_id},
                    'width': {'ideal': 640},
                    'height': {'ideal': 480},
                    'frameRate': {'ideal': 30}
                }
            }
            
            # Get camera stream
            self.camera_stream = await window.navigator.mediaDevices.getUserMedia(constraints)
            self.video.srcObject = self.camera_stream
            
            # Wait for video to load
            def on_video_loaded():
                self.camera_status.innerText = "Camera connected successfully"
                self.camera_details.innerHTML = f"Resolution: {self.video.videoWidth}x{self.video.videoHeight}<br>Ready to start tracking"
                self.start_btn.disabled = False
                self.log_debug(f"Camera stream active: {self.video.videoWidth}x{self.video.videoHeight}")
                
            self.video.onloadedmetadata = on_video_loaded
            
        except Exception as e:
            error_msg = f"Camera connection failed: {e}"
            self.camera_status.innerText = "Camera connection failed"
            self.camera_details.innerHTML = error_msg
            self.log_debug(error_msg)
    
    async def stop_camera(self):
        """Stop the camera stream"""
        if self.camera_stream:
            tracks = self.camera_stream.getTracks()
            for track in tracks:
                track.stop()
            self.camera_stream = None
            self.log_debug("Camera stream stopped")
    
    async def start_tracking(self, event=None):
        """Start robot tracking"""
        if not self.camera_stream:
            self.log_debug("No camera stream available")
            return
            
        self.tracking = True
        self.start_btn.disabled = True
        self.stop_btn.disabled = False
        self.status_display.innerText = "Tracking Active"
        self.log_debug("Started robot tracking")
        
        # Start processing loop
        self.process_video()
    
    async def stop_tracking(self, event=None):
        """Stop robot tracking"""
        self.tracking = False
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
        self.status_display.innerText = "Tracking Stopped"
        self.log_debug("Stopped robot tracking")
    
    def calibrate_field(self, event=None):
        """Calibrate field coordinates"""
        self.log_debug("Field calibration started")
        self.status_display.innerText = "Place AprilTags at field corners, then click Calibrate"
        # Simple calibration for now
        self.pixels_to_meters = self.field_width_meters / 640
        self.status_display.innerText = "Field calibrated"
        self.log_debug(f"Field calibrated: {self.pixels_to_meters:.4f} meters/pixel")
    
    def take_snapshot(self, event=None):
        """Take a snapshot of current frame"""
        if self.video.videoWidth > 0:
            self.ctx.drawImage(self.video, 0, 0, 640, 480)
            self.log_debug("Snapshot taken")
        else:
            self.log_debug("No video feed available for snapshot")
    
    def process_video(self):
        """Main video processing loop"""
        if not self.tracking or not self.camera_stream:
            return
            
        try:
            # Draw video frame to canvas
            if self.video.videoWidth > 0:
                self.ctx.drawImage(self.video, 0, 0, 640, 480)
                
                # Simulate AprilTag detection for now
                self.simulate_detection()
                
                # Update FPS
                self.update_fps()
                
        except Exception as e:
            self.log_debug(f"Processing error: {e}")
        
        # Continue processing
        window.requestAnimationFrame(self.process_video)
    
    def simulate_detection(self):
        """Simulate AprilTag detection for testing"""
        import random
        
        # Simulate finding a robot occasionally
        if random.random() > 0.8:  # 20% chance of detection per frame
            robot_data = {
                'robot_id': 1,
                'position': {
                    'x': random.uniform(-1.8, 1.8),
                    'y': 0.1,
                    'z': random.uniform(-1.8, 1.8)
                },
                'rotation': random.uniform(0, 360),
                'timestamp': time.time(),
                'confidence': random.uniform(0.8, 1.0)
            }
            
            # Draw detection visualization
            self.draw_detection_overlay(robot_data)
            
            self.update_display(robot_data)
            asyncio.create_task(self.send_robot_data(robot_data))
    
    def draw_detection_overlay(self, robot_data):
        """Draw detection overlay on canvas"""
        # Convert field coordinates to pixel coordinates
        center_x = 320 + (robot_data['position']['x'] / self.field_width_meters) * 640
        center_y = 240 + (robot_data['position']['z'] / self.field_height_meters) * 480
        
        # Draw detection box
        self.ctx.strokeStyle = '#00ff00'
        self.ctx.lineWidth = 2
        self.ctx.strokeRect(center_x - 25, center_y - 25, 50, 50)
        
        # Draw center point
        self.ctx.fillStyle = '#ff0000'
        self.ctx.beginPath()
        self.ctx.arc(center_x, center_y, 5, 0, 2 * 3.14159)
        self.ctx.fill()
        
        # Draw robot ID
        self.ctx.fillStyle = '#ffffff'
        self.ctx.font = '12px Arial'
        self.ctx.fillText(f"Robot {robot_data['robot_id']}", center_x + 10, center_y - 10)
    
    def update_display(self, robot_data):
        """Update the UI with detected robot data"""
        pos = robot_data['position']
        self.position_display.innerText = f"X: {pos['x']:.2f}, Y: {pos['y']:.2f}, Z: {pos['z']:.2f}"
        self.rotation_display.innerText = f"Rotation: {robot_data['rotation']:.1f}°"
        self.timestamp_display.innerText = f"Last Update: {time.strftime('%H:%M:%S')}"
        self.tags_display.innerText = "Tags: 1"
    
    async def send_robot_data(self, robot_data):
        """Send robot data through the channel"""
        try:
            # Send position data
            await myChannel.post('/robot/position/x', robot_data['position']['x'])
            await myChannel.post('/robot/position/y', robot_data['position']['y'])
            await myChannel.post('/robot/position/z', robot_data['position']['z'])
            await myChannel.post('/robot/rotation', robot_data['rotation'])
            await myChannel.post('/robot/timestamp', robot_data['timestamp'])
            
            # Send complete robot data as JSON
            await myChannel.post('/robot/data', json.dumps(robot_data))
            
            self.connection_status.innerText = f"Sent: {time.strftime('%H:%M:%S')}"
            self.connection_status.className = "status-connected"
            
        except Exception as e:
            error_msg = f"Send Error: {e}"
            self.log_debug(f"Channel send error: {e}")
            self.connection_status.innerText = error_msg
            self.connection_status.className = "status-error"
    
    def update_fps(self):
        """Update FPS counter"""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.fps_time >= 1.0:
            self.fps_display.innerText = f"FPS: {self.fps_counter}"
            self.fps_counter = 0
            self.fps_time = current_time

# Initialize the tracker
tracker = RobotTracker()

# Auto-detect cameras on startup
asyncio.create_task(tracker.detect_cameras())

# Channel callback for receiving commands
async def handle_channel_message(message):
    """Handle incoming channel messages"""
    try:
        if message['type'] == 'data' and 'payload' in message:
            payload_data = json.loads(message['payload'])
            topic = payload_data['topic']
            value = payload_data['value']
            
            if topic == '/robot/command/calibrate':
                tracker.calibrate_field(None)
            elif topic == '/robot/command/start':
                await tracker.start_tracking(None)
            elif topic == '/robot/command/stop':
                await tracker.stop_tracking(None)
            elif topic == '/robot/command/detect_cameras':
                await tracker.detect_cameras(None)
                
    except Exception as e:
        tracker.log_debug(f"Channel message error: {e}")

myChannel.callback = handle_channel_message
