from pyscript import document, window, when
import asyncio

print("=== Loading video.py ===")

VideoCode = '''    
<h3>Camera Setup</h3>
<video id="local_video_{suffix}" width="300" height="200" autoplay muted style="border: 1px solid #ccc; background: #f0f0f0;"></video>
<br>
<button id="video_btn_{suffix}" class="camera-btn">Start Camera</button>
<div id="live_indicator_{suffix}" class="status-indicator"></div>
<div id="video_status_{suffix}" class="status">Camera: Not connected</div>
<style>
.camera-btn {{ 
    padding: 10px 15px; 
    margin: 10px 5px; 
    background: #28a745; 
    color: white; 
    border: none; 
    border-radius: 4px; 
    cursor: pointer;
}}
.camera-btn:disabled {{ 
    background: #6c757d; 
    cursor: not-allowed;
}}
.status-indicator {{ 
    width: 12px; 
    height: 12px; 
    border-radius: 50%; 
    display: inline-block; 
    margin: 0 8px; 
    background: red; 
    transition: background 0.3s;
}}
</style>
'''

class CEEO_Video:
    def __init__(self, divName, suffix="main"):
        print(f"Creating CEEO_Video with suffix: {suffix}")
        
        self.suffix = suffix
        self.connected = False
        self.local_stream = None
        
        # Set up HTML
        self.videodiv = document.getElementById(divName)
        if not self.videodiv:
            print(f"Div not found: {divName}")
            return
            
        self.videodiv.innerHTML = VideoCode.format(suffix=suffix)
        print(f"Video HTML inserted for {suffix}")
        
        # Get UI elements
        self.video_element = document.getElementById(f'local_video_{suffix}')
        self.connect_btn = document.getElementById(f'video_btn_{suffix}')
        self.status_indicator = document.getElementById(f'live_indicator_{suffix}')
        self.video_status = document.getElementById(f'video_status_{suffix}')
        
        if not all([self.video_element, self.connect_btn, self.status_indicator, self.video_status]):
            print("Some UI elements not found")
            return
        
        # Set up event handler
        self.connect_btn.onclick = self.toggle_camera
        
        # Test video element
        self.test_video_element()
        
        print("CEEO_Video initialized successfully")

    def test_video_element(self):
        """Test if video element is working"""
        try:
            if self.video_element:
                self.video_element.style.backgroundColor = '#f0f0f0'
                print("Video element test passed")
            else:
                print("Video element not found")
        except Exception as e:
            print(f"Video element test failed: {e}")

    async def toggle_camera(self, event):
        """Toggle camera on/off"""
        try:
            if self.connected:
                await self.disconnect_camera()
            else:
                await self.connect_camera()
                
            # Enable/disable streaming button based on camera status
            streaming_btn = document.getElementById("startStreaming")
            if streaming_btn:
                streaming_btn.disabled = not self.connected
                
        except Exception as e:
            print(f"Camera toggle error: {e}")
            self.update_status("Camera: Error", "red")

    async def connect_camera(self):
        """Connect to user's camera"""
        try:
            print("Requesting camera access...")
            self.update_status("Camera: Connecting...", "orange")
            
            # Check if getUserMedia is available
            if not hasattr(window.navigator, 'mediaDevices'):
                raise Exception("MediaDevices API not available")
                
            if not hasattr(window.navigator.mediaDevices, 'getUserMedia'):
                raise Exception("getUserMedia not available")
            
            # Request camera only - no audio needed
            constraints = {
                'video': True,
                'audio': False
            }
            
            print("Calling getUserMedia...")
            self.local_stream = await window.navigator.mediaDevices.getUserMedia(constraints)
            
            if not self.local_stream:
                raise Exception("Failed to get media stream")
            
            # Set video source
            self.video_element.srcObject = self.local_stream
            
            # Update state
            self.connected = True
            self.connect_btn.innerHTML = 'Disconnect Camera'
            self.update_status("Camera: Connected", "green")
            
            print("Camera connected successfully")
            
            # Log stream info
            tracks = self.local_stream.getTracks()
            for track in tracks:
                print(f"Track: {track.kind} - {track.label}")
            
        except Exception as e:
            error_msg = str(e)
            print(f"Camera connection failed: {error_msg}")
            self.update_status(f"Camera: Error - {error_msg}", "red")
            
            # Show user-friendly error
            if "Permission denied" in error_msg:
                window.alert("Camera permission denied. Please allow camera access and try again.")
            elif "not found" in error_msg:
                window.alert("No camera found. Please connect a camera and try again.")
            else:
                window.alert(f"Camera error: {error_msg}")

    async def disconnect_camera(self):
        """Disconnect camera"""
        try:
            print("Disconnecting camera...")
            
            # Stop all tracks
            if self.local_stream:
                tracks = self.local_stream.getTracks()
                for track in tracks:
                    track.stop()
                    print(f"Stopped track: {track.kind}")
                
                # Clear video source
                self.video_element.srcObject = None
                self.local_stream = None
            
            # Update state
            self.connected = False
            self.connect_btn.innerHTML = 'Start Camera'
            self.update_status("Camera: Disconnected", "red")
            
            print("Camera disconnected")
            
        except Exception as e:
            print(f"Camera disconnect error: {e}")

    def update_status(self, message, color="gray"):
        """Update status display"""
        try:
            if self.video_status:
                self.video_status.textContent = message
            
            if self.status_indicator:
                if color == "green":
                    self.status_indicator.style.background = "#28a745"
                elif color == "red":
                    self.status_indicator.style.background = "#dc3545"
                elif color == "orange":
                    self.status_indicator.style.background = "#ffc107"
                else:
                    self.status_indicator.style.background = "#6c757d"
                    
        except Exception as e:
            print(f"Status update error: {e}")

    def get_stream(self):
        """Get the current media stream"""
        return self.local_stream if self.connected else None

print("video.py loaded successfully")
