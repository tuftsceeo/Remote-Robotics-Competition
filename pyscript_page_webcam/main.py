"""
AprilTag Detection System - Optimized Version
PyScript 2023.03.1 compatible
Inspired by the official apriltag.py structure
"""

import js
import asyncio
import time
import base64
import io
import cv2
import numpy as np
from PIL import Image
from pyodide.ffi import create_proxy
from collections import namedtuple

# =============================================================================
# APRILTAG DETECTION STRUCTURES (inspired by apriltag.py)
# =============================================================================

# Detection result structure - mimics the official apriltag.py Detection class
DetectionBase = namedtuple(
    'DetectionBase',
    'tag_family, tag_id, hamming, goodness, decision_margin, '
    'homography, center, corners'
)

class Detection(DetectionBase):
    """
    AprilTag detection result - simplified version of official Detection class
    """
    
    def __init__(self, tag_family, tag_id, hamming, goodness, decision_margin, 
                 homography, center, corners):
        super().__init__()
    
    def __str__(self):
        return f"AprilTag(family={self.tag_family}, id={self.tag_id}, center={self.center})"

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def log_message(message, log_div):
    """Add message to log with timestamp"""
    timestamp = time.strftime('%H:%M:%S')
    log_entry = f'<div>[{timestamp}] {message}</div>'
    log_div.innerHTML = log_entry + log_div.innerHTML
    print(f"[{timestamp}] {message}")

def update_status(message, status_element):
    """Update system status display"""
    status_element.innerText = message

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
    pil_image = to_pil(cv2_image)
    img_byte_arr = io.BytesIO()
    pil_image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    data = base64.b64encode(img_byte_arr).decode('utf-8')
    src = f"data:image/png;base64,{data}"
    result_image_element.setAttribute('src', src)

# =============================================================================
# CAMERA MANAGER CLASS
# =============================================================================

class CameraManager:
    def __init__(self, video_element, canvas_element, status_element, log_element):
        self.video = video_element
        self.canvas = canvas_element
        self.status = status_element
        self.log = log_element
        self.ctx = canvas_element.getContext("2d")
        self.is_active = False
        
    async def start_camera(self):
        """Start camera with proper error handling"""
        try:
            log_message("Requesting camera access...", self.log)
            
            if not hasattr(js.navigator, 'mediaDevices'):
                log_message("Media devices not available", self.log)
                update_status("Media devices not available", self.status)
                return False
            
            media = js.Object.new()
            media.audio = False
            media.video = True
            
            stream = await js.navigator.mediaDevices.getUserMedia(media)
            self.video.srcObject = stream
            
            self.is_active = True
            log_message("Camera stream connected", self.log)
            update_status("Camera active", self.status)
            return True
            
        except Exception as e:
            log_message(f"Camera error: {e}", self.log)
            update_status("Camera failed", self.status)
            return False
    
    def capture_frame(self):
        """Capture current frame from video"""
        if not self.is_active:
            return None
            
        try:
            self.ctx.drawImage(self.video, 0, 0, 640, 480)
            image_data_url = self.canvas.toDataURL('image/jpeg')
            raw_image = string_to_image(image_data_url.split('base64,')[1])
            cv2_image = to_opencv(raw_image)
            return cv2_image
            
        except Exception as e:
            log_message(f"Frame capture error: {e}", self.log)
            return None
    
    def stop_camera(self):
        """Stop camera stream"""
        if self.video.srcObject:
            tracks = self.video.srcObject.getTracks()
            for track in tracks:
                track.stop()
        self.is_active = False
        update_status("Camera stopped", self.status)

# =============================================================================
# APRILTAG DETECTOR CLASS (Simplified and Optimized)
# =============================================================================

class AprilTagDetector:
    """
    Simplified AprilTag detector inspired by the official apriltag.py structure
    Focuses on core AprilTag detection without excessive complexity
    """
    
    def __init__(self, log_element):
        self.log = log_element
        self.debug_mode = True
        
        # Core detection parameters (simplified from official implementation)
        self.quad_decimate = 1.0
        self.quad_sigma = 0.0
        self.refine_edges = True
        self.refine_decode = False
        self.refine_pose = False
        
        # Detection thresholds
        self.min_tag_size = 50      # Minimum tag size in pixels
        self.max_tag_size = 300     # Maximum tag size in pixels
        self.min_area = 2500        # Minimum contour area
        self.max_area = 90000       # Maximum contour area
        
        log_message("AprilTag detector initialized", self.log)
    
    def _preprocess_image(self, gray_img):
        """
        Simplified preprocessing pipeline inspired by official AprilTag processing
        """
        # Apply blur if sigma > 0 (matches official implementation)
        if self.quad_sigma > 0:
            blurred = cv2.GaussianBlur(gray_img, (0, 0), self.quad_sigma)
        else:
            blurred = gray_img
        
        # Decimate if needed (matches official implementation)
        if self.quad_decimate > 1.0:
            height, width = blurred.shape
            new_height = int(height / self.quad_decimate)
            new_width = int(width / self.quad_decimate)
            blurred = cv2.resize(blurred, (new_width, new_height))
        
        # Adaptive threshold (core of AprilTag detection)
        binary = cv2.adaptiveThreshold(
            blurred, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            11, 2
        )
        
        # Scale back up if decimated
        if self.quad_decimate > 1.0:
            binary = cv2.resize(binary, (gray_img.shape[1], gray_img.shape[0]))
        
        return binary
    
    def _is_valid_quad(self, contour):
        """
        Core quad validation inspired by official AprilTag quad detection
        """
        # Basic area check
        area = cv2.contourArea(contour)
        if not (self.min_area <= area <= self.max_area):
            return False, None
        
        # Bounding box check
        x, y, w, h = cv2.boundingRect(contour)
        if w < self.min_tag_size or h < self.min_tag_size:
            return False, None
        if w > self.max_tag_size or h > self.max_tag_size:
            return False, None
        
        # Aspect ratio check (AprilTags are square)
        aspect_ratio = max(w, h) / min(w, h)
        if aspect_ratio > 1.5:  # Allow some tolerance
            return False, None
        
        # Approximate to polygon
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Must have 4 vertices (quadrilateral)
        if len(approx) != 4:
            return False, None
        
        # Check convexity
        if not cv2.isContourConvex(approx):
            return False, None
        
        return True, approx
    
    def _calculate_homography(self, corners):
        """
        Calculate homography matrix for pose estimation
        Simplified version of official implementation
        """
        # Standard tag corner coordinates (unit square)
        tag_corners = np.array([
            [-1, -1],
            [ 1, -1],
            [ 1,  1],
            [-1,  1]
        ], dtype=np.float32)
        
        # Image corners (from detection)
        image_corners = np.array(corners, dtype=np.float32).reshape(-1, 2)
        
        # Calculate homography
        try:
            H, _ = cv2.findHomography(tag_corners, image_corners, cv2.RANSAC)
            return H if H is not None else np.eye(3)
        except:
            return np.eye(3)
    
    def _decode_tag(self, binary_roi):
        """
        Simplified tag decoding - placeholder for actual AprilTag decoding
        In real implementation, this would decode the actual tag bits
        """
        # This is a simplified version - real AprilTag decoding is complex
        # For now, return placeholder values
        return {
            'family': 'tag36h11',
            'id': 1,  # Would be decoded from tag bits
            'hamming': 0,  # Hamming distance
            'goodness': 0.8,  # Detection quality
            'decision_margin': 10.0  # Decision margin
        }
    
    def _extract_tag_region(self, gray_img, corners):
        """
        Extract and rectify the tag region for decoding
        """
        # Define the output size for the rectified tag
        tag_size = 64
        
        # Define the destination points (corners of output square)
        dst_corners = np.array([
            [0, 0],
            [tag_size-1, 0],
            [tag_size-1, tag_size-1],
            [0, tag_size-1]
        ], dtype=np.float32)
        
        # Source corners from detection
        src_corners = np.array(corners, dtype=np.float32).reshape(-1, 2)
        
        # Calculate perspective transform
        M = cv2.getPerspectiveTransform(src_corners, dst_corners)
        
        # Apply transform to extract rectified tag
        rectified = cv2.warpPerspective(gray_img, M, (tag_size, tag_size))
        
        # Threshold the rectified image
        _, binary_roi = cv2.threshold(rectified, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary_roi
    
    def detect(self, cv2_image):
        """
        Main detection method inspired by official apriltag.py detect() method
        """
        detections = []
        
        try:
            # Convert to grayscale
            if len(cv2_image.shape) == 3:
                gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = cv2_image
            
            # Preprocess image
            binary = self._preprocess_image(gray)
            
            # Find contours
            contours, _ = cv2.findContours(
                binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
            )
            
            if self.debug_mode:
                log_message(f"Found {len(contours)} contours", self.log)
            
            # Process each contour
            for contour in contours:
                # Validate as potential AprilTag quad
                is_valid, corners = self._is_valid_quad(contour)
                
                if is_valid:
                    # Extract tag region for decoding
                    binary_roi = self._extract_tag_region(gray, corners)
                    
                    # Decode the tag (simplified)
                    tag_info = self._decode_tag(binary_roi)
                    
                    # Calculate center
                    M = cv2.moments(contour)
                    if M["m00"] != 0:
                        center_x = M["m10"] / M["m00"]
                        center_y = M["m01"] / M["m00"]
                    else:
                        center_x, center_y = 0, 0
                    
                    # Calculate homography
                    homography = self._calculate_homography(corners)
                    
                    # Create detection object (matching official structure)
                    detection = Detection(
                        tag_family=tag_info['family'],
                        tag_id=tag_info['id'],
                        hamming=tag_info['hamming'],
                        goodness=tag_info['goodness'],
                        decision_margin=tag_info['decision_margin'],
                        homography=homography,
                        center=np.array([center_x, center_y]),
                        corners=corners.reshape(-1, 2)
                    )
                    
                    detections.append(detection)
                    
                    if self.debug_mode:
                        log_message(f"Detected AprilTag: family={tag_info['family']}, id={tag_info['id']}", self.log)
            
            # Draw detections
            for detection in detections:
                self._draw_detection(cv2_image, detection)
            
            if self.debug_mode:
                log_message(f"Total detections: {len(detections)}", self.log)
            
            return detections
            
        except Exception as e:
            log_message(f"Detection error: {e}", self.log)
            return []
    
    def _draw_detection(self, cv2_image, detection):
        """
        Draw detection results on image
        """
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
    
    def detection_pose(self, detection, camera_params, tag_size=1):
        """
        Calculate pose from detection (simplified version of official method)
        """
        # This would implement pose calculation similar to official apriltag.py
        # For now, return placeholder pose matrix
        pose_matrix = np.eye(4)
        init_error = 0.0
        final_error = 0.0
        
        return pose_matrix, init_error, final_error

# =============================================================================
# UI MANAGER CLASS
# =============================================================================

class UIManager:
    def __init__(self):
        # Get all DOM elements
        self.video = js.document.querySelector("#video")
        self.canvas = js.document.querySelector("#canvas")
        self.result_image = js.document.querySelector("#result-image")
        self.log_div = js.document.querySelector("#log")
        
        # UI elements
        self.start_camera_btn = js.document.querySelector("#start-camera")
        self.snap_photo_btn = js.document.querySelector("#snap-photo")
        self.start_detection_btn = js.document.querySelector("#start-detection")
        self.stop_detection_btn = js.document.querySelector("#stop-detection")
        self.toggle_debug_btn = js.document.querySelector("#toggle-debug")
        
        # Status elements
        self.status = js.document.querySelector("#status")
        self.tag_count = js.document.querySelector("#tag-count")
        self.fps_display = js.document.querySelector("#fps")
        self.total_detections = js.document.querySelector("#total-detections")
        self.detection_list = js.document.querySelector("#detection-list")
        
        # State variables
        self.detection_count = 0
        self.fps_counter = 0
        self.last_fps_time = time.time()
        
        # Validate DOM elements
        self.validate_elements()
    
    def validate_elements(self):
        """Check if all DOM elements exist"""
        elements = {
            'video': self.video,
            'canvas': self.canvas,
            'result_image': self.result_image,
            'log_div': self.log_div,
            'start_camera_btn': self.start_camera_btn,
            'snap_photo_btn': self.snap_photo_btn,
            'start_detection_btn': self.start_detection_btn,
            'stop_detection_btn': self.stop_detection_btn,
            'toggle_debug_btn': self.toggle_debug_btn,
            'status': self.status,
            'tag_count': self.tag_count,
            'fps_display': self.fps_display,
            'total_detections': self.total_detections,
            'detection_list': self.detection_list
        }
        
        missing = []
        for name, element in elements.items():
            if not element:
                missing.append(name)
        
        if missing:
            print(f"Missing DOM elements: {missing}")
            return False
        else:
            print("All DOM elements found")
            return True
    
    def log(self, message):
        """Log message with timestamp"""
        log_message(message, self.log_div)
    
    def set_status(self, message):
        """Update status display"""
        update_status(message, self.status)
    
    def show_result(self, cv2_image):
        """Display detection results"""
        show_result_image(cv2_image, self.result_image)
    
    def update_detection_display(self, detections):
        """Update detection results in UI"""
        # Update counters
        self.tag_count.innerText = str(len(detections))
        self.detection_count += len(detections)
        self.total_detections.innerText = str(self.detection_count)
        
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
                </div>
                """
            self.detection_list.innerHTML = results_html
        else:
            self.detection_list.innerHTML = "<p>No AprilTags detected</p>"
    
    def update_fps(self):
        """Update FPS counter"""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.last_fps_time >= 1.0:
            self.fps_display.innerText = str(self.fps_counter)
            self.fps_counter = 0
            self.last_fps_time = current_time
    
    def enable_detection_controls(self):
        """Enable detection-related controls"""
        self.start_detection_btn.disabled = False
        self.snap_photo_btn.disabled = False
    
    def set_detection_state(self, detecting):
        """Update UI for detection state"""
        if detecting:
            self.start_detection_btn.disabled = True
            self.stop_detection_btn.disabled = False
            self.set_status("Detection active")
            self.log("Detection started")
        else:
            self.start_detection_btn.disabled = False
            self.stop_detection_btn.disabled = True
            self.set_status("Detection paused")
            self.log("Detection stopped")
    
    def setup_canvas(self):
        """Setup canvas dimensions"""
        self.canvas.width = 640
        self.canvas.height = 480
        print("Canvas dimensions set to 640x480")

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
    
    # Initialize UI manager
    ui = UIManager()
    ui.setup_canvas()
    ui.log("System initializing...")
    
    # Initialize camera manager
    camera = CameraManager(ui.video, ui.canvas, ui.status, ui.log_div)
    
    # Initialize detector
    detector = AprilTagDetector(ui.log_div)
    
    # Check browser compatibility
    if hasattr(js.navigator, 'mediaDevices'):
        ui.log("Media devices available")
    else:
        ui.log("Media devices not available - use Chrome/Firefox")
        ui.set_status("Browser not supported")
    
    ui.log("System ready! Click Start Camera to begin")

def process_frame():
    """Process current video frame for detection"""
    if not detecting or not camera.is_active:
        return []
    
    try:
        # Capture frame from camera
        cv2_image = camera.capture_frame()
        if cv2_image is None:
            return []
        
        # Detect AprilTags
        detections = detector.detect(cv2_image)
        
        # Update UI with detection results
        ui.show_result(cv2_image)
        ui.update_detection_display(detections)
        ui.update_fps()
        
        return detections
        
    except Exception as e:
        ui.log(f"Frame processing error: {e}")
        return []

# Event handlers
async def start_camera_handler(e):
    """Handle start camera button click"""
    success = await camera.start_camera()
    if success:
        ui.enable_detection_controls()

async def snap_photo_handler(e):
    """Handle snap photo button click"""
    try:
        cv2_image = camera.capture_frame()
        if cv2_image is None:
            ui.log("No camera frame available")
            return
        
        detections = detector.detect(cv2_image)
        ui.show_result(cv2_image)
        ui.update_detection_display(detections)
        ui.log(f"Photo taken - found {len(detections)} AprilTags")
        
    except Exception as e:
        ui.log(f"Photo capture error: {e}")

async def start_detection_handler(e):
    """Handle start detection button click"""
    global detecting
    detecting = True
    ui.set_detection_state(True)

async def stop_detection_handler(e):
    """Handle stop detection button click"""
    global detecting
    detecting = False
    ui.set_detection_state(False)

async def toggle_debug_handler(e):
    """Toggle debug mode"""
    detector.debug_mode = not detector.debug_mode
    status = "enabled" if detector.debug_mode else "disabled"
    ui.log(f"Debug mode {status}")

# Main detection loop
async def detection_loop():
    """Main continuous detection loop"""
    while True:
        if detecting:
            process_frame()
        await asyncio.sleep(0.1)  # 10 FPS

def setup_event_listeners():
    """Attach event listeners to buttons"""
    try:
        ui.start_camera_btn.addEventListener('click', create_proxy(start_camera_handler))
        ui.snap_photo_btn.addEventListener('click', create_proxy(snap_photo_handler))
        ui.start_detection_btn.addEventListener('click', create_proxy(start_detection_handler))
        ui.stop_detection_btn.addEventListener('click', create_proxy(stop_detection_handler))
        ui.toggle_debug_btn.addEventListener('click', create_proxy(toggle_debug_handler))
        ui.log("Event listeners attached")
    except Exception as e:
        ui.log(f"Error attaching event listeners: {e}")

# =============================================================================
# INITIALIZATION
# =============================================================================

# Initialize everything
initialize_system()
setup_event_listeners()

# Start detection loop
asyncio.create_task(detection_loop())

print("AprilTag detector fully initialized")
