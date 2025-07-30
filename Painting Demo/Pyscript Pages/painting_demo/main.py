from pyscript import document, window
import json

print("=== Competitive Car Location Trail Painter - Grid Territory System ===")

import channel
signaling_channel = channel.CEEO_Channel(
    "hackathon", 
    "@chrisrogers", 
    "talking-on-a-channel",
    divName='all_things_channels',
    suffix='_competitive_trail_painter'
)

signaling_channel.topic.value = '/Car_Location_1/All,/Car_Location_2/All'

# Global variables
canvas = None
ctx = None
canvas_width = 0
canvas_height = 0
corner_size = 120
brush_size = 60

# Grid-based territory system
grid_cols = 25  # Number of columns in territory grid
grid_rows = 15  # Number of rows in territory grid
territory_grid = []  # 2D array: 0 = neutral, 1 = team1, 2 = team2
grid_cell_width = 0
grid_cell_height = 0

# Track both cars separately
cars = {
    1: {"previous_x": None, "previous_y": None, "current_color": "#CC0000"},
    2: {"previous_x": None, "previous_y": None, "current_color": "#00AA00"}
}

# Corner colors and positions
corners = {
    "top_left": {"color": "#CC0000", "x": 0, "y": 0},
    "top_right": {"color": "#00AA00", "x": "right", "y": 0},
    "bottom_left": {"color": "#0000CC", "x": 0, "y": "bottom"},
    "bottom_right": {"color": "#CC8800", "x": "right", "y": "bottom"}
}

# Paint boosters
paint_boosters = []
booster_radius = 30
splatter_radius = 120
game_over = False

def setup_canvas():
    """Initialize canvas and drawing context"""
    global canvas, ctx, canvas_width, canvas_height, paint_boosters
    global territory_grid, grid_cell_width, grid_cell_height, grid_cols, grid_rows
    
    canvas = document.getElementById("trailCanvas")
    ctx = canvas.getContext("2d")
    
    # Set canvas size
    canvas_width = window.innerWidth - 20
    canvas_height = min(window.innerHeight - 300, 700)
    
    canvas.width = canvas_width
    canvas.height = canvas_height
    
    # Set drawing properties
    ctx.lineWidth = brush_size
    ctx.lineCap = "round"
    ctx.lineJoin = "round"
    
    # Initialize territory grid system
    grid_cell_width = canvas_width / grid_cols
    grid_cell_height = canvas_height / grid_rows
    
    # Create 2D territory grid (0 = neutral, 1 = team1, 2 = team2)
    territory_grid = []
    for row in range(grid_rows):
        territory_grid.append([0] * grid_cols)
    
    # Create paint boosters
    center_x = canvas_width // 2
    center_y = canvas_height // 2
    offset = 120
    
    paint_boosters = [
        {"x": center_x - offset, "y": center_y - offset},
        {"x": center_x + offset, "y": center_y - offset},
        {"x": center_x - offset, "y": center_y + offset},
        {"x": center_x + offset, "y": center_y + offset}
    ]
    
    # Clear canvas with white background
    ctx.fillStyle = "#FFFFFF"
    ctx.fillRect(0, 0, canvas_width, canvas_height)
    
    # Draw corner indicators
    draw_corner_indicators()
    
    # Draw paint boosters
    draw_paint_boosters()
    
    # Optionally draw grid lines (subtle)
    draw_grid_lines()
    
    print(f"Canvas initialized: {canvas_width}x{canvas_height}")
    print(f"Territory grid: {grid_cols}x{grid_rows} = {grid_cols * grid_rows} squares")
    print("Car coordinates: (0,0) = top-left, (1200,1200) = bottom-right")

def draw_corner_indicators():
    """Draw colored squares in each corner"""
    global ctx, canvas_width, canvas_height, corner_size
    
    # Top-left corner (Red)
    ctx.fillStyle = corners["top_left"]["color"]
    ctx.fillRect(0, 0, corner_size, corner_size)
    
    # Top-right corner (Green)
    ctx.fillStyle = corners["top_right"]["color"]
    ctx.fillRect(canvas_width - corner_size, 0, corner_size, corner_size)
    
    # Bottom-left corner (Blue)
    ctx.fillStyle = corners["bottom_left"]["color"]
    ctx.fillRect(0, canvas_height - corner_size, corner_size, corner_size)
    
    # Bottom-right corner (Orange)
    ctx.fillStyle = corners["bottom_right"]["color"]
    ctx.fillRect(canvas_width - corner_size, canvas_height - corner_size, corner_size, corner_size)

def draw_paint_boosters():
    """Draw paint booster dots"""
    global ctx, paint_boosters, booster_radius
    
    for booster in paint_boosters:
        # Black border
        ctx.strokeStyle = "#000000"
        ctx.lineWidth = 3
        ctx.beginPath()
        ctx.arc(booster["x"], booster["y"], booster_radius, 0, 2 * 3.14159)
        ctx.stroke()
        
        # Gray fill
        ctx.fillStyle = "#808080"
        ctx.beginPath()
        ctx.arc(booster["x"], booster["y"], booster_radius - 2, 0, 2 * 3.14159)
        ctx.fill()
    
    # Reset line width
    ctx.lineWidth = brush_size

def draw_grid_lines():
    """Draw subtle grid lines to show territory boundaries"""
    global ctx, canvas_width, canvas_height, grid_cols, grid_rows, grid_cell_width, grid_cell_height
    
    ctx.strokeStyle = "#E0E0E0"  # Light gray
    ctx.lineWidth = 1
    
    # Draw vertical lines
    for col in range(1, grid_cols):
        x = col * grid_cell_width
        ctx.beginPath()
        ctx.moveTo(x, 0)
        ctx.lineTo(x, canvas_height)
        ctx.stroke()
    
    # Draw horizontal lines
    for row in range(1, grid_rows):
        y = row * grid_cell_height
        ctx.beginPath()
        ctx.moveTo(0, y)
        ctx.lineTo(canvas_width, y)
        ctx.stroke()
    
    # Reset line width
    ctx.lineWidth = brush_size

def map_coordinates(car_x, car_y):
    """Map car coordinates to canvas coordinates"""
    # Car coordinates range from 0 to 1200, with (0,0) at top left
    max_coord = 1200
    
    canvas_x = (car_x / max_coord) * canvas_width
    canvas_y = (car_y / max_coord) * canvas_height
    
    canvas_x = max(0, min(canvas_width, canvas_x))
    canvas_y = max(0, min(canvas_height, canvas_y))
    
    return canvas_x, canvas_y

def canvas_to_grid(canvas_x, canvas_y):
    """Convert canvas coordinates to grid coordinates"""
    global grid_cell_width, grid_cell_height, grid_cols, grid_rows
    
    grid_col = int(canvas_x / grid_cell_width)
    grid_row = int(canvas_y / grid_cell_height)
    
    # Clamp to grid bounds
    grid_col = max(0, min(grid_cols - 1, grid_col))
    grid_row = max(0, min(grid_rows - 1, grid_row))
    
    return grid_col, grid_row

def claim_territory(canvas_x, canvas_y, team):
    """Claim territory around the given position for the team"""
    global territory_grid, brush_size, grid_cell_width, grid_cell_height
    
    # Calculate how many grid cells the brush covers
    brush_radius_cols = max(1, int((brush_size / 2) / grid_cell_width))
    brush_radius_rows = max(1, int((brush_size / 2) / grid_cell_height))
    
    center_col, center_row = canvas_to_grid(canvas_x, canvas_y)
    
    # Claim territory in a square around the brush position
    for row in range(center_row - brush_radius_rows, center_row + brush_radius_rows + 1):
        for col in range(center_col - brush_radius_cols, center_col + brush_radius_cols + 1):
            if 0 <= row < grid_rows and 0 <= col < grid_cols:
                territory_grid[row][col] = team

def calculate_territory_percentages():
    """Fast percentage calculation using grid squares"""
    global territory_grid, grid_rows, grid_cols
    
    team1_squares = 0
    team2_squares = 0
    total_squares = grid_rows * grid_cols
    
    for row in range(grid_rows):
        for col in range(grid_cols):
            if territory_grid[row][col] == 1:
                team1_squares += 1
            elif territory_grid[row][col] == 2:
                team2_squares += 1
    
    team1_percent = (team1_squares / total_squares) * 100
    team2_percent = (team2_squares / total_squares) * 100
    
    return team1_percent, team2_percent

def update_percentages():
    """Update percentage display - now blazingly fast!"""
    try:
        team1_percent, team2_percent = calculate_territory_percentages()
        
        # Update UI
        document.getElementById("team1Percentage").innerHTML = f"{team1_percent:.1f}%"
        document.getElementById("team2Percentage").innerHTML = f"{team2_percent:.1f}%"
        document.getElementById("team1Progress").style.width = f"{team1_percent}%"
        document.getElementById("team2Progress").style.width = f"{team2_percent}%"
        
        return team1_percent, team2_percent
    except:
        pass
    
    return 0, 0

def detect_corner_color(x, y, team):
    """Detect if position is in a corner and return the corner color"""
    global canvas_width, canvas_height, corner_size
    
    # Check top-left corner (Team 1)
    if x <= corner_size and y <= corner_size:
        return "#CC0000" if team == 1 else cars[team]["current_color"]
    
    # Check top-right corner (Team 2)
    if x >= canvas_width - corner_size and y <= corner_size:
        return "#00AA00" if team == 2 else cars[team]["current_color"]
    
    # Check bottom-left corner (Team 1)
    if x <= corner_size and y >= canvas_height - corner_size:
        return "#0000CC" if team == 1 else cars[team]["current_color"]
    
    # Check bottom-right corner (Team 2)
    if x >= canvas_width - corner_size and y >= canvas_height - corner_size:
        return "#CC8800" if team == 2 else cars[team]["current_color"]
    
    return cars[team]["current_color"]

def check_paint_booster_collision(x, y):
    """Check if position collides with any paint booster"""
    global paint_boosters, booster_radius
    
    for booster in paint_boosters:
        dx = x - booster["x"]
        dy = y - booster["y"]
        distance = (dx * dx + dy * dy) ** 0.5
        if distance <= booster_radius:
            print(f"Booster hit at ({booster['x']}, {booster['y']})!")
            return booster
    return None

def create_paint_splatter(center_x, center_y, color):
    """Create a paint splatter at the given position"""
    global ctx, splatter_radius
    
    ctx.fillStyle = color
    ctx.beginPath()
    ctx.arc(center_x, center_y, splatter_radius, 0, 2 * 3.14159)
    ctx.fill()
    
    print(f"Paint splatter created at ({center_x}, {center_y}) with color {color}")

def draw_trail(x, y, team):
    """Draw trail from previous position to current position"""
    global ctx, cars
    
    car_data = cars[team]
    color = car_data["current_color"]
    
    # Check for paint booster collision
    booster = check_paint_booster_collision(x, y)
    if booster:
        create_paint_splatter(booster["x"], booster["y"], color)
        # Claim large territory around splatter
        splatter_grid_radius = max(3, int(splatter_radius / max(grid_cell_width, grid_cell_height)))
        center_col, center_row = canvas_to_grid(booster["x"], booster["y"])
        for row in range(center_row - splatter_grid_radius, center_row + splatter_grid_radius + 1):
            for col in range(center_col - splatter_grid_radius, center_col + splatter_grid_radius + 1):
                if 0 <= row < grid_rows and 0 <= col < grid_cols:
                    territory_grid[row][col] = team
    
    # Draw regular trail
    if car_data["previous_x"] is not None and car_data["previous_y"] is not None:
        # Draw line from previous to current position
        ctx.strokeStyle = color
        ctx.beginPath()
        ctx.moveTo(car_data["previous_x"], car_data["previous_y"])
        ctx.lineTo(x, y)
        ctx.stroke()
        
        # Claim territory along the trail
        claim_territory(x, y, team)
    else:
        # First point, draw a dot
        ctx.fillStyle = color
        ctx.beginPath()
        ctx.arc(x, y, brush_size // 2, 0, 2 * 3.14159)
        ctx.fill()
        
        # Claim territory around the dot
        claim_territory(x, y, team)
    
    # Update previous position
    car_data["previous_x"] = x
    car_data["previous_y"] = y

def check_win_condition():
    """Check if any team has won (50% territory control)"""
    global game_over
    
    if game_over:
        return False
    
    team1_percent, team2_percent = calculate_territory_percentages()
    
    if team1_percent >= 50.0:
        print(f"Team 1 wins with {team1_percent:.1f}% territory!")
        game_over = True
        try:
            window.eval('''
            const banner = document.getElementById("winBanner");
            const msgElem = document.getElementById("winMessage");
            msgElem.innerHTML = "<div style='color: black;'>Team 1 Wins!</div><div style='font-size: 0.7em; margin-top: 10px; color: #666;'>Red and Blue team conquered the territory!</div>";
            banner.style.display = "block";
            ''')
        except:
            pass
        return True
    elif team2_percent >= 50.0:
        print(f"Team 2 wins with {team2_percent:.1f}% territory!")
        game_over = True
        try:
            window.eval('''
            const banner = document.getElementById("winBanner");
            const msgElem = document.getElementById("winMessage");
            msgElem.innerHTML = "<div style='color: black;'>Team 2 Wins!</div><div style='font-size: 0.7em; margin-top: 10px; color: #666;'>Green and Orange team conquered the territory!</div>";
            banner.style.display = "block";
            ''')
        except:
            pass
        return True
    
    return False

def update_status(team, x, y, car_x, car_y, rotation):
    """Update status display"""
    try:
        # Update percentages every time (now it's fast!)
        team1_percent, team2_percent = update_percentages()
        
        status_elem = document.getElementById("statusDisplay")
        status_elem.innerHTML = f"""
        <strong>Team {team} Car:</strong> X: {car_x:.1f}, Y: {car_y:.1f}<br>
        <strong>Canvas Position:</strong> X: {int(x)}, Y: {int(y)}<br>
        <strong>Rotation:</strong> {rotation:.1f}°<br>
        <strong>Current Color:</strong> <span style="color: {cars[team]['current_color']};">●</span> {cars[team]['current_color']}<br>
        <strong>Territory:</strong> Team 1: {team1_percent:.1f}% | Team 2: {team2_percent:.1f}%
        """
    except:
        pass

def car_location_callback(message):
    """Handle incoming car location data"""
    try:
        if message['type'] == 'data' and 'payload' in message:
            payload_data = json.loads(message['payload'])
            topic = payload_data.get('topic', '')
            value = payload_data.get('value', {})
            
            # Determine which team based on topic
            team = None
            if topic == '/Car_Location_1/All':
                team = 1
            elif topic == '/Car_Location_2/All':
                team = 2
            
            if team and isinstance(value, dict):
                car_x = value.get('x', 0)
                car_y = value.get('y', 0)
                rotation = value.get('rotation', 0)
                
                # Map to canvas coordinates
                canvas_x, canvas_y = map_coordinates(car_x, car_y)
                
                # Check if we're in a corner and update color
                new_color = detect_corner_color(canvas_x, canvas_y, team)
                if new_color != cars[team]["current_color"]:
                    cars[team]["current_color"] = new_color
                    print(f"Team {team} color changed to: {new_color}")
                
                # Draw the trail and claim territory
                draw_trail(canvas_x, canvas_y, team)
                
                # Update status display (includes fast percentage update)
                update_status(team, canvas_x, canvas_y, car_x, car_y, rotation)
                
                # Check win condition occasionally
                if int(car_x) % 50 == 0:  # Check every 50 position updates
                    check_win_condition()
                
    except Exception as e:
        print(f"Car location callback error: {e}")

def clear_canvas():
    """Clear the canvas and reset game"""
    global cars, territory_grid, grid_rows, grid_cols, game_over
    
    game_over = False
    
    # Reset car tracking
    for team in cars:
        cars[team]["previous_x"] = None
        cars[team]["previous_y"] = None
        cars[team]["current_color"] = "#CC0000" if team == 1 else "#00AA00"
    
    # Reset territory grid
    for row in range(grid_rows):
        for col in range(grid_cols):
            territory_grid[row][col] = 0
    
    # Clear canvas
    ctx.fillStyle = "#FFFFFF"
    ctx.fillRect(0, 0, canvas_width, canvas_height)
    
    # Redraw corner indicators and boosters
    draw_corner_indicators()
    draw_paint_boosters()
    draw_grid_lines()
    
    # Hide win banner
    try:
        window.eval('''
        const banner = document.getElementById("winBanner");
        banner.style.display = "none";
        ''')
    except:
        pass
    
    # Reset percentages
    document.getElementById("team1Percentage").innerHTML = "0.0%"
    document.getElementById("team2Percentage").innerHTML = "0.0%"
    document.getElementById("team1Progress").style.width = "0%"
    document.getElementById("team2Progress").style.width = "0%"
    
    print("Game reset!")

def setup_events():
    """Setup event handlers"""
    # Clear button
    clear_btn = document.getElementById("clearButton")
    if clear_btn:
        clear_btn.onclick = lambda e: clear_canvas()
    
    # Make reset available globally
    window.resetGame = clear_canvas
    
    # Window resize handler
    def handle_resize():
        setup_canvas()
        clear_canvas()
    
    window.addEventListener('resize', handle_resize)

def initialize():
    """Initialize the application"""
    # Set up canvas
    setup_canvas()
    
    # Initialize percentages
    update_percentages()
    
    # Set up the car location callback
    signaling_channel.callback = car_location_callback
    
    def delayed_setup():
        setup_events()
        print("Ready! Listening for Car_Location_1/All and Car_Location_2/All data...")
        print("Drive to corners to change colors!")
        print("Hit gray boosters for massive territory splatter!")
        print("First team to control 50% territory wins!")
    
    window.setTimeout(delayed_setup, 500)

# Initialize when page loads
initialize()
print("=== Grid Territory Trail Painter Ready ===")