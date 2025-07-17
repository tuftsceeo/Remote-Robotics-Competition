from pyscript import document, window
import asyncio
import json

print("=== Robot Controller & Video Receiver ===")

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

# Global variables
current_x = 0
current_y = 0
keys_pressed = set()
movement_timer = None
video_room_id = None
video_ready = False
peer_connection = False
offer_processed = False

def update_display():
    """Update coordinate display"""
    try:
        document.getElementById("x-value").textContent = str(int(current_x))
        document.getElementById("y-value").textContent = str(int(current_y))
    except Exception as e:
        print(f"Display error: {e}")

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
    """Send controller data"""
    try:
        data = {"x": int(current_x), "y": int(current_y)}
        await signaling_channel.post("/Controller/data", data)
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

# Video functions
def update_video_status(message):
    """Update video status"""
    try:
        document.getElementById("videoStatus").textContent = f"Status: {message}"
    except:
        pass

def combined_signaling_callback(message):
    """Handle signaling messages"""
    try:
        if message['type'] == 'data' and 'payload' in message:
            payload_data = json.loads(message['payload'])
            topic = payload_data['topic']
            value = payload_data['value']
            
            if video_ready and video_room_id and topic == f'/webrtc/{video_room_id}':
                message_type = value.get('type', 'unknown')
                
                if message_type == 'offer':
                    global offer_processed
                    if not offer_processed:
                        offer_processed = True
                        update_video_status("Processing offer...")
                        asyncio.create_task(handle_webrtc_offer(value))
                        
                elif message_type == 'candidate':
                    if peer_connection:
                        asyncio.create_task(handle_ice_candidate_from_sender(value['candidate']))
                        
    except Exception as e:
        print(f"Signaling error: {e}")

async def handle_webrtc_offer(offer_data):
    """Handle WebRTC offer"""
    if not peer_connection:
        await create_peer_connection()
    await process_offer_and_create_answer(offer_data)

async def create_peer_connection():
    """Create peer connection"""
    global peer_connection
    if peer_connection:
        return
        
    window.eval('''
    try {
        const pcConfig = {iceServers: [{urls: 'stun:stun.l.google.com:19302'}]};
        window.receiverPeerConnection = new RTCPeerConnection(pcConfig);
        
        window.receiverPeerConnection.onicecandidate = function(event) {
            if (event.candidate && !window.receiverConnectionEstablished) {
                const candidateData = {
                    type: 'candidate',
                    candidate: {
                        candidate: event.candidate.candidate,
                        sdpMid: event.candidate.sdpMid,
                        sdpMLineIndex: event.candidate.sdpMLineIndex
                    }
                };
                window.candidateToSend = JSON.stringify(candidateData);
                window.pythonSendCandidate();
            }
        };
        
        window.receiverPeerConnection.ontrack = function(event) {
            const remoteVideo = document.getElementById('remoteVideo');
            if (remoteVideo) {
                remoteVideo.srcObject = event.streams[0];
                window.pythonUpdateVideoStatus('Receiving live video!');
            }
        };
        
        window.receiverPeerConnection.onconnectionstatechange = function(event) {
            const state = window.receiverPeerConnection.connectionState;
            if (state === 'connected') {
                window.receiverConnectionEstablished = true;
                window.pythonUpdateVideoStatus('Connected! Receiving stream');
            } else if (state === 'failed') {
                window.pythonUpdateVideoStatus('Connection failed');
            } else if (state === 'disconnected') {
                window.receiverConnectionEstablished = false;
                window.pythonUpdateVideoStatus('Disconnected');
            }
        };
    } catch (error) {
        console.error('Peer connection error:', error);
    }
    ''')
    peer_connection = True

async def process_offer_and_create_answer(offer_data):
    """Process offer and create answer"""
    window.currentOffer = offer_data
    window.eval('''
    async function processOfferAndAnswer() {
        try {
            const offer = window.currentOffer;
            const remoteDesc = new RTCSessionDescription(offer);
            await window.receiverPeerConnection.setRemoteDescription(remoteDesc);
            
            const answer = await window.receiverPeerConnection.createAnswer();
            await window.receiverPeerConnection.setLocalDescription(answer);
            
            const answerData = {type: 'answer', sdp: answer.sdp};
            window.answerToSend = JSON.stringify(answerData);
            window.pythonSendAnswer();
        } catch (error) {
            console.error('Offer processing error:', error);
        }
    }
    processOfferAndAnswer();
    ''')

async def send_answer():
    """Send answer"""
    try:
        answer_data = json.loads(window.answerToSend)
        await signaling_channel.post(f'/webrtc/{video_room_id}', answer_data)
        update_video_status("Answer sent - establishing connection...")
    except Exception as e:
        print(f"Send answer error: {e}")

async def send_ice_candidate():
    """Send ICE candidate"""
    try:
        candidate_data = json.loads(window.candidateToSend)
        await signaling_channel.post(f'/webrtc/{video_room_id}', candidate_data)
    except Exception as e:
        print(f"Send candidate error: {e}")

async def handle_ice_candidate_from_sender(candidate_data):
    """Handle incoming ICE candidate"""
    window.incomingCandidate = candidate_data
    window.eval('''
    async function handleIncomingCandidate() {
        try {
            if (window.receiverPeerConnection && window.receiverPeerConnection.remoteDescription) {
                const candidate = window.incomingCandidate;
                const iceCandidate = new RTCIceCandidate(candidate);
                await window.receiverPeerConnection.addIceCandidate(iceCandidate);
            }
        } catch (error) {
            console.error('ICE candidate error:', error);
        }
    }
    handleIncomingCandidate();
    ''')

def handle_join_button_click():
    """Handle join button click"""
    global video_room_id, video_ready, offer_processed, peer_connection
    
    room_input = document.getElementById("roomInput")
    video_room_id = room_input.value.strip().lower()
    if not video_room_id:
        return
        
    update_video_status("Joining stream...")
    
    # Reset state
    video_ready = False
    offer_processed = False
    peer_connection = False
    window.receiverConnectionEstablished = False
    
    # Clean up existing connection
    window.eval('''
    if (window.receiverPeerConnection) {
        window.receiverPeerConnection.close();
        window.receiverPeerConnection = null;
    }
    ''')
    
    # Set callback and enable
    signaling_channel.callback = combined_signaling_callback
    video_ready = True
    
    # Disable controls
    document.getElementById("joinStream").disabled = True
    room_input.disabled = True
    
    update_video_status("Listening for WebRTC messages...")

def setup_events():
    """Setup event handlers"""
    # Store functions for JavaScript
    window.pythonKeyDown = handle_keydown
    window.pythonKeyUp = handle_keyup
    window.pythonMouseDown = handle_mouse_down
    window.pythonMouseUp = handle_mouse_up
    window.pythonJoinVideo = handle_join_button_click
    window.pythonSendAnswer = lambda: asyncio.create_task(send_answer())
    window.pythonSendCandidate = lambda: asyncio.create_task(send_ice_candidate())
    window.pythonUpdateVideoStatus = update_video_status
    window.receiverConnectionEstablished = False
    
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
    
    const joinBtn = document.getElementById('joinStream');
    if (joinBtn) {
        joinBtn.addEventListener('click', function() {
            window.pythonJoinVideo();
        });
    }
    ''')

def initialize():
    """Initialize application"""
    stop_movement_timer()
    update_display()
    update_video_status("Ready to join video stream")
    
    def delayed_setup():
        setup_events()
        print("Ready! Use WASD keys or buttons to control robot")
        print("Enter Room ID to receive video stream")
    
    window.setTimeout(delayed_setup, 500)

# Initialize
initialize()
print("=== Ready ===")
