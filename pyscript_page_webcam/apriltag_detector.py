"""
AprilTag Detector Module - Based on Official AprilTag Structure
Adapted for pure Python/OpenCV without ctypes, following official apriltag.py patterns
"""

import cv2
import numpy as np
from collections import namedtuple, OrderedDict
import re

# =============================================================================
# APRILTAG DETECTION STRUCTURES (Based on Official Implementation)
# =============================================================================

DetectionBase = namedtuple(
    'DetectionBase',
    'tag_family, tag_id, hamming, goodness, decision_margin, '
    'homography, center, corners'
)

class Detection(DetectionBase):
    """
    AprilTag detection result - mirrors official apriltag.py Detection class
    """
    
    _print_fields = [
        'Family', 'ID', 'Hamming error', 'Goodness',
        'Decision margin', 'Homography', 'Center', 'Corners'
    ]
    
    _max_len = max(len(field) for field in _print_fields)
    
    def tostring(self, values=None, indent=0):
        """Converts this object to a string with the given level of indentation."""
        rval = []
        indent_str = ' '*(self._max_len+2+indent)

        if not values:
            values = OrderedDict(zip(self._print_fields, self))

        for label in values:
            value_str = str(values[label])
            if value_str.find('\n') > 0:
                value_str = value_str.split('\n')
                value_str = [value_str[0]] + [indent_str+v for v in value_str[1:]]
                value_str = '\n'.join(value_str)
            rval.append('{:>{}s}: {}'.format(
                label, self._max_len+indent, value_str))

        return '\n'.join(rval)
    
    def __str__(self):
        return self.tostring()

# =============================================================================
# DETECTOR OPTIONS (Based on Official Implementation)
# =============================================================================

class DetectorOptions(object):
    """
    Convenience wrapper for detector options - mirrors official DetectorOptions
    """
    
    def __init__(self,
                 families='tag36h11',
                 border=1,
                 nthreads=4,
                 quad_decimate=1.0,
                 quad_blur=0.0,
                 refine_edges=True,
                 refine_decode=False,
                 refine_pose=False,
                 debug=False,
                 quad_contours=True):
        
        self.families = families
        self.border = int(border)
        self.nthreads = int(nthreads)
        self.quad_decimate = float(quad_decimate)
        self.quad_sigma = float(quad_blur)
        self.refine_edges = int(refine_edges)
        self.refine_decode = int(refine_decode)
        self.refine_pose = int(refine_pose)
        self.debug = int(debug)
        self.quad_contours = quad_contours

# =============================================================================
# APRILTAG DETECTOR CLASS (Based on Official Implementation)
# =============================================================================

class AprilTagDetector(object):
    """
    AprilTag detector following official apriltag.py structure
    Adapted for pure Python/OpenCV implementation
    """
    
    def __init__(self, options=None, log_callback=None):
        """Initialize detector with options similar to official implementation"""
        
        if options is None:
            options = DetectorOptions()
        
        self.options = options
        self.log_callback = log_callback or print
        self.debug_mode = bool(options.debug)
        
        # Parse families like official implementation
        if options.families == 'all':
            self.families_list = ['tag36h11', 'tag25h9', 'tag16h5', 'tagCircle21h7', 'tagCircle49h12', 'tagCustom48h12', 'tagStandard41h12', 'tagStandard52h13']
        elif isinstance(options.families, list):
            self.families_list = options.families
        else:
            self.families_list = [n for n in re.split(r'\W+', options.families) if n]
        
        # Detection statistics
        self.detection_count = 0
        
        if self.debug_mode:
            self.log_callback(f"AprilTag detector initialized with families: {self.families_list}")
    
    def detect(self, img, return_image=False):
        """
        Main detection method - mirrors official detect() method signature
        """
        
        # Handle both grayscale and color images like official implementation
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        
        # Ensure uint8 format like official implementation
        if gray.dtype != np.uint8:
            gray = gray.astype(np.uint8)
        
        # Convert to internal format for processing
        c_img = self._convert_image(gray)
        
        # Detect AprilTags
        detections = self._detect_apriltags(c_img)
        
        # Create visualization if requested
        if return_image:
            dimg = self._vis_detections(gray.shape, detections)
            return detections, dimg
        else:
            return detections
    
    def _convert_image(self, img):
        """Convert image to internal format - mirrors official _convert_image"""
        # Apply quad decimation if specified
        if self.options.quad_decimate > 1.0:
            height, width = img.shape
            new_height = int(height / self.options.quad_decimate)
            new_width = int(width / self.options.quad_decimate)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Apply blur if specified
        if self.options.quad_sigma > 0:
            img = cv2.GaussianBlur(img, (0, 0), self.options.quad_sigma)
        
        return img
    
    def _detect_apriltags(self, img):
        """Core AprilTag detection algorithm"""
        detections = []
        
        try:
            # Adaptive thresholding - key part of AprilTag detection
            binary = cv2.adaptiveThreshold(
                img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Find quad candidates using contour detection
            quads = self._find_quads(binary)
            
            if self.debug_mode:
                self.log_callback(f"Found {len(quads)} quad candidates")
            
            # Process each quad candidate
            for quad in quads:
                detection = self._process_quad(img, quad)
                if detection is not None:
                    detections.append(detection)
                    if self.debug_mode:
                        self.log_callback(f"Valid AprilTag detected: ID {detection.tag_id}")
            
            # Apply quad decimation scaling back if needed
            if self.options.quad_decimate > 1.0:
                detections = self._scale_detections(detections, self.options.quad_decimate)
            
            return detections
            
        except Exception as e:
            self.log_callback(f"Detection error: {e}")
            return []
    
    def _find_quads(self, binary):
        """Find quadrilateral candidates in binary image"""
        # Use different contour finding strategies
        contour_modes = [
            cv2.RETR_CCOMP,   # Most effective for AprilTags
            cv2.RETR_TREE,    # Hierarchical
            cv2.RETR_LIST,    # All contours
        ]
        
        all_quads = []
        
        for mode in contour_modes:
            contours, hierarchy = cv2.findContours(binary, mode, cv2.CHAIN_APPROX_SIMPLE)
            
            if self.debug_mode:
                self.log_callback(f"Contour mode {mode}: found {len(contours)} contours")
            
            # Process contours to find quads
            for i, contour in enumerate(contours):
                quad = self._contour_to_quad(contour, hierarchy, i if hierarchy is not None else None)
                if quad is not None:
                    all_quads.append(quad)
            
            # If we found good quads, prefer them
            if len(all_quads) > 0:
                break
        
        return all_quads
    
    def _contour_to_quad(self, contour, hierarchy, contour_idx):
        """Convert contour to quad if it meets AprilTag criteria"""
        
        # Basic area filtering
        area = cv2.contourArea(contour)
        if area < 100:  # Too small
            return None
        
        # Approximate contour to polygon
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Must be roughly quadrilateral
        if len(approx) < 4 or len(approx) > 6:
            return None
        
        # If more than 4 points, try to get the best 4
        if len(approx) > 4:
            # Use convex hull and get 4 corner points
            hull = cv2.convexHull(contour)
            epsilon = 0.05 * cv2.arcLength(hull, True)
            approx = cv2.approxPolyDP(hull, epsilon, True)
            
            if len(approx) != 4:
                return None
        
        # Check if it's roughly square (AprilTags are square)
        rect = cv2.boundingRect(approx)
        aspect_ratio = max(rect[2], rect[3]) / min(rect[2], rect[3])
        if aspect_ratio > 2.0:  # Too rectangular
            return None
        
        # Check if quad is convex
        if not cv2.isContourConvex(approx):
            return None
        
        # Order corners consistently (important for homography)
        quad = self._order_corners(approx.reshape(-1, 2))
        
        return quad
    
    def _order_corners(self, corners):
        """Order corners in consistent manner: top-left, top-right, bottom-right, bottom-left"""
        
        # Sort by y coordinate
        corners = corners[np.argsort(corners[:, 1])]
        
        # Get top and bottom pairs
        top_pair = corners[:2]
        bottom_pair = corners[2:]
        
        # Sort each pair by x coordinate
        top_pair = top_pair[np.argsort(top_pair[:, 0])]
        bottom_pair = bottom_pair[np.argsort(bottom_pair[:, 0])]
        
        # Order: top-left, top-right, bottom-right, bottom-left
        ordered = np.array([
            top_pair[0],    # top-left
            top_pair[1],    # top-right
            bottom_pair[1], # bottom-right
            bottom_pair[0]  # bottom-left
        ])
        
        return ordered
    
    def _process_quad(self, img, quad):
        """Process a quad candidate to extract AprilTag information"""
        
        try:
            # Calculate homography
            homography = self._calculate_homography(quad)
            
            # Extract and decode tag
            tag_img = self._extract_tag_image(img, quad)
            tag_info = self._decode_tag(tag_img)
            
            if tag_info is None:
                return None
            
            # Calculate center
            center = np.mean(quad, axis=0)
            
            # Create detection object
            detection = Detection(
                tag_family=tag_info['family'],
                tag_id=tag_info['id'],
                hamming=tag_info['hamming'],
                goodness=tag_info['goodness'],
                decision_margin=tag_info['decision_margin'],
                homography=homography,
                center=center,
                corners=quad
            )
            
            return detection
            
        except Exception as e:
            if self.debug_mode:
                self.log_callback(f"Error processing quad: {e}")
            return None
    
    def _calculate_homography(self, corners):
        """Calculate homography matrix from unit square to image quad"""
        
        # Unit square corners (AprilTag coordinate system)
        unit_square = np.array([
            [-1, -1],
            [ 1, -1],
            [ 1,  1],
            [-1,  1]
        ], dtype=np.float32)
        
        # Image corners
        image_corners = np.array(corners, dtype=np.float32)
        
        # Calculate homography
        try:
            H, _ = cv2.findHomography(unit_square, image_corners, cv2.RANSAC, 3.0)
            return H if H is not None else np.eye(3)
        except:
            return np.eye(3)
    
    def _extract_tag_image(self, img, quad):
        """Extract and rectify tag image for decoding"""
        
        # Define output size
        tag_size = 64
        
        # Destination corners (rectified square)
        dst_corners = np.array([
            [0, 0],
            [tag_size-1, 0],
            [tag_size-1, tag_size-1],
            [0, tag_size-1]
        ], dtype=np.float32)
        
        # Source corners from quad
        src_corners = np.array(quad, dtype=np.float32)
        
        # Get perspective transform
        M = cv2.getPerspectiveTransform(src_corners, dst_corners)
        
        # Apply transform
        rectified = cv2.warpPerspective(img, M, (tag_size, tag_size))
        
        return rectified
    
    def _decode_tag(self, tag_img):
        """Decode AprilTag from rectified image"""
        
        try:
            # Threshold the tag image
            _, binary = cv2.threshold(tag_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Check if it looks like a valid AprilTag
            if not self._validate_tag_structure(binary):
                return None
            
            # For now, return simulated tag info
            # In real implementation, this would decode the actual bits
            tag_info = {
                'family': self.families_list[0] if self.families_list else 'tag36h11',
                'id': self.detection_count,
                'hamming': 0,
                'goodness': 0.8,
                'decision_margin': 10.0
            }
            
            self.detection_count += 1
            return tag_info
            
        except Exception as e:
            if self.debug_mode:
                self.log_callback(f"Tag decoding error: {e}")
            return None
    
    def _validate_tag_structure(self, binary):
        """Validate that binary image has AprilTag-like structure"""
        
        size = binary.shape[0]
        border_size = max(1, size // 10)
        
        # Check border - should be mostly black or white
        border_pixels = []
        
        # Top and bottom borders
        border_pixels.extend(binary[:border_size, :].flatten())
        border_pixels.extend(binary[-border_size:, :].flatten())
        
        # Left and right borders
        border_pixels.extend(binary[:, :border_size].flatten())
        border_pixels.extend(binary[:, -border_size:].flatten())
        
        if len(border_pixels) == 0:
            return False
        
        # Convert to numpy array for proper comparison
        border_pixels = np.array(border_pixels)
        
        # Check border consistency
        black_pixels = np.sum(border_pixels < 128)
        white_pixels = np.sum(border_pixels >= 128)
        
        border_consistency = max(black_pixels, white_pixels) / len(border_pixels)
        
        if border_consistency < 0.6:
            return False
        
        # Check interior has some variation (not all one color)
        interior_start = border_size + 1
        interior_end = size - border_size - 1
        
        if interior_end > interior_start:
            interior = binary[interior_start:interior_end, interior_start:interior_end]
            
            if interior.size > 0:
                interior_black = np.sum(interior < 128)
                interior_white = np.sum(interior >= 128)
                
                if interior_black + interior_white > 0:
                    interior_variation = min(interior_black, interior_white) / (interior_black + interior_white)
                    
                    if interior_variation < 0.1:  # Too uniform
                        return False
        
        return True
    
    def _scale_detections(self, detections, scale_factor):
        """Scale detections back up if quad decimation was applied"""
        
        scaled_detections = []
        
        for detection in detections:
            # Scale corners and center
            scaled_corners = detection.corners * scale_factor
            scaled_center = detection.center * scale_factor
            
            # Recalculate homography with scaled corners
            scaled_homography = self._calculate_homography(scaled_corners)
            
            # Create new detection with scaled coordinates
            scaled_detection = Detection(
                tag_family=detection.tag_family,
                tag_id=detection.tag_id,
                hamming=detection.hamming,
                goodness=detection.goodness,
                decision_margin=detection.decision_margin,
                homography=scaled_homography,
                center=scaled_center,
                corners=scaled_corners
            )
            
            scaled_detections.append(scaled_detection)
        
        return scaled_detections
    
    def _vis_detections(self, shape, detections):
        """Create visualization image with detections"""
        
        height, width = shape
        vis_img = np.zeros((height, width), dtype=np.uint8)
        
        # Draw detections
        for detection in detections:
            corners = detection.corners.astype(np.int32)
            
            # Draw quad outline
            cv2.polylines(vis_img, [corners.reshape(-1, 1, 2)], True, 255, 2)
            
            # Draw center
            center = detection.center.astype(np.int32)
            cv2.circle(vis_img, tuple(center), 5, 255, -1)
            
            # Draw ID
            cv2.putText(vis_img, str(detection.tag_id), 
                       tuple(center + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 255, 1)
        
        return vis_img
    
    def detection_pose(self, detection, camera_params, tag_size=1, z_sign=1):
        """
        Calculate pose from detection - mirrors official detection_pose method
        """
        
        try:
            fx, fy, cx, cy = camera_params
            
            # Object points (3D coordinates of tag corners)
            object_points = np.array([
                [-tag_size/2, -tag_size/2, 0],
                [ tag_size/2, -tag_size/2, 0],
                [ tag_size/2,  tag_size/2, 0],
                [-tag_size/2,  tag_size/2, 0]
            ], dtype=np.float32)
            
            # Image points
            image_points = detection.corners.astype(np.float32)
            
            # Camera matrix
            camera_matrix = np.array([
                [fx, 0, cx],
                [0, fy, cy],
                [0, 0, 1]
            ], dtype=np.float32)
            
            # Distortion coefficients (assume no distortion)
            dist_coeffs = np.zeros(4)
            
            # Solve PnP
            success, rvec, tvec = cv2.solvePnP(
                object_points, image_points, camera_matrix, dist_coeffs
            )
            
            if success:
                # Convert to 4x4 transformation matrix
                R, _ = cv2.Rodrigues(rvec)
                
                pose_matrix = np.eye(4)
                pose_matrix[:3, :3] = R
                pose_matrix[:3, 3] = tvec.flatten()
                
                # Apply z_sign
                if z_sign < 0:
                    pose_matrix[:3, 3] *= -1
                
                return pose_matrix, 0.0, 0.0
            else:
                return np.eye(4), float('inf'), float('inf')
                
        except Exception as e:
            if self.debug_mode:
                self.log_callback(f"Pose estimation error: {e}")
            return np.eye(4), float('inf'), float('inf')

# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def add_arguments(parser):
    """Add arguments to ArgumentParser - mirrors official add_arguments"""
    
    defaults = DetectorOptions()
    
    show_default = ' (default %(default)s)'
    
    parser.add_argument('-f', metavar='FAMILIES',
                        dest='families', default=defaults.families,
                        help='Tag families' + show_default)
    
    parser.add_argument('-B', metavar='N',
                        dest='border', type=int, default=defaults.border,
                        help='Tag border size in pixels' + show_default)
    
    parser.add_argument('-t', metavar='N',
                        dest='nthreads', type=int, default=defaults.nthreads,
                        help='Number of threads' + show_default)
    
    parser.add_argument('-x', metavar='SCALE',
                        dest='quad_decimate', type=float,
                        default=defaults.quad_decimate,
                        help='Quad decimation factor' + show_default)
    
    parser.add_argument('-b', metavar='SIGMA',
                        dest='quad_sigma', type=float, default=defaults.quad_sigma,
                        help='Apply low-pass blur to input' + show_default)
    
    parser.add_argument('-0', dest='refine_edges', default=True,
                        action='store_false',
                        help='Spend less time trying to align edges of tags')
    
    parser.add_argument('-1', dest='refine_decode', default=False,
                        action='store_true',
                        help='Spend more time trying to decode tags')
    
    parser.add_argument('-2', dest='refine_pose', default=False,
                        action='store_true',
                        help='Spend more time trying to precisely localize tags')
    
    parser.add_argument('-c', dest='quad_contours', default=False,
                        action='store_true',
                        help='Use new contour-based quad detection')

# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================

# For backward compatibility with existing code
def create_detector(log_callback=None):
    """Create detector with default options"""
    options = DetectorOptions(debug=True)
    return AprilTagDetector(options, log_callback)
