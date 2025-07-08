"""
AprilTag-like Detection System
Consolidated single file for PyScript 2023.03.1 compatibility
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
            
            # Check if getUserMedia is available
            if not hasattr(js.navigator, 'mediaDevices'):
                log_message("Media devices not available", self.log)
                update_status("Media devices not available", self.status)
                return False
            
            # Request camera access
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
            # Draw video frame to canvas
            self.ctx.drawImage(self.video, 0, 0, 640, 480)
            
            # Get image data and convert to OpenCV
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
# APRILTAG DETECTOR CLASS
# =============================================================================

class AprilTagDetector:
    def __init__(self, log_element):
        self.log = log_element
        self.min_tag_area = 200  # Minimum area for tag consideration
        self.max_tag_area = 100000  # Increased maximum area
        self.image_area_threshold = 0.8  # Reject contours larger than 80% of image
        self.min_aspect_ratio = 0.5  # More relaxed aspect ratio
        self.max_aspect_ratio = 2.0  # More relaxed aspect ratio
        self.debug_mode = True  # Enable debugging by default
        self.image_width = 640
        self.image_height = 480
        self.total_image_area = self.image_width * self.image_height
        log_message("AprilTag detector initialized with expanded parameters", self.log)
    
    def preprocess_image(self, gray_img):
        """Enhanced preprocessing pipeline for better detection"""
        # Apply CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray_img)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
        
        # Try multiple thresholding approaches with different parameters
        results = []
        
        # Method 1: Adaptive thresholding (normal)
        binary1 = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        results.append(binary1)
        
        # Method 2: Adaptive thresholding (inverted)
        binary2 = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        results.append(binary2)
        
        # Method 3: Different block size
        binary3 = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 15, 2
        )
        results.append(binary3)
        
        # Method 4: Mean thresholding
        binary4 = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        results.append(binary4)
        
        # Combine results with bitwise operations
        combined = results[0]
        for binary in results[1:]:
            combined = cv2.bitwise_or(combined, binary)
        
        # Light morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        morphed = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=1)
        morphed = cv2.morphologyEx(morphed, cv2.MORPH_OPEN, kernel, iterations=1)
        
        return morphed
    
    def is_valid_tag(self, contour):
        """Enhanced validation of potential AprilTag contours with debugging"""
        # Area check
        area = cv2.contourArea(contour)
        
        # Check if contour is too large (probably background)
        if area > self.total_image_area * self.image_area_threshold:
            if self.debug_mode:
                percentage = (area / self.total_image_area) * 100
                log_message(f"Rejected contour: area {area:.0f} is {percentage:.1f}% of image (too large)", self.log)
            return False, None
        
        # Standard area check
        if not (self.min_tag_area < area < self.max_tag_area):
            if self.debug_mode:
                log_message(f"Rejected contour: area {area:.0f} outside range [{self.min_tag_area}, {self.max_tag_area}]", self.log)
            return False, None
        
        # Get bounding rectangle for aspect ratio check
        x, y, w, h = cv2.boundingRect(contour)
        if w == 0 or h == 0:
            if self.debug_mode:
                log_message("Rejected contour: zero width or height", self.log)
            return False, None
        
        # Quick aspect ratio check
        aspect_ratio = max(w, h) / min(w, h)
        if aspect_ratio > 5.0:  # Very elongated shapes
            if self.debug_mode:
                log_message(f"Rejected contour: aspect ratio {aspect_ratio:.2f} too extreme", self.log)
            return False, None
        
        # Convexity check (more relaxed)
        hull = cv2.convexHull(contour)
        if cv2.contourArea(hull) == 0:
            if self.debug_mode:
                log_message("Rejected contour: zero hull area", self.log)
            return False, None
        
        convexity = area / cv2.contourArea(hull)
        if convexity < 0.6:  # More relaxed convexity requirement
            if self.debug_mode:
                log_message(f"Rejected contour: convexity {convexity:.2f} too low", self.log)
            return False, None
        
        # Polygon approximation (more relaxed)
        epsilon = 0.05 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Allow 4-8 vertices
        if not (4 <= len(approx) <= 8):
            if self.debug_mode:
                log_message(f"Rejected contour: {len(approx)} vertices (need 4-8)", self.log)
            return False, None
        
        # If we have more than 4 vertices, try to find better approximation
        if len(approx) > 4:
            # Try with smaller epsilon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            if len(approx) > 6:
                # Use minimum area rectangle if still too many vertices
                rect = cv2.minAreaRect(contour)
                box = cv2.boxPoints(rect)
                approx = np.int0(box).reshape(-1, 1, 2)
        
        if self.debug_mode:
            log_message(f"Accepted contour: area={area:.0f}, vertices={len(approx)}, convexity={convexity:.2f}, aspect={aspect_ratio:.2f}", self.log)
        
        return True, approx
    
    def calculate_confidence(self, contour, approx):
        """More sophisticated confidence calculation"""
        confidence = 0.0
        
        # Area-based confidence
        area = cv2.contourArea(contour)
        if self.min_tag_area < area < self.max_tag_area:
            # Favor medium-sized areas
            optimal_area = 5000  # Preferred area
            area_score = 1.0 - min(abs(area - optimal_area) / optimal_area, 1.0)
            confidence += area_score * 0.3
        
        # Aspect ratio confidence
        x, y, w, h = cv2.boundingRect(contour)
        if w > 0 and h > 0:
            aspect_ratio = max(w, h) / min(w, h)
            if aspect_ratio < 2.0:  # Prefer more square shapes
                aspect_score = 1.0 - (aspect_ratio - 1.0) / 1.0
                confidence += aspect_score * 0.3
        
        # Convexity confidence
        hull = cv2.convexHull(contour)
        if cv2.contourArea(hull) > 0:
            convexity = area / cv2.contourArea(hull)
            confidence += convexity * 0.2
        
        # Vertex count confidence (prefer 4 vertices)
        vertex_count = len(approx)
        if vertex_count == 4:
            confidence += 0.2
        elif vertex_count <= 6:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def detect_tags(self, cv2_image):
        """
        Optimized AprilTag-like detection with debugging
        Returns list of detection dictionaries
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)
            
            # Preprocess image
            processed = self.preprocess_image(gray)
            
            # Find contours
            contours, _ = cv2.findContours(
                processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            if self.debug_mode:
                log_message(f"Found {len(contours)} contours to analyze", self.log)
                if len(contours) > 0:
                    areas = [cv2.contourArea(c) for c in contours]
                    log_message(f"Contour areas: {sorted(areas, reverse=True)[:5]} (showing top 5)", self.log)
            
            detections = []
            
            for i, contour in enumerate(contours):
                # Validate contour as potential tag
                is_valid, approx = self.is_valid_tag(contour)
                
                if is_valid:
                    # Calculate moments and center
                    M = cv2.moments(contour)
                    if M["m00"] == 0:
                        continue
                    
                    center_x = M["m10"] / M["m00"]
                    center_y = M["m01"] / M["m00"]
                    
                    # Calculate confidence
                    confidence = self.calculate_confidence(contour, approx)
                    
                    # More relaxed confidence threshold
                    if confidence > 0.2:  # Lowered from 0.3
                        detection = {
                            'type': 'apriltag',
                            'id': i + 1,
                            'center': [float(center_x), float(center_y)],
                            'corners': approx.reshape(-1, 2).tolist(),
                            'area': float(cv2.contourArea(contour)),
                            'confidence': confidence
                        }
                        
                        detections.append(detection)
                        
                        # Draw detection on image
                        self.draw_detection(cv2_image, detection)
                        
                        if self.debug_mode:
                            log_message(f"Detection {i+1}: confidence={confidence:.2f}, area={cv2.contourArea(contour):.0f}", self.log)
            
            if self.debug_mode:
                log_message(f"Final detections: {len(detections)} AprilTags found", self.log)
            
            return detections
            
        except Exception as e:
            log_message(f"Detection error: {e}", self.log)
            return []
    
    def draw_detection(self, cv2_image, detection):
        """Enhanced drawing of detections"""
        center = detection['center']
        corners = detection['corners']
        detection_id = detection['id']
        confidence = detection['confidence']
        
        # Choose color based on confidence
        if confidence > 0.6:
            color = (0, 255, 0)  # Green - high confidence
        elif confidence > 0.4:
            color = (0, 255, 255)  # Yellow - medium confidence
        else:
            color = (0, 165, 255)  # Orange - low confidence
        
        # Draw contour
        if len(corners) >= 4:
            pts = np.array(corners, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(cv2_image, [pts], True, color, 3)
        
        # Draw center point
        cv2.circle(cv2_image, (int(center[0]), int(center[1])), 8, (0, 0, 255), -1)
        
        # Draw ID and confidence with background for better visibility
        text = f"ID:{detection_id} ({confidence:.2f})"
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        cv2.rectangle(cv2_image, 
                     (int(center[0]) + 10, int(center[1]) - 25), 
                     (int(center[0]) + 10 + text_size[0], int(center[1]) - 25 - text_size[1]), 
                     (0, 0, 0), -1)
        
        cv2.putText(cv2_image, text,
                   (int(center[0]) + 15, int(center[1]) - 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

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
                detection_type = detection.get('type', 'unknown')
                detection_id = detection.get('id', '?')
                center = detection.get('center', [0, 0])
                confidence = detection.get('confidence', 0)
                area = detection.get('area', 0)
                
                results_html += f"""
                <div class="detection-item">
                    <div class="detection-id">{detection_type.title()} {detection_id}</div>
                    <div class="detection-pos">Center: ({center[0]:.0f}, {center[1]:.0f})</div>
                    <div class="detection-pos">Area: {area:.0f} pixels</div>
                    <div class="detection-pos">Confidence: {confidence:.2f}</div>
                </div>
                """
            self.detection_list.innerHTML = results_html
        else:
            self.detection_list.innerHTML = "<p>No AprilTags detected in current frame</p>"
    
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
        
        # Detect AprilTag-like patterns
        detections = detector.detect_tags(cv2_image)
        
        # Update UI
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
    detections = process_frame()
    ui.log(f"Photo taken - found {len(detections)} objects")

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

# Main detection loop
async def detection_loop():
    """Main continuous detection loop"""
    while True:
        if detecting:
            process_frame()
        await asyncio.sleep(0.1)  # 10 FPS

async def toggle_debug_handler(e):
    """Toggle debug mode"""
    detector.debug_mode = not detector.debug_mode
    status = "enabled" if detector.debug_mode else "disabled"
    ui.log(f"Debug mode {status}")

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
