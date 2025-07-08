"""
AprilTag Detection System - Main Application
PyScript 2024.11.1 compatible
Uses separate AprilTagDetector module for detection logic
"""

import asyncio
import time
import base64
import io
import cv2
import numpy as np
from PIL import Image
from pyscript import document, when
from pyodide.ffi import create_proxy
from apriltag_detector import AprilTagDetector, DetectorOptions

# Get JS object for browser APIs
import js

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def string_to_image(base64_string):
    """Convert base64 string to PIL image"""
    imgdata = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(imgdata))

def to_opencv(pil_image):
    """Convert PIL image to OpenCV format"""
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGR)

def to_pil(cv2_image):
    """Convert OpenCV image to PIL format"""
    return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGBA))

def show_result_image(cv2_image, result_image_element):
    """Display OpenCV image in the results area"""
    try:
        pil_image = to_pil(cv2_image)
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='PNG', optimize=True)
        img_byte_arr = img_byte_arr.getvalue()
        data = base64.b64encode(img_byte_arr).decode('utf-8')
        src = f"data:image/png;base64,{data}"
        
        # PyScript 2024.11.1 compatible attribute setting
        try:
            result_image_element.setAttribute('src', src)
        except:
            # Alternative method
            result_image_element.src = src
            
    except Exception as e:
        print(f"Error displaying result: {e}")

def draw_detections(cv2_image, detections):
    """Draw detection results on image"""
    for detection in detections:
        center = detection.center
        corners = detection.corners
        tag_id = detection.tag_id
        
        # Draw contour
        pts = np.array(corners, np.int32).reshape((-1, 1, 2))
        cv2.polylines(cv2_image, [pts], True, (0, 255, 0), 3)
        
        # Draw center
        cv2.circle(cv2_image, (int(center[0]), int(center[1])), 5, (0, 0, 255), -1)
        
        # Draw ID
        cv2.putText(cv2_image, f"ID: {tag_id}",
                   (int(center[0]) - 20, int(center[1]) - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

# =============================================================================
# CAMERA MANAGER
# =============================================================================

class CameraManager:
    def __init__(self, video_element, canvas_element):
        self.video = video_element
        self.canvas = canvas_element
        # In PyScript 2024.11.1, canvas context access might be different
        try:
            self.ctx = canvas_element.getContext("2d")
        except:
            # Fallback for different API
            self.ctx = canvas_element.get_context("2d")
        self.is_active = False
        
    async def start_camera(self):
        """Start camera with proper error handling"""
        try:
            print("Requesting camera access...")
            
            # Check for media devices availability
            if not hasattr(js.navigator, 'mediaDevices'):
                print("Media devices not available")
                return False
            
            # Create media constraints - use js.Object.fromEntries for proper JS object
            try:
                # Method 1: Direct object creation
                media_constraints = js.Object.new()
                media_constraints.audio = False
                media_constraints.video = True
            except:
                # Method 2: Alternative creation method
                media_constraints = {
                    'audio': False,
                    'video': True
                }
            
            # Get user media
            stream = await js.navigator.mediaDevices.getUserMedia(media_constraints)
            
            # Set video source
            try:
                self.video.srcObject = stream
            except:
                # Alternative method for PyScript 2024.11.1
                self.video.src_object = stream
            
            self.is_active = True
            print("Camera stream connected")
            return True
            
        except Exception as e:
            print(f"Camera error: {e}")
            return False
    
    def capture_frame(self):
        """Capture current frame from video"""
        if not self.is_active:
            return None
            
        try:
            # Draw video frame to canvas
            self.ctx.drawImage(self.video, 0, 0, 640, 480)
            
            # Get image data - try different methods for PyScript 2024.11.1
            try:
                image_data_url = self.canvas.toDataURL('image/jpeg')
            except:
                # Alternative method if toDataURL doesn't work directly
                image_data_url = self.canvas.to_data_url('image/jpeg')
            
            raw_image = string_to_image(image_data_url.split('base64,')[1])
            cv2_image = to_opencv(raw_image)
            return cv2_image
            
        except Exception as e:
            print(f"Frame capture error: {e}")
            return None
    
    def stop_camera(self):
        """Stop camera stream"""
        try:
            if hasattr(self.video, 'srcObject') and self.video.srcObject:
                tracks = self.video.srcObject.getTracks()
                for track in tracks:
                    track.stop()
            elif hasattr(self.video, 'src_object') and self.video.src_object:
                tracks = self.video.src_object.getTracks()
                for track in tracks:
                    track.stop()
        except Exception as e:
            print(f"Error stopping camera: {e}")
        
        self.is_active = False
        print("Camera stopped")

# AprilTagDetector is now imported from separate module

# =============================================================================
# UI MANAGER
# =============================================================================

class UIManager:
    def __init__(self):
        # Get DOM elements using pyscript.document
        self.video = document.querySelector("#video")
        self.canvas = document.querySelector("#canvas")
        self.result_image = document.querySelector("#result-image")
        
        # UI elements
        self.start_camera_btn = document.querySelector("#start-camera")
        self.start_detection_btn = document.querySelector("#start-detection")
        self.stop_detection_btn = document.querySelector("#stop-detection")
        
        # Status elements
        self.tag_count = document.querySelector("#tag-count")
        self.fps_display = document.querySelector("#fps")
        self.detection_list = document.querySelector("#detection-list")
        
        # FPS optimization
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.last_ui_update = time.time()
        
        print("UI Manager initialized")
    
    def show_result(self, cv2_image):
        """Display detection results - optimized for FPS"""
        current_time = time.time()
        if current_time - self.last_ui_update > 0.033:  # ~30 FPS max for UI updates
            show_result_image(cv2_image, self.result_image)
            self.last_ui_update = current_time
    
    def update_detection_display(self, detections):
        """Update detection results"""
        # Update tag count - PyScript 2024.11.1 compatible
        try:
            self.tag_count.innerText = str(len(detections))
        except:
            self.tag_count.textContent = str(len(detections))
        
        # Update detection list
        if detections:
            results_html = ""
            for detection in detections:
                center = detection.center
                results_html += f"""
                <div class="detection-item">
                    <div class="detection-id">AprilTag ID: {detection.tag_id}</div>
                    <div class="detection-pos">Family: {detection.tag_family}</div>
                    <div class="detection-pos">Center: ({center[0]:.0f}, {center[1]:.0f})</div>
                    <div class="detection-pos">Hamming: {detection.hamming}</div>
                    <div class="detection-pos">Goodness: {detection.goodness:.2f}</div>
                    <div class="detection-pos">Decision Margin: {detection.decision_margin:.2f}</div>
                </div>
                """
            try:
                self.detection_list.innerHTML = results_html
            except:
                self.detection_list.inner_html = results_html
        else:
            try:
                self.detection_list.innerHTML = "<p>No AprilTags detected</p>"
            except:
                self.detection_list.inner_html = "<p>No AprilTags detected</p>"
    
    def update_fps(self):
        """Update FPS counter"""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.last_fps_time >= 1.0:
            try:
                self.fps_display.innerText = str(self.fps_counter)
            except:
                self.fps_display.textContent = str(self.fps_counter)
            self.fps_counter = 0
            self.last_fps_time = current_time
    
    def enable_detection_controls(self):
        """Enable detection-related controls"""
        try:
            self.start_detection_btn.disabled = False
        except:
            self.start_detection_btn.setAttribute('disabled', False)
    
    def set_detection_state(self, detecting):
        """Update UI for detection state"""
        if detecting:
            try:
                self.start_detection_btn.disabled = True
                self.stop_detection_btn.disabled = False
            except:
                self.start_detection_btn.setAttribute('disabled', True)
                self.stop_detection_btn.setAttribute('disabled', False)
            print("Detection active")
        else:
            try:
                self.start_detection_btn.disabled = False
                self.stop_detection_btn.disabled = True
            except:
                self.start_detection_btn.setAttribute('disabled', False)
                self.stop_detection_btn.setAttribute('disabled', True)
            print("Detection paused")
    
    def setup_canvas(self):
        """Setup canvas dimensions"""
        try:
            self.canvas.width = 640
            self.canvas.height = 480
        except:
            # Alternative method for PyScript 2024.11.1
            self.canvas.setAttribute('width', '640')
            self.canvas.setAttribute('height', '480')
        print("Canvas dimensions set")

# =============================================================================
# MAIN APPLICATION
# =============================================================================

# Global state
ui = None
camera = None
detector = None
detecting = False

def initialize_system():
    """Initialize all system components"""
    global ui, camera, detector
    
    ui = UIManager()
    ui.setup_canvas()
    print("System initializing...")
    
    camera = CameraManager(ui.video, ui.canvas)
    detector = AprilTagDetector(DetectorOptions(debug=True), print)
    
    if hasattr(js.navigator, 'mediaDevices'):
        print("Media devices available")
    else:
        print("Media devices not available")
    
    print("System ready!")

def process_frame():
    """Process current video frame for detection"""
    if not detecting or not camera.is_active:
        return []
    
    try:
        cv2_image = camera.capture_frame()
        if cv2_image is None:
            return []
        
        detections = detector.detect(cv2_image)
        
        # Draw detections on image
        draw_detections(cv2_image, detections)
        
        # Update UI
        ui.show_result(cv2_image)
        ui.update_detection_display(detections)
        ui.update_fps()
        
        return detections
        
    except Exception as e:
        print(f"Frame processing error: {e}")
        return []

# Event handlers
async def start_camera_handler(e):
    """Handle start camera button click"""
    success = await camera.start_camera()
    if success:
        ui.enable_detection_controls()

async def start_detection_handler(e):
    """Handle start detection button click"""
    global detecting
    detecting = True
    ui.set_detection_state(True)
    print("Detection started")

async def stop_detection_handler(e):
    """Handle stop detection button click"""
    global detecting
    detecting = False
    ui.set_detection_state(False)
    print("Detection stopped")

# Main detection loop - optimized for FPS
async def detection_loop():
    """Main continuous detection loop"""
    while True:
        if detecting:
            process_frame()
        await asyncio.sleep(0.016)  # ~60 FPS target

def setup_event_listeners():
    """Attach event listeners to buttons using PyScript 2024.11.1 syntax"""
    try:
        # Use the newer event handling approach
        ui.start_camera_btn.onclick = create_proxy(start_camera_handler)
        ui.start_detection_btn.onclick = create_proxy(start_detection_handler)
        ui.stop_detection_btn.onclick = create_proxy(stop_detection_handler)
        print("Event listeners attached")
    except Exception as e:
        print(f"Error attaching event listeners: {e}")

# Alternative event handlers using @when decorator (PyScript 2024.11.1 style)
@when("click", "#start-camera")
async def start_camera_click(event):
    """Handle start camera button click"""
    await start_camera_handler(event)

@when("click", "#start-detection")
async def start_detection_click(event):
    """Handle start detection button click"""
    await start_detection_handler(event)

@when("click", "#stop-detection")
async def stop_detection_click(event):
    """Handle stop detection button click"""
    await stop_detection_handler(event)

# =============================================================================
# INITIALIZATION
# =============================================================================

# Initialize everything
initialize_system()

# Event listeners are automatically set up via @when decorators
# No need to call setup_event_listeners() explicitly

# Start detection loop
asyncio.create_task(detection_loop())

print("Accurate AprilTag detector ready!")
