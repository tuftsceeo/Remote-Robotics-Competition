from pyscript import document, window, when
import asyncio 
import struct
import plot
from hubs import hubs
import channel
import json

myChannel = channel.CEEO_Channel("hackathon", "@chrisrogers", "talking-on-a-channel", 
                                 divName = 'all_things_channels', suffix='_test')

red_dot = document.getElementById('red-dot')
tracking_board = document.getElementById('tracking-board')
camera_coords_display = document.getElementById('camera-coords')
board_coords_display = document.getElementById('board-coords')
status_display = document.getElementById('status')

# Store current coordinates
current_coords = {'x': 0, 'y': 0}

# Camera and board dimensions
CAMERA_WIDTH = 640   # VGA width from OpenMV
CAMERA_HEIGHT = 480  # VGA height from OpenMV
BOARD_SIZE = 400     # Size of our visual board in pixels

def update_dot_position():
    board_x = (current_coords['x'] / CAMERA_WIDTH) * BOARD_SIZE
    board_y = (current_coords['y'] / CAMERA_HEIGHT) * BOARD_SIZE
    
    # Clamp coordinates to board boundaries
    board_x = max(10, min(BOARD_SIZE - 10, board_x))  # Keep dot 10px from edges
    board_y = max(10, min(BOARD_SIZE - 10, board_y))
    
    # Update dot position (subtract half dot size since we're positioning from center)
    red_dot.style.left = f"{board_x - 10}px"
    red_dot.style.top = f"{board_y - 10}px"
    
    # Update coordinate displays
    camera_coords_display.innerText = f"Camera: ({current_coords['x']}, {current_coords['y']})"
    board_coords_display.innerText = f"Board: ({int(board_x)}, {int(board_y)})"
    
    # Calculate real-world position (assuming 12" x 12" paper)
    real_x = (current_coords['x'] / CAMERA_WIDTH) * 12
    real_y = (current_coords['y'] / CAMERA_HEIGHT) * 12
    status_display.innerText = f"Real position: ({real_x:.1f}\", {real_y:.1f}\")"

async def fred(message):
    """Async callback function to handle incoming channel messages"""
    try:
        if message['type'] == 'data' and 'payload' in message:
            payload_data = json.loads(message['payload'])
            topic = payload_data['topic']
            value = payload_data['value']
            
            if topic == '/OpenMV/x':
                current_coords['x'] = value
                update_dot_position()
            elif topic == '/OpenMV/y':
                current_coords['y'] = value
                update_dot_position()
                
    except Exception as e:
        print(f"Error processing message: {e}")
        print(f"Message received: {message}")
        status_display.innerText = f"Error: {e}"

myChannel.callback = fred
update_dot_position()
