from pyscript import document, window, when
import json
import random
import string
import asyncio

print("=== WebRTC Video Streaming ===")

# Import channel for signaling - CORRECT FORMAT
try:
    import channel
    print("Channel module imported")
    signaling_channel = channel.CEEO_Channel(
        "hackathon", 
        "@chrisrogers", 
        "talking-on-a-channel",
        divName='all_things_channels',
        suffix='_test'
    )
    print("Signaling channel created")
except Exception as e:
    print(f"Channel setup failed: {e}")
    signaling_channel = None

# Import video module
try:
    import video
    print("Video module imported")
    video_sender = video.CEEO_Video('video_sender', suffix="sender")
    print("Video sender created")
except Exception as e:
    print(f"Video setup failed: {e}")
    video_sender = None

# Global WebRTC variables
peer_connection = None
local_stream = None
room_id = None
is_sender = False

def log(message):
    """Log messages to console"""
    print(f"[WebRTC] {message}")

def update_status(element_id, message):
    """Update status display"""
    try:
        element = document.getElementById(element_id)
        if element:
            element.textContent = message
    except Exception as e:
        log(f"Status update error: {e}")

async def handle_signaling_message(message):
    """Handle incoming signaling messages from channel - following OpenMV example pattern"""
    global room_id  # Declare once at the top of the function
    
    try:
        if message['type'] == 'data' and 'payload' in message:
            payload_data = json.loads(message['payload'])
            topic = payload_data['topic']
            value = payload_data['value']
            
            log(f"Received message on topic: {topic}")
            
            # Handle WebRTC signaling messages - any room starting with /webrtc/
            if topic.startswith('/webrtc/'):
                room_from_topic = topic.replace('/webrtc/', '')
                log(f"WebRTC message for room: {room_from_topic}")
                
                # If we're a receiver and don't have a room yet, auto-detect from first message
                if not is_sender and not room_id:
                    room_id = room_from_topic
                    log(f"Auto-detected room ID: {room_id}")
                
                # Process WebRTC data if it's for our room or we're not in a room yet
                if room_id == room_from_topic or not room_id:
                    log(f"Processing WebRTC message: {value.get('type', 'unknown')}")
                    await handle_signaling_data(value)
                else:
                    log(f"Ignoring message for different room: {room_from_topic} (ours: {room_id})")
                    
            else:
                log(f"Non-WebRTC message on topic: {topic}")
                
    except Exception as e:
        log(f"Signaling message error: {e}")
        log(f"Message was: {message}")

async def handle_signaling_data(data):
    """Handle incoming WebRTC signaling data"""
    try:
        message_type = data.get('type', 'unknown')
        log(f"Processing {message_type}")
        
        if message_type == 'offer':
            # Receiver: handle incoming offer
            await create_peer_connection()
            remote_desc = window.RTCSessionDescription.new(data)
            await peer_connection.setRemoteDescription(remote_desc)
            await send_answer()
            
        elif message_type == 'answer':
            # Sender: handle incoming answer
            remote_desc = window.RTCSessionDescription.new(data)
            await peer_connection.setRemoteDescription(remote_desc)
            log("Answer processed - connection should establish")
            
        elif message_type == 'candidate':
            # Both: handle ICE candidates
            ice_candidate = window.RTCIceCandidate.new(data['candidate'])
            await peer_connection.addIceCandidate(ice_candidate)
            log("ICE candidate added")
            
    except Exception as e:
        log(f"Signaling data error: {e}")

async def create_peer_connection():
    """Create RTCPeerConnection"""
    global peer_connection
    
    try:
        log("Creating peer connection...")
        
        # WebRTC config with STUN server
        pc_config = {
            'iceServers': [{'urls': 'stun:stun.l.google.com:19302'}]
        }
        
        # Use .new() for JavaScript constructors in PyScript
        peer_connection = window.RTCPeerConnection.new(pc_config)
        
        # Set up event handlers
        peer_connection.onicecandidate = on_ice_candidate
        peer_connection.ontrack = on_track
        peer_connection.onconnectionstatechange = on_connection_state_change
        
        # Add local stream tracks if we're the sender
        if is_sender and local_stream:
            tracks = local_stream.getTracks()
            for track in tracks:
                peer_connection.addTrack(track, local_stream)
                log(f"Added track: {track.kind}")
        
        log("Peer connection created successfully")
        
    except Exception as e:
        log(f"Peer connection error: {e}")

def on_ice_candidate(event):
    """Handle ICE candidate events"""
    try:
        if event.candidate:
            candidate_data = {
                'type': 'candidate',
                'candidate': {
                    'candidate': event.candidate.candidate,
                    'sdpMid': event.candidate.sdpMid,
                    'sdpMLineIndex': event.candidate.sdpMLineIndex
                }
            }
            # Send via channel
            asyncio.create_task(send_signaling_data(candidate_data))
            log("ICE candidate sent")
    except Exception as e:
        log(f"ICE candidate error: {e}")

def on_track(event):
    """Handle remote stream"""
    try:
        log("Received remote stream!")
        remote_video = document.getElementById('remoteVideo')
        if remote_video:
            remote_video.srcObject = event.streams[0]
            update_status("receiverStatus", "Status: Receiving live video!")
    except Exception as e:
        log(f"Remote track error: {e}")

def on_connection_state_change(event):
    """Handle connection state changes"""
    try:
        state = peer_connection.connectionState
        log(f"Connection state: {state}")
        
        if state == "connected":
            if is_sender:
                update_status("streamStatus", "Connected! Streaming live video")
            else:
                update_status("receiverStatus", "Connected! Receiving stream")
        elif state == "failed":
            if is_sender:
                update_status("streamStatus", "Connection failed")
            else:
                update_status("receiverStatus", "Connection failed")
        elif state == "disconnected":
            if is_sender:
                update_status("streamStatus", "Disconnected")
            else:
                update_status("receiverStatus", "Disconnected")
                
    except Exception as e:
        log(f"Connection state error: {e}")

async def send_signaling_data(data):
    """Send data via signaling channel"""
    try:
        if signaling_channel and room_id:
            await signaling_channel.post(f'/webrtc/{room_id}', data)
            log(f"Sent: {data.get('type', 'unknown')}")
        else:
            log("Cannot send - no channel or room ID")
    except Exception as e:
        log(f"Send signaling data error: {e}")

async def send_offer():
    """Create and send WebRTC offer"""
    try:
        log("Creating offer...")
        offer = await peer_connection.createOffer()
        await peer_connection.setLocalDescription(offer)
        
        offer_data = {
            'type': 'offer',
            'sdp': offer.sdp
        }
        await send_signaling_data(offer_data)
        log("Offer sent")
        
    except Exception as e:
        log(f"Send offer error: {e}")

async def send_answer():
    """Create and send WebRTC answer"""
    try:
        log("Creating answer...")
        answer = await peer_connection.createAnswer()
        await peer_connection.setLocalDescription(answer)
        
        answer_data = {
            'type': 'answer',
            'sdp': answer.sdp
        }
        await send_signaling_data(answer_data)
        log("Answer sent")
        
    except Exception as e:
        log(f"Send answer error: {e}")

async def start_streaming():
    """Start streaming as sender"""
    global room_id, is_sender, local_stream
    
    try:
        # Get local stream from video sender
        if not video_sender or not video_sender.connected:
            window.alert("Please start camera first!")
            return
            
        local_stream = video_sender.local_stream
        if not local_stream:
            window.alert("No camera stream available!")
            return
        
        # Set sender state
        is_sender = True
        
        # Generate room ID - fix for PyScript (no random.choices)
        chars = string.ascii_lowercase + string.digits
        room_id = ''.join(random.choice(chars) for _ in range(6))
        
        log(f"Starting stream with room ID: {room_id}")
        update_status("senderStatus", "Status: Creating stream...")
        
        # Create peer connection and send offer
        await create_peer_connection()
        await send_offer()
        
        # Show room info
        document.getElementById("roomId").textContent = room_id.upper()
        document.getElementById("roomInfo").style.display = "block"
        document.getElementById("startStreaming").disabled = True
        
        update_status("senderStatus", f"Status: Streaming (Room: {room_id.upper()})")
        
    except Exception as e:
        log(f"Streaming error: {e}")
        update_status("senderStatus", f"Error: {e}")

async def join_stream():
    """Join stream as receiver"""
    global room_id, is_sender
    
    room_id = document.getElementById("roomInput").value.strip().lower()
    if not room_id:
        window.alert("Please enter a Room ID")
        return
        
    try:
        is_sender = False
        log(f"Joining stream: {room_id}")
        update_status("receiverStatus", "Status: Waiting for stream...")
        
        # No need to set topics - callback handles everything!
        log(f"Ready to receive WebRTC messages for room: {room_id}")
        
        document.getElementById("joinStream").disabled = True
        document.getElementById("roomInput").disabled = True
        
        update_status("receiverStatus", "Status: Ready to receive...")
        
    except Exception as e:
        log(f"Join error: {e}")
        update_status("receiverStatus", f"Error: {e}")

# Set up event handlers
@when("click", "#startStreaming")
async def on_start_streaming(event):
    await start_streaming()

@when("click", "#joinStream") 
async def on_join_stream(event):
    await join_stream()

# Initialize when DOM is ready
@when("DOMContentLoaded", document)
async def initialize():
    log("Initializing WebRTC app...")
    
    try:
        # Set up signaling channel callback immediately - like OpenMV example
        if signaling_channel:
            signaling_channel.callback = handle_signaling_message
            log("Signaling callback set - will handle ALL incoming messages")
        else:
            log("ERROR: signaling_channel is None!")
        
        log("WebRTC app initialized")
        
    except Exception as e:
        log(f"Initialization error: {e}")

print("=== WebRTC Setup Complete ===")
