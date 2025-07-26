from pyscript import document, window
import asyncio
import json

print("=== Robot Controller & OpenMV Camera ===")

# Configuration
ACCELERATION_RATE = 50
UPDATE_INTERVAL = 50
MAX_VALUE = 1000

# Import channel
import channel
signaling_channel = channel.CEEO_Channel(
    "hackathon", 
    "@chrisrogers", 
    "talking-on-a-channel",
    divName='all_things_channels',
    suffix='_controller'
)

signaling_channel.topic.value = '/default'

# Global variables
current_x = 0
current_y = 0
keys_pressed = set()
movement_timer = None
image_count = 0
selected_controller = "Controller_1"  # Default controller

def update_display():
    """Update coordinate display"""
    try:
        document.getElementById("x-value").textContent = str(int(current_x))
        document.getElementById("y-value").textContent = str(int(current_y))
        document.getElementById("active-controller").textContent = selected_controller
    except Exception as e:
        print(f"Display error: {e}")

def handle_controller_change():
    """Handle controller dropdown change"""
    global selected_controller
    try:
        dropdown = document.getElementById("controller-select")
        selected_controller = dropdown.value
        update_display()
        print(f"Controller changed to: {selected_controller}")
    except Exception as e:
        print(f"Controller change error: {e}")

def calculate_target_values():
    """Calculate target values based on pressed keys"""
    target_x = 0
    target_y = 0
    
    if 'w' in keys_pressed:
        target_y -= MAX_VALUE
    if 's' in keys_pressed:
        target_y += MAX_VALUE
    if 'a' in keys_pressed:
        target_x -= MAX_VALUE
    if 'd' in keys_pressed:
        target_x += MAX_VALUE
    
    return target_x, target_y

def update_movement():
    """Update movement values"""
    global current_x, current_y
    
    target_x, target_y = calculate_target_values()
    
    def move_toward(current, target, rate):
        if current < target:
            return min(current + rate, target)
        elif current > target:
            return max(current - rate, target)
        return current
    
    current_x = move_toward(current_x, target_x, ACCELERATION_RATE)
    current_y = move_toward(current_y, target_y, ACCELERATION_RATE)
    
    update_display()
    asyncio.create_task(send_controller_data())
    
    if len(keys_pressed) == 0 and current_x == 0 and current_y == 0:
        stop_movement_timer()

def start_movement_timer():
    """Start movement timer"""
    global movement_timer
    if movement_timer is None:
        window.eval(f'''
        window.movementTimer = setInterval(function() {{
            if (window.pythonUpdateMovement) {{
                window.pythonUpdateMovement();
            }}
        }}, {UPDATE_INTERVAL});
        ''')
        movement_timer = True
        window.pythonUpdateMovement = update_movement

def stop_movement_timer():
    """Stop movement timer"""
    global movement_timer
    if movement_timer is not None:
        window.eval('''
        if (window.movementTimer) {
            clearInterval(window.movementTimer);
            window.movementTimer = null;
        }
        ''')
        movement_timer = None

def update_key_visual(key, pressed):
    """Update key visual state"""
    try:
        key_element = document.getElementById(f"key-{key}")
        if key_element:
            if pressed:
                key_element.classList.add("pressed")
            else:
                key_element.classList.remove("pressed")
    except:
        pass

async def send_controller_data():
    """Send controller data to selected controller"""
    try:
        data = {"x": int(current_x), "y": int(current_y)}
        topic = f"/{selected_controller}/data"
        await signaling_channel.post(topic, data)
        # Uncomment the line below if you also want to send to Car_Location_1/All
        # await signaling_channel.post("/Car_Location_1/All", data)
    except Exception as e:
        print(f"Send error: {e}")

def handle_keydown(key):
    """Handle keydown"""
    if key in ['w', 'a', 's', 'd']:
        was_empty = len(keys_pressed) == 0
        keys_pressed.add(key)
        update_key_visual(key, True)
        if was_empty:
            start_movement_timer()

def handle_keyup(key):
    """Handle keyup"""
    if key in ['w', 'a', 's', 'd']:
        keys_pressed.discard(key)
        update_key_visual(key, False)

def handle_mouse_down(key):
    """Handle mouse down"""
    if key in ['w', 'a', 's', 'd']:
        was_empty = len(keys_pressed) == 0
        keys_pressed.add(key)
        update_key_visual(key, True)
        if was_empty:
            start_movement_timer()

def handle_mouse_up(key):
    """Handle mouse up"""
    if key in ['w', 'a', 's', 'd']:
        keys_pressed.discard(key)
        update_key_visual(key, False)

# Camera functions
def update_camera_status(message):
    """Update camera status"""
    try:
        document.getElementById("cameraStatus").textContent = f"Status: {message}"
    except:
        pass

def grab_camera(data):
    """Display received camera image"""
    global image_count
    try:
        data_url = f"data:image/jpeg;base64,{data}"
        img = document.getElementById("displayImage")
        container = document.getElementById("imageContainer")
        no_image_msg = document.getElementById("noImageMessage")
        
        # Hide the "no image" message
        if no_image_msg:
            no_image_msg.style.display = "none"
        
        # Set the image source and show it
        img.src = data_url
        img.style.display = "block"
        
        # Update image count and status
        image_count += 1
        update_camera_status(f"Receiving live feed - Frame {image_count}")
        
    except Exception as e:
        print(f"Camera display error: {e}")
        update_camera_status("Error displaying camera feed")

def camera_callback(message):
    """Handle camera messages from OpenMV"""
    try:
        if message['type'] == 'data' and 'payload' in message:
            payload_data = json.loads(message['payload'])
            topic = payload_data.get('topic', '')
            value = payload_data.get('value', '')
            
            if topic == '/camera' and value:
                grab_camera(value)
                
    except Exception as e:
        print(f"Camera callback error: {e}")

def setup_events():
    """Setup event handlers"""
    # Store functions for JavaScript
    window.pythonKeyDown = handle_keydown
    window.pythonKeyUp = handle_keyup
    window.pythonMouseDown = handle_mouse_down
    window.pythonMouseUp = handle_mouse_up
    window.pythonUpdateCameraStatus = update_camera_status
    window.pythonControllerChange = handle_controller_change
    
    # Setup JavaScript event handlers
    window.eval('''
    document.addEventListener('keydown', function(event) {
        const key = event.key.toLowerCase();
        if (['w', 'a', 's', 'd'].includes(key) && !event.repeat) {
            window.pythonKeyDown(key);
        }
    });
    
    document.addEventListener('keyup', function(event) {
        const key = event.key.toLowerCase();
        if (['w', 'a', 's', 'd'].includes(key)) {
            window.pythonKeyUp(key);
        }
    });
    
    document.querySelectorAll('.arrow-key').forEach(function(element) {
        element.addEventListener('mousedown', function() {
            const key = this.getAttribute('data-key');
            if (key) window.pythonMouseDown(key);
        });
        
        element.addEventListener('mouseup', function() {
            const key = this.getAttribute('data-key');
            if (key) window.pythonMouseUp(key);
        });
        
        element.addEventListener('mouseleave', function() {
            const key = this.getAttribute('data-key');
            if (key) window.pythonMouseUp(key);
        });
    });
    
    // Add controller dropdown change handler
    const controllerSelect = document.getElementById('controller-select');
    if (controllerSelect) {
        controllerSelect.addEventListener('change', function() {
            window.pythonControllerChange();
        });
    }
    ''')

def initialize():
    """Initialize application"""
    stop_movement_timer()
    update_display()
    update_camera_status("Listening for OpenMV camera feed")
    
    # Set up the camera callback
    signaling_channel.callback = camera_callback
    
    def delayed_setup():
        setup_events()
        print("Ready! Use WASD keys or buttons to control robot")
        print("OpenMV camera feed will appear automatically when available")
        print(f"Default controller: {selected_controller}")
    
    window.setTimeout(delayed_setup, 500)

# Initialize
initialize()
print("=== Ready ===")