import random
import math
import json
from pyodide.ffi import create_proxy
from pyscript import document, when, window
import js
import channel
import asyncio

# Use the channel class for all WebSocket communication
myChannel = channel.CEEO_Channel("hackathon", "@chrisrogers", "talking-on-a-channel", suffix='_test')

class Car:
    def __init__(self, car_id):
        self.car_id = car_id
        self.element = document.getElementById(f'car-{car_id}')
        self.hitbox_visual = document.getElementById(f'car-hitbox-visual-{car_id}')
        self.x_coord_span = document.getElementById(f'car-{car_id}-x')
        self.y_coord_span = document.getElementById(f'car-{car_id}-y')
        self.bearing_span = document.getElementById(f'car-{car_id}-yaw')
        self.banana_bar = document.getElementById(f'banana-bar-{car_id}')
        self.state = {
            'x': self.element.offsetLeft,
            'y': self.element.offsetTop,
            'angle': 0,
            'orientation': 0
        }
        self.is_stunned = False
        self.stun_start_time = 0
        self.banana_count = 0

    def move_to(self, x, y):
        self.state['x'] = x
        self.state['y'] = y
        self.element.style.left = f"{x}px"
        self.element.style.top = f"{y}px"

    def rotate_to(self, angle):
        self.state['angle'] = angle
        self.element.style.transform = f"translate(-50%, -50%) rotate({self.state['orientation'] + angle}deg)"
        self.hitbox_visual.style.transform = f"translate(-50%, -50%) rotate({self.state['orientation'] + angle}deg)"

    def update_banana_bar(self):
        for i in range(1, 4):
            banana_img = document.getElementById(f'banana-{self.car_id}-{i}')
            if i <= self.banana_count:
                banana_img.src = 'images/banannaPeel.png'
            else:
                banana_img.src = 'images/banannaPeelGreyedOut.png'

# --- Global Variables ---
show_hitboxes = False
peel_counter = 0
debug_panels_visible = True
selected_car_id = 1
master_projector_on = True

# --- Car Instances ---
cars = {
    1: Car(1),
    2: Car(2)
}

# --- Banana Peel Logic ---
peels_container = document.getElementById('peels-container')
hitbox_container = document.getElementById('hitbox-container')

def place_peel(peel_id, location=None):
    peel_html = f'<img src="images/banannaPeel.png" id="{peel_id}" class="peel-image" style="display: none;" onload="positionHitbox(\'{peel_id}\')">'
    hitbox_html = f'<div id="peel-hitbox-{peel_id}" class="peel-hitbox-visual" style="opacity: 0;"></div>'
    peels_container.insertAdjacentHTML('beforeend', peel_html)
    hitbox_container.insertAdjacentHTML('beforeend', hitbox_html)

    peel = document.getElementById(peel_id)
    hitbox_div = document.getElementById(f'peel-hitbox-{peel_id}')

    if peel and hitbox_div:
        if location is None:
            window_width = document.documentElement.clientWidth
            window_height = document.documentElement.clientHeight
            peel_width = peel.width
            peel_height = peel.height
            left = random.randint(0, window_width - peel_width)
            top = random.randint(0, window_height - peel_height)
            location = (top, left)

        peel.style.top = f'{location[0]}px'
        peel.style.left = f'{location[1]}px'

        if show_hitboxes:
            hitbox_div.style.opacity = '1'

        peel.style.display = 'block'

def clear_all_bananas():
    all_peels = document.querySelectorAll('.peel-image[id^="peel-"]')
    for peel in all_peels:
        hitbox_div = document.getElementById(f'peel-hitbox-{peel.id}')
        if peel:
            peel.remove()
        if hitbox_div:
            hitbox_div.remove()

# --- Collision Detection ---
def dot_product(v1, v2):
    return v1[0] * v2[0] + v1[1] * v2[1]

def normalize(v):
    length = math.sqrt(v[0]**2 + v[1]**2)
    if length == 0:
        return (0, 0)
    return (v[0] / length, v[1] / length)

def get_projection(axis, polygon_corners):
    min_proj = dot_product(axis, polygon_corners[0])
    max_proj = min_proj
    for i in range(1, len(polygon_corners)):
        proj = dot_product(axis, polygon_corners[i])
        min_proj = min(min_proj, proj)
        max_proj = max(max_proj, proj)
    return min_proj, max_proj

def check_overlap(min1, max1, min2, max2):
    return max1 >= min2 and max2 >= min1

async def check_for_peel_collision(car):
    # Use fixed dimensions for the car's hitbox
    fixed_car_width = 150
    fixed_car_height = 75

    car_hitbox_width = fixed_car_width * 0.8
    car_hitbox_height = fixed_car_height * 0.5

    # Calculate the rotated hitbox corners
    angle_rad = math.radians(car.state['angle'] + 90) # Add 90 for hitbox orientation

    # Calculate half-dimensions for easier rotation calculation
    half_width = car_hitbox_width / 2
    half_height = car_hitbox_height / 2

    # Car's center point
    cx = car.state['x']
    cy = car.state['y']

    # Calculate rotated corners relative to the center
    corners = []
    for i in range(4):
        x_offset = half_width if (i == 0 or i == 3) else -half_width
        y_offset = half_height if (i == 0 or i == 1) else -half_height

        rotated_x = cx + (x_offset * math.cos(angle_rad)) - (y_offset * math.sin(angle_rad))
        rotated_y = cy + (x_offset * math.sin(angle_rad)) + (y_offset * math.cos(angle_rad))
        corners.append((rotated_x, rotated_y))

    # Car's corners (already calculated)
    car_corners = corners

    # Get all banana peel elements (both static and dynamic)
    all_peels = document.querySelectorAll('.peel-image[id^="peel-"]')

    for peel in all_peels:
        hitbox_div = document.getElementById(f'peel-hitbox-{peel.id}')

        if peel and hitbox_div and peel.style.display == 'block': # Only check visible peels
            peel_rect = peel.getBoundingClientRect()
            peel_hitbox_width = 20
            peel_hitbox_height = 20
            peel_hitbox_left = peel_rect.left + (peel_rect.width - peel_hitbox_width) / 2
            peel_hitbox_top = peel_rect.top + (peel_rect.height - peel_hitbox_height) / 2
            peel_hitbox_right = peel_hitbox_left + peel_hitbox_width
            peel_hitbox_bottom = peel_hitbox_top + peel_hitbox_height

            # Banana peel's corners (axis-aligned)
            peel_corners = [
                (peel_hitbox_left, peel_hitbox_top),
                (peel_hitbox_right, peel_hitbox_top),
                (peel_hitbox_right, peel_hitbox_bottom),
                (peel_hitbox_left, peel_hitbox_bottom)
            ]

            # Define axes for SAT
            car_axes = []
            for i in range(4):
                p1 = car_corners[i]
                p2 = car_corners[(i + 1) % 4]
                edge = (p2[0] - p1[0], p2[1] - p1[1])
                normal = normalize((-edge[1], edge[0])) # Perpendicular vector
                car_axes.append(normal)

            peel_axes = [(1, 0), (0, 1)]

            axes = car_axes + peel_axes

            collision = True
            for axis in axes:
                car_min, car_max = get_projection(axis, car_corners)
                peel_min, peel_max = get_projection(axis, peel_corners)

                if not check_overlap(car_min, car_max, peel_min, peel_max):
                    collision = False
                    break

            if collision:
                peel.remove()
                hitbox_div.remove()
                if master_projector_on:
                    asyncio.create_task(myChannel.post(f"/Car_Location_{car.car_id}/Peeled", "True"))
                    await asyncio.sleep(2)  # Allow time for the message to be sent
                    asyncio.create_task(myChannel.post(f"/Car_Location_{car.car_id}/Peeled", "False"))
                car.is_stunned = True
                car.stun_start_time = js.Date.now()
                return True
    return False

# --- Manual Control & Game Loop ---
keys_pressed = set()

@when("keydown", "body")
def handle_keydown(event):
    global peel_counter, debug_panels_visible
    keys_pressed.add(event.key)
    selected_car = cars[selected_car_id]

    if '1' <= event.key <= '8':
        place_peel(f'peel-{event.key}')
    elif event.key == 'b':
        if selected_car.banana_count > 0:
            peel_counter += 1
            new_peel_id = f'peel-dynamic-{peel_counter}'

            angle = math.radians(selected_car.state['angle'])
            dx = 200 * math.sin(angle)
            dy = 200 * math.cos(angle)

            place_peel(new_peel_id, (selected_car.state['y']-dy, selected_car.state['x']+dx))
            selected_car.banana_count -= 1
            selected_car.update_banana_bar()
    elif event.key == 'c':
        clear_all_bananas()
    elif event.key == 'p':
        if selected_car.banana_count < 3:
            selected_car.banana_count += 1
            selected_car.update_banana_bar()
    elif event.key == 'i':
        debug_panels_visible = not debug_panels_visible
        update_all_debug_elements_visibility()

@when("keyup", "body")
def handle_keyup(event):
    keys_pressed.discard(event.key)

async def game_loop(time):
    step = 2.5
    rotation_step = 5

    for car_id, car in cars.items():
        if car.is_stunned:
            current_time = js.Date.now()
            if current_time - car.stun_start_time >= 1210:
                car.is_stunned = False
        else:
            await check_for_peel_collision(car)

            if car_id == selected_car_id:
                if 'a' in keys_pressed:
                    car.state['angle'] -= rotation_step
                if 'd' in keys_pressed:
                    car.state['angle'] += rotation_step

                if 'w' in keys_pressed or 's' in keys_pressed:
                    angle_rad = math.radians(car.state['angle'])
                    dx = step * math.sin(angle_rad)
                    dy = step * math.cos(angle_rad)

                    if 'w' in keys_pressed:
                        car.state['x'] -= dx
                        car.state['y'] += dy
                    if 's' in keys_pressed:
                        car.state['x'] += dx
                        car.state['y'] -= dy

        car.move_to(car.state['x'], car.state['y'])
        car.rotate_to(car.state['angle'])
        update_car_hitbox(car)

    js.window.requestAnimationFrame(create_proxy(game_loop))

# --- UI Updates ---
def update_car_hitbox(car):
    if show_hitboxes:
        car.hitbox_visual.style.display = 'block'
        fixed_car_width = 150
        fixed_car_height = 75
        car_hitbox_width = fixed_car_width * 0.8
        car_hitbox_height = fixed_car_height * 0.5
        car.hitbox_visual.style.width = f"{car_hitbox_width}px"
        car.hitbox_visual.style.height = f"{car_hitbox_height}px"
        car.hitbox_visual.style.left = f"{car.state['x']}px"
        car.hitbox_visual.style.top = f"{car.state['y']}px"
        car.hitbox_visual.style.transform = f"translate(-50%, -50%) rotate({car.state['angle'] + 90}deg)"
    else:
        car.hitbox_visual.style.display = 'none'

def update_all_debug_elements_visibility():
    for car_id in cars:
        document.getElementById(f'status-box-{car_id}').style.display = 'block' if debug_panels_visible else 'none'
    document.getElementById('bottom-left-debug-panel').style.display = 'block' if debug_panels_visible else 'none'
    document.getElementById('bottom-right-debug-panel').style.display = 'block' if debug_panels_visible else 'none'

# --- WebSocket Channel Communication ---
async def on_message_callback(message):
    document.getElementById('connection-status').innerText = "Yes"
    try:
        payload_data = json.loads(message["payload"])
        topic = payload_data.get("topic")
        value = payload_data.get("value")

        for car_id, car in cars.items():
            if topic == f"/Car_Location_{car_id}/All":
                x = value.get('x')
                y = value.get('y')
                rotation = value.get('rotation')

                if x is not None and y is not None and rotation is not None:
                    car.move_to(float(x), float(y))
                    car.rotate_to(float(rotation))
                    car.x_coord_span.innerText = str(x)
                    car.y_coord_span.innerText = str(y)
                    car.bearing_span.innerText = str(rotation)

        selected_topic_filter = document.getElementById('topic-filter').value
        if selected_topic_filter == "All" or selected_topic_filter == topic:
            document.getElementById('latest-channel-message').innerText = f"Topic: {topic}, Value: {value}"

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Could not parse JSON message: {e}")
        selected_topic_filter = document.getElementById('topic-filter').value
        if selected_topic_filter == "All":
            document.getElementById('latest-channel-message').innerText = f"Raw: {message['payload']}"

myChannel.callback = on_message_callback

@when("click", "#connect-button")
async def connect_to_channel(event):
    try:
        await myChannel.connect_disconnect(event)
        if myChannel.is_connected:
            document.getElementById('connection-status').innerText = "Yes"
            asyncio.create_task(myChannel.post("/system/status", "ready"))
        else:
            document.getElementById('connection-status').innerText = "No"

    except Exception as e:
        print(f"Connection failed: {e}")
        document.getElementById('connection-status').innerText = "Error"

@when("change", "#topic-filter")
def on_filter_change(event):
    document.getElementById('latest-channel-message').innerText = ""

@when("change", "#car-select")
def on_car_select_change(event):
    global selected_car_id
    selected_car_id = int(event.target.value)

@when("input", ".orientation-slider")
def handle_orientation_change(event):
    car_id = int(event.target.id.split('-')[-1])
    cars[car_id].state['orientation'] = int(event.target.value)
    cars[car_id].rotate_to(cars[car_id].state['angle'])

@when("change", "#show-hitboxes-toggle")
def handle_show_hitboxes_toggle(event):
    global show_hitboxes
    show_hitboxes = event.target.checked
    for car in cars.values():
        update_car_hitbox(car)
    all_peels = document.querySelectorAll('.peel-image[id^="peel-"]')
    for peel in all_peels:
        hitbox_div = document.getElementById(f'peel-hitbox-{peel.id}')
        if hitbox_div:
            hitbox_div.style.opacity = '1' if show_hitboxes else '0'

@when("change", ".show-car-toggle")
def handle_show_car_toggle(event):
    car_id = int(event.target.id.split('-')[-1])
    car = cars[car_id]
    if event.target.checked:
        car.element.style.display = 'block'
    else:
        car.element.style.display = 'none'

@when("change", "#master-projector-toggle")
def handle_master_projector_toggle(event):
    global master_projector_on
    master_projector_on = event.target.checked

# --- Initial Setup ---
for car in cars.values():
    car.rotate_to(car.state['angle'])
    update_car_hitbox(car)
update_all_debug_elements_visibility()
game_loop(0)