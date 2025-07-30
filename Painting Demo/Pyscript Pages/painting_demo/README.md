# Competitive Car Location Trail Painter - Grid Territory System

**Author:** William Goldman  
**Last Edited:** July 25, 2025

This project demonstrates a competitive territory control game where two teams use remote-controlled cars to paint trails and claim territory on a digital canvas. It demonstrates communication over WebSockets.

## Overview

- Channel Connection – Receives real-time car location data via WebSockets  
- Color Zones – Change paint color by driving into corner zones  
- Team Progress Visualization

## Technologies Used

- [`channels.py`](https://chrisrogers.pyscriptapps.com/talking-on-a-channel/latest/py/channel.py) module by Chris Rogers – Handles communication over WebSockets via the CEEO_Channel class  
- HTML5 Canvas
- Javascript as fstring

## How to Use

### 1. Connect to the Channel  
The system listens for:
- `/Car_Location_1/All` (Team 1)  
- `/Car_Location_2/All` (Team 2)

No manual connection is necessary.

### 2. Drive the Car and make sure data is being sent over channels

- Team 1 (Red & Blue): Starts with red, can also be blue
- Team 2 (Green & Orange): Starts with green, can also be orange 
