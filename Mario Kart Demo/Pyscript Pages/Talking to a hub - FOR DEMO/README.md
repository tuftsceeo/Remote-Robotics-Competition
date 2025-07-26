## How to Use
1. Turn on your LEGO SPIKE
2. Press the bluetooth button so it is flashing blue
3. Press the 'Connect' button underneath 'Element Setup'
4. Select the hub in the popup
5. Press the 'connect' button underneath 'Channel Setup'
6. Scroll down and press the green play button in the 'Coding Environment' secion

---

## Testing

Can we plot a sensor in real-time?  Or many sensors?  Or can we control then the motors with sensor values in micropython?

## Javascript
1. ble.js has the bluetooth code
2. plotly.js has the calls to plotly (and I added this HTML <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>)

## Python
1. main.py is the main code that integrates everything with the DOM
2. plot.py will build your plot for you (using plotly.js)
3. wave.py will do all the wave protocol to talk with the wave devices (parsing replies and sending commands)

## Not Used
1. SPIKEbleCEEO.py is a modified library so that the SPIKE can talk BLE to this page
2. SPIKEPrimeCode.py is the code that should be running on the SPIKE to start the connection