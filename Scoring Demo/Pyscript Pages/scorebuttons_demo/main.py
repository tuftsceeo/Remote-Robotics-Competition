from pyscript import document, window
import json
import random
import channel

signaling_channel = channel.CEEO_Channel(
    "hackathon", 
    "@chrisrogers", 
    "talking-on-a-channel",
    divName='all_things_channels',
    suffix='_dual_game'
)

signaling_channel.topic.value = '/Car_Location_1/All'

canvas = None
ctx = None
canvas_width = 0
canvas_height = 0
alliance1_score = 0
alliance2_score = 0
targets = []
last_hit_time = 0
hit_cooldown = 500  # ms
animation_timer = None

controllers = {
    1: {"pointer_x": 200, "pointer_y": 300, "car_x": 0, "car_y": 0},
    2: {"pointer_x": 600, "pointer_y": 300, "car_x": 0, "car_y": 0}
}

class Target:
    def __init__(self, x, y, radius, color, alliance, points):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.alliance = alliance
        self.points = points
        self.is_active = True
        self.hit_animation = 0
        self.base_color = color

    def draw_js(self):
        return f"drawTarget({self.x}, {self.y}, {self.radius}, '{self.color}', {self.points}, {self.hit_animation})"

    def check_hit(self, px, py):
        distance = ((px - self.x) ** 2 + (py - self.y) ** 2) ** 0.5
        return distance <= self.radius

    def hit(self):
        self.hit_animation = 15
        return self.points

    def update_animation(self):
        """Update animation state"""
        if self.hit_animation > 0:
            self.hit_animation -= 1
            return True  # Still animating
        return False  # Animation finished

def setup_canvas():
    """Initialize canvas for full-screen display"""
    global canvas, ctx, canvas_width, canvas_height
    canvas = document.getElementById("gameCanvas")
    ctx = canvas.getContext("2d")
    
    # Set canvas to full viewport for projection
    canvas_width = window.innerWidth
    canvas_height = window.innerHeight
    
    canvas.width = canvas_width
    canvas.height = canvas_height
    
    print(f"Full-screen game canvas initialized: {canvas_width}x{canvas_height}")

def create_targets():
    """Create targets positioned for full-screen canvas"""
    global targets
    targets = []
    configs = [
        # Alliance 1 targets (red) - left side
        {"x": 0.2, "y": 0.3, "r": 50, "c": "#E53935", "a": 1, "p": 10},
        {"x": 0.25, "y": 0.6, "r": 45, "c": "#E53935", "a": 1, "p": 15},
        {"x": 0.1, "y": 0.8, "r": 40, "c": "#E53935", "a": 1, "p": 20},
        {"x": 0.35, "y": 0.45, "r": 55, "c": "#E53935", "a": 1, "p": 25},
        # Alliance 2 targets (blue) - right side
        {"x": 0.8, "y": 0.3, "r": 50, "c": "#1E88E5", "a": 2, "p": 10},
        {"x": 0.75, "y": 0.6, "r": 45, "c": "#1E88E5", "a": 2, "p": 15},
        {"x": 0.9, "y": 0.8, "r": 40, "c": "#1E88E5", "a": 2, "p": 20},
        {"x": 0.65, "y": 0.45, "r": 55, "c": "#1E88E5", "a": 2, "p": 25},
    ]
    for cfg in configs:
        x = cfg["x"] * canvas_width
        y = cfg["y"] * canvas_height
        targets.append(Target(x, y, cfg["r"], cfg["c"], cfg["a"], cfg["p"]))

def update_scene_js():
    """Update the entire scene using JavaScript functions"""
    js_commands = ["clearCanvas()"]
    js_commands.append(f"drawScoreBar({alliance1_score}, {alliance2_score})")
    
    # Draw all targets with their current animation states
    for target in targets:
        if target.is_active:
            js_commands.append(target.draw_js())
    
    # Draw both pointers
    controller1 = controllers[1]
    controller2 = controllers[2]
    js_commands.append(f"drawPointer({controller1['pointer_x']}, {controller1['pointer_y']}, 1)")
    js_commands.append(f"drawPointer({controller2['pointer_x']}, {controller2['pointer_y']}, 2)")
    
    # Execute all drawing commands at once
    window.eval("; ".join(js_commands))

def start_animation_timer():
    """Start animation timer for hit effects"""
    global animation_timer
    if animation_timer is None:
        window.eval(f'''
        window.animationTimer = setInterval(function() {{
            if (window.pythonUpdateAnimations) {{
                window.pythonUpdateAnimations();
            }}
        }}, 33);  // ~30 FPS for smooth animations
        ''')
        animation_timer = True
        window.pythonUpdateAnimations = update_animations

def stop_animation_timer():
    """Stop animation timer when no animations are running"""
    global animation_timer
    if animation_timer is not None:
        window.eval('''
        if (window.animationTimer) {
            clearInterval(window.animationTimer);
            window.animationTimer = null;
        }
        ''')
        animation_timer = None

def update_animations():
    """Update all target animations"""
    any_animating = False
    
    for target in targets:
        if target.update_animation():
            any_animating = True
    
    if any_animating:
        # Redraw scene with updated animations
        update_scene_js()
    else:
        # No more animations, stop the timer
        stop_animation_timer()

def map_coordinates(car_x, car_y):
    """Map car coordinates to canvas coordinates"""
    if car_x >= 0 and car_y >= 0:
        max_coord = 1200
        cx = (car_x / max_coord) * canvas_width
        cy = (car_y / max_coord) * (canvas_height - 100) + 100  # Leave space for score bar
    else:
        cx = ((car_x + 1000) / 2000) * canvas_width
        cy = ((car_y + 1000) / 2000) * (canvas_height - 100) + 100
    return max(0, min(canvas_width, cx)), max(100, min(canvas_height, cy))

def check_target_hits(controller_id):
    """Check if pointer is hitting any targets for specific controller"""
    global alliance1_score, alliance2_score, last_hit_time
    import time
    now = time.time() * 1000
    if now - last_hit_time < hit_cooldown:
        return
    
    controller = controllers[controller_id]
    pointer_x = controller["pointer_x"]
    pointer_y = controller["pointer_y"]
    
    for target in targets:
        if target.is_active and target.check_hit(pointer_x, pointer_y):
            # Only allow scoring for matching alliance
            if target.alliance == controller_id:
                points = target.hit()
                
                if target.alliance == 1:
                    alliance1_score += points
                else:
                    alliance2_score += points
                
                last_hit_time = now
                update_status()
                
                # Start animation timer for hit effect
                start_animation_timer()
                print(f"Controller {controller_id} scored {points} points for Alliance {target.alliance}!")
                break

def car_location_callback(msg):
    """Handle incoming car location data from both controllers"""
    try:
        if msg['type'] == 'data' and 'payload' in msg:
            data = json.loads(msg['payload'])
            topic = data.get('topic', '')
            value = data.get('value', {})
            
            # Determine which controller based on topic
            controller_id = None
            if topic == '/Car_Location_1/All':
                controller_id = 1
            elif topic == '/Car_Location_2/All':
                controller_id = 2
            
            if controller_id and isinstance(value, dict):
                car_x = value.get('x', 0)
                car_y = value.get('y', 0)
                rotation = value.get('rotation', 0)
                
                # Update controller data
                controllers[controller_id]["car_x"] = car_x
                controllers[controller_id]["car_y"] = car_y
                controllers[controller_id]["pointer_x"], controllers[controller_id]["pointer_y"] = map_coordinates(car_x, car_y)
                
                # Check for hits (only for matching alliance)
                check_target_hits(controller_id)
                
                # Redraw scene and update status
                update_scene_js()
                update_status()
                
    except Exception as e:
        print(f"Callback error: {e}")

def update_status():
    """Update status display for both controllers"""
    try:
        controller1 = controllers[1]
        controller2 = controllers[2]
        
        status_elem = document.getElementById("statusDisplay")
        status_elem.innerHTML = f"""
        <strong>Controller 1:</strong> X: {controller1['car_x']:.1f}, Y: {controller1['car_y']:.1f}<br>
        <strong>Pointer 1:</strong> X: {int(controller1['pointer_x'])}, Y: {int(controller1['pointer_y'])}<br>
        <strong>Controller 2:</strong> X: {controller2['car_x']:.1f}, Y: {controller2['car_y']:.1f}<br>
        <strong>Pointer 2:</strong> X: {int(controller2['pointer_x'])}, Y: {int(controller2['pointer_y'])}<br>
        <strong>Alliance 1:</strong> {alliance1_score} points<br>
        <strong>Alliance 2:</strong> {alliance2_score} points
        """
    except:
        pass

def reset_game():
    """Reset the game scores and targets"""
    global alliance1_score, alliance2_score
    
    alliance1_score = 0
    alliance2_score = 0
    
    # Reset both controllers
    controllers[1]["car_x"] = 0
    controllers[1]["car_y"] = 0
    controllers[1]["pointer_x"] = 200
    controllers[1]["pointer_y"] = 300
    
    controllers[2]["car_x"] = 0
    controllers[2]["car_y"] = 0
    controllers[2]["pointer_x"] = 600
    controllers[2]["pointer_y"] = 300
    
    # Stop any running animations
    stop_animation_timer()
    
    # Recreate targets
    create_targets()
    
    # Redraw scene and update status
    update_scene_js()
    update_status()
    
    print("Game reset!")

def toggle_controls_panel():
    """Toggle visibility of controls panel and header"""
    try:
        controls_panel = document.getElementById("overlay-controls")
        header_panel = document.getElementById("overlay-header")
        toggle_btn = document.getElementById("toggleControls")
        
        if controls_panel.classList.contains("hidden"):
            controls_panel.classList.remove("hidden")
            header_panel.classList.remove("hidden")
            toggle_btn.innerHTML = "Hide Controls"
            print("Controls panel and header shown")
        else:
            controls_panel.classList.add("hidden")
            header_panel.classList.add("hidden")
            toggle_btn.innerHTML = "Show Controls"
            print("Controls panel and header hidden")
    except Exception as e:
        print(f"Toggle error: {e}")

def setup_events():
    """Setup event handlers"""
    # Store Python functions in window for JavaScript access
    window.pythonResetGame = reset_game
    window.pythonToggleControls = toggle_controls_panel
    
    # Setup event handlers using JavaScript
    window.eval('''
        // Reset button
        const resetBtn = document.getElementById("resetButton");
        if (resetBtn) {
            resetBtn.addEventListener('click', function() {
                if (window.pythonResetGame) {
                    window.pythonResetGame();
                }
            });
        }
        
        // Toggle controls button
        const toggleBtn = document.getElementById("toggleControls");
        if (toggleBtn) {
            toggleBtn.addEventListener('click', function() {
                if (window.pythonToggleControls) {
                    window.pythonToggleControls();
                }
            });
        }
        
        // Keyboard event handler for 't' key
        document.addEventListener('keydown', function(event) {
            const key = event.key.toLowerCase();
            if (key === 't' && !event.repeat) {
                if (window.pythonToggleControls) {
                    window.pythonToggleControls();
                }
            }
        });
        
        // Window resize handler
        window.addEventListener('resize', function() {
            if (window.pythonResizeCanvas) {
                window.pythonResizeCanvas();
            }
        });
    ''')

def handle_resize():
    """Handle window resize"""
    setup_canvas()
    setup_js_canvas()
    create_targets()
    update_scene_js()
    update_status()

def setup_js_canvas():
    """Setup JavaScript canvas drawing functions for full-screen"""
    window.eval(f'''
    const canvas = document.getElementById("gameCanvas");
    const ctx = canvas.getContext("2d");

    window.clearCanvas = function() {{
        ctx.fillStyle = "#F0F0F0";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }}

    window.drawPointer = function(x, y, controllerId) {{
        // Different colors for each controller
        const colors = {{
            1: "#FF6B6B",  // Red for Controller 1 (Alliance 1)
            2: "#4ECDC4"   // Teal for Controller 2 (Alliance 2)
        }};
        
        const color = colors[controllerId] || "#00FF00";
        
        // Semi-transparent colored circle - larger for full screen
        ctx.save();
        ctx.globalAlpha = 0.8;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, 10, 0, Math.PI * 2);
        ctx.fill();
        
        // Crosshair lines - larger for visibility
        ctx.globalAlpha = 1.0;
        ctx.strokeStyle = "#000000";
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(x-18, y);
        ctx.lineTo(x+18, y);
        ctx.moveTo(x, y-18);
        ctx.lineTo(x, y+18);
        ctx.stroke();
        
        // Controller number in center
        ctx.fillStyle = "#000000";
        ctx.font = "bold 14px Arial";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(controllerId.toString(), x, y);
        
        ctx.restore();
    }}

    window.drawTarget = function(x, y, radius, color, points, animation) {{
        // Draw target with animation scaling
        let scale = 1;
        if (animation > 0) {{
            scale = 1 + (animation / 40);  // Smooth scaling animation
            ctx.save();
            ctx.globalAlpha = 0.9;
        }}
        
        // Draw target circle
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, radius * scale, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw border - thicker for full screen
        ctx.strokeStyle = "#000000";
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.arc(x, y, radius * scale, 0, Math.PI * 2);
        ctx.stroke();
        
        // Draw points text - larger for full screen
        ctx.fillStyle = "#FFFFFF";
        ctx.font = "bold 28px Arial";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(points.toString(), x, y);
        
        if (animation > 0) {{
            ctx.restore();
        }}
    }}

    window.drawScoreBar = function(score1, score2) {{
        const barHeight = 100;  // Larger score bar for full screen
        const midPoint = canvas.width / 2;
        
        // Alliance 1 side (red)
        ctx.fillStyle = "#E53935";
        ctx.fillRect(0, 0, midPoint, barHeight);
        
        // Alliance 2 side (blue)
        ctx.fillStyle = "#1E88E5";
        ctx.fillRect(midPoint, 0, midPoint, barHeight);
        
        // Alliance labels - larger text for full screen
        ctx.fillStyle = "#FFFFFF";
        ctx.font = "bold 32px Arial";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("Alliance 1", canvas.width * 0.25, 30);
        ctx.fillText("Alliance 2", canvas.width * 0.75, 30);
        
        // Scores - larger text for full screen
        ctx.font = "bold 48px Arial";
        ctx.fillText(score1.toString(), canvas.width * 0.25, 70);
        ctx.fillText(score2.toString(), canvas.width * 0.75, 70);
        
        // Center divider
        ctx.fillStyle = "#000000";
        ctx.fillRect(midPoint - 3, 0, 6, barHeight);
    }}
    ''')

def initialize():
    """Initialize the full-screen game"""
    setup_canvas()
    setup_js_canvas()
    create_targets()
    
    # Store resize function for JavaScript access
    window.pythonResizeCanvas = handle_resize
    
    # Initial scene draw
    update_scene_js()
    update_status()
    
    # Setup car location callback
    signaling_channel.callback = car_location_callback
    
    def delayed_setup():
        setup_events()
    
    window.setTimeout(delayed_setup, 500)

window.setTimeout(initialize, 300)
