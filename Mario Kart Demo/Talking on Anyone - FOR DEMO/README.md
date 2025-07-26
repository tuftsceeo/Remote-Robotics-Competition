## How to Use
1. Turn on your LEGO SPIKE and connect it to your computer with a cable
3. Press the 'connect up' button underneath 'Serial Terminal Setup'
4. Press the 'LOAD CODE' button at the top of the page and press the 'run' button underneath 'Serial Terminal Setup' 
5. Press the 'connect' button underneath 'BLE Setup'
6. Select the hub in the popup
7. Press the 'connect' button underneath 'Channel Setup'
8. Scroll down and press the green play button under the last 'LOAD CODE' button

---

## Talking to the Microprocessor

This will connect up to your camera, SPIKE Prime, RP2040, ESP32, or LEGO Tech Element

## Python
1. main.py is the main code
2. myCode.py is a library of example code to use for all the different processors (note all send out a json package with
one of the keys being 'x')
3. in the case of the tech elements, you do not use the serial connection part - but instead copy that code down into the
main python area below

## Known bugs
- Coro error?


