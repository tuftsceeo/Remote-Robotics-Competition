from pyscript import document, window
import asyncio
import json
import time

# Test what libraries are available
NUMPY_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
    print("✅ NumPy available")
    # Use the callback if it exists
    if hasattr(window, 'onLibraryStatus'):
        window.onLibraryStatus('numpy', 'success', 'Available')
except Exception as e:
    print(f"❌ NumPy failed: {e}")
    if hasattr(window, 'onLibraryStatus'):
        window.onLibraryStatus('numpy', 'error', str(e))

print("🔧 Setting up channel system...")

# Channel setup with error handling
myChannel = None
try:
    import channel
    myChannel = channel.CEEO_Channel("robotics-competition", "@your-username", "apriltag-tracker", 
                                     divName='all_things_channels', suffix='_tracker')
    print("✅ Channel system loaded")
except Exception as e:
    print(f"❌ Channel import error: {e}")
    print("📡 Channels disabled - detection will work but data won't be sent")

class RobotTracker:
    def __init__(self):
        self.robot_count = 0
        self.last_detection_time = 0
        self.detection_history = {}
        
        print("🎯 Robot tracker initialized")
        
    def update_robot_data(self, robot_data):
        """Called from JavaScript when AprilTags are detected"""
        try:
            robot_id = robot_data.get('robot_id', 0)
            position = robot_data.get('position', {})
            rotation = robot_data.get('rotation', 0.0)
            timestamp = robot_data.get('timestamp', time.time())
            confidence = robot_data.get('confidence', 0.0)
            
            # Store detection history
            self.detection_history[robot_id] = {
                'position': position,
                'rotation': rotation,
                'timestamp': timestamp,
                'confidence': confidence
            }
            
            # Send to channels
            asyncio.create_task(self.send_to_channels(robot_id, position, rotation, confidence))
            
            print(f"📍 Robot {robot_id}: x={position.get('x', 0):.2f}, z={position.get('z', 0):.2f}, conf={confidence:.2f}")
            
        except Exception as e:
            print(f"❌ Error updating robot data: {e}")
            import traceback
            traceback.print_exc()
    
    async def send_to_channels(self, robot_id, position, rotation, confidence):
        """Send robot data to channels"""
        if not myChannel:
            print("📡 Channels not available - skipping send")
            return
            
        try:
            # Send individual position components
            await myChannel.post(f'/robot/{robot_id}/position/x', position.get('x', 0.0))
            await myChannel.post(f'/robot/{robot_id}/position/y', position.get('y', 0.1))
            await myChannel.post(f'/robot/{robot_id}/position/z', position.get('z', 0.0))
            await myChannel.post(f'/robot/{robot_id}/rotation', rotation)
            await myChannel.post(f'/robot/{robot_id}/confidence', confidence)
            
            # Send complete robot data as JSON
            robot_data = {
                'id': robot_id,
                'position': position,
                'rotation': rotation,
                'confidence': confidence,
                'timestamp': time.time()
            }
            
            await myChannel.post(f'/robot/{robot_id}/data', json.dumps(robot_data))
            await myChannel.post('/robots/count', len(self.detection_history))
            
            print(f"📡 Sent robot {robot_id} data to channels")
            
        except Exception as e:
            print(f"❌ Channel error: {e}")
    
    def get_robot_status(self):
        """Get current robot tracking status"""
        current_time = time.time()
        active_robots = 0
        
        for robot_id, data in self.detection_history.items():
            if current_time - data['timestamp'] < 2.0:  # Active if seen in last 2 seconds
                active_robots += 1
        
        return {
            'total_robots': len(self.detection_history),
            'active_robots': active_robots,
            'last_update': self.last_detection_time
        }
    
    def clear_old_detections(self):
        """Remove old robot detections"""
        current_time = time.time()
        old_robots = []
        
        for robot_id, data in self.detection_history.items():
            if current_time - data['timestamp'] > 10.0:  # Remove if not seen for 10 seconds
                old_robots.append(robot_id)
        
        for robot_id in old_robots:
            del self.detection_history[robot_id]
            print(f"🗑️ Removed old robot {robot_id}")
    
    def test_system(self):
        """Test function for debugging"""
        print("=== System Test ===")
        print(f"NumPy: {'✅' if NUMPY_AVAILABLE else '❌'}")
        print(f"Robots tracked: {len(self.detection_history)}")
        print(f"Channel connected: {'✅' if myChannel else '❌'}")
        
        # Send test data
        asyncio.create_task(self.send_test_data())
    
    async def send_test_data(self):
        """Send test data to channels"""
        if not myChannel:
            print("📡 Channels not available for test")
            return
            
        try:
            test_position = {'x': 1.0, 'y': 0.1, 'z': 0.5}
            await self.send_to_channels(999, test_position, 45.0, 0.9)
            print("📡 Test data sent")
        except Exception as e:
            print(f"❌ Test error: {e}")

# Create tracker instance
tracker = RobotTracker()

# Make available to JavaScript
window.pyTracker = tracker

# Cleanup task
async def cleanup_task():
    """Periodically clean up old detections"""
    while True:
        await asyncio.sleep(5)  # Run every 5 seconds
        tracker.clear_old_detections()

# Start cleanup task
asyncio.create_task(cleanup_task())

# Channel callback for incoming messages
async def handle_channel_message(message):
    if not myChannel:
        return
        
    try:
        if message['type'] == 'data' and 'payload' in message:
            payload_data = json.loads(message['payload'])
            topic = payload_data.get('topic', '')
            
            if topic == '/robot/command/test':
                tracker.test_system()
            elif topic == '/robot/command/status':
                status = tracker.get_robot_status()
                await myChannel.post('/robot/status', json.dumps(status))
            elif topic == '/robot/command/clear':
                tracker.detection_history.clear()
                print("🗑️ Cleared all robot detections")
                
    except Exception as e:
        print(f"❌ Channel callback error: {e}")

# Set callback only if channel is available
if myChannel:
    myChannel.callback = handle_channel_message

# Update connection status
def update_connection_status():
    try:
        status_div = document.getElementById('connection-status')
        if status_div:
            status_div.innerHTML = f"""
                <span class="status-indicator status-active"></span>
                Channel: Connected to robotics-competition<br>
                <small>Ready to send AprilTag data</small>
            """
    except Exception as e:
        print(f"❌ Status update error: {e}")

# Signal that Python is ready
window.onPythonReady()
update_connection_status()

print("🚀 AprilTag tracker system ready!")
print("📹 Start camera and detection to begin tracking")
print("📡 Robot data will be sent to channels automatically")

# Optional: Send startup notification
async def startup_notification():
    if not myChannel:
        print("📡 Channels not available - skipping startup notification")
        return
        
    try:
        await myChannel.post('/system/status', 'AprilTag tracker started')
        print("📡 Startup notification sent")
    except Exception as e:
        print(f"❌ Startup notification error: {e}")

asyncio.create_task(startup_notification())
