# Remote FLL - Scoring Demo

**Author:** William Goldman  
**Last Edited:** July 25, 2025

This project demonstrates how a robot can be used as a controller to interact with a digital scoring system. It showcases real-time communication over WebSockets, scoring visualization using a canvas, and the potential for displaying the score directly on the playing field.

## Overview
- Channel connection (sending and receiving data over websockets)  
- Playing field with score zones and alliance scores
- Reset button, car position, score display, color key

## Technologies Used

- [`channels.py`](https://chrisrogers.pyscriptapps.com/talking-on-a-channel/latest/py/channel.py) module by Chris Rogers – Handles communication over WebSockets via the CEEO_Channel class  
- HTML5 Canvas
- Javascript as fstring

## How to Use

1. Click the 'connect' button in the channel UI. Leave the channel name blank to listen to all data or use `/Car_Location_2/All` to listen specifically to the car location updates used in this demo.

2. Drive the Robot:
    - Move your robot to control the position marker on the canvas.  
    - When the marker touches a target, points are scored for the corresponding alliance.

3. Reset the Game
   - Press the 'Reset' button to clear scores and regenerate targets.

## Game Rules

- Drive your car around the virtual field to hit targets. It is currently setup so that only one player/position is recorded so the controller can score for both alliances.
