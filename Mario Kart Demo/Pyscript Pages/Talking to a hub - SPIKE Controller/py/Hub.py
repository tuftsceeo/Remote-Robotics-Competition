from pyscript import document, window, when
import asyncio 
import struct
import json
from pyscript.js_modules import ble

HubHTML = '''   
<h3 id='title{num}'>Element Setup</h3>
<table>
  <tr>
    <td>w = </td>
    <td id = 'name{num}'>Sensor </td>
    <td><button id = "sync{num}">Connect</button></td>
    <td><select id="dropdown{num}"></select></td>
    <td style="width: 400px; text-align: center"><label id = "value{num}">0</label></td>
    <td> </td>
  </tr>
</table>
<div style = 'color:#0000FF; width: 800px; font-size: 9px' id = "activity{num}"></div>
'''

import SpikePrime as hub0
import TechElement as hub1
import TechElement_EP2 as hub1
import TechElement as hub2
hubs = [hub0, hub1, hub2]

import struct

class Hub_PS:
    def __init__(self,divName = 'all_things_hubs', suffix='_hub', hub = 1):
        self.hubInfo = hubs[hub]
        self.hubdiv = document.getElementById(divName)
        self.hubdiv.innerHTML = HubHTML.format(num = suffix)
        self.myble = ble.BLEDevice.new()
        
        self.info = None
        self.reply = None
        self.list_update = False
        self.final_callback = None
        
        self.name = document.getElementById('name'+suffix)
        self.sync = document.getElementById('sync'+suffix)
        self.sync.onclick = self.ask
        self.dropdown = document.getElementById('dropdown'+suffix)
        self.latest = document.getElementById('value'+suffix)
        self.activity = document.getElementById('activity'+suffix)

    async def ask(self, event): 
        if self.sync.innerHTML == 'Connect':
            await self.myble.scan()
            if not self.myble.device: 
                window.console.log(f'failed {self.myble.device}')
                return
            self.sync.innerHTML = 'Disconnect'
            try:
                await self.myble.connect(self.my_callback)
                # Send request for info and then feed rate (in msec)
                window.console.log('starting to test')
                fmt, ID, val = self.hubInfo.commands.get('info')
                window.console.log(fmt, ID)
                await self.send(fmt, ID)
                for i in range(30):
                    if self.info:  # waits for the info_response to arrive and get parsed
                        await self.feed_rate(1000)
                        return
                    print('waiting')
                    await asyncio.sleep(0.1)
                #maybe it is a SPIKE Prime bot
            except Exception as e:
                print(f"Interrupted {e}")
        else:
            self.myble.disconnect()
            self.dropdown.options.length = 0
            self.sync.innerHTML = 'Connect'
            self.info = None
            self.list_update = False

            
    def device_message(self, data, verbose = False):
        messages = {}
        while data:
            ID = data[0]
            if verbose: print([i for i in data])
            if ID in self.hubInfo.DEVICE_MESSAGE_MAP:
                name, fmt, keys = self.hubInfo.DEVICE_MESSAGE_MAP[ID]
                if verbose: print(name, fmt, keys)
                size = struct.calcsize(fmt)
                if size > len(data):
                    if verbose: print('Remaining characters ',data)
                    break
                content = struct.unpack(fmt, data[:size])[1:]  #get rid of id
                if keys:
                    if keys[0] == 'port':
                        name = name + '_' + self.hubInfo.port_lut[content[0]]
                    messages[name] = {k:v for k,v in zip(keys,content)}
                else:
                    messages[name] = content[0] if size == 2 else content
                data = data[size:]
            else:
                print(f"Unknown device ID: {ID}")
                break
        return messages
    
    def info_response(self, data):
        messages = {}
        for LINE in self.hubInfo.INFO_MESSAGE:
            name, fmt, keys = LINE
            size = struct.calcsize(fmt)
            content = struct.unpack(fmt, data[:size])
            if keys:
                messages[name] = {k:v for k,v in zip(keys,content)}
            else:
                messages[name] = content[0] if size == 2 else content
            data = data[size:]
        return messages
    
    def makeList(self, reply):
        self.myList = list(reply.keys())
        window.console.log('my list is ',self.myList)
        self.list_update = True

        options = []
        for f in self.myList:
            if f in self.hubInfo.TO_HIDE:
                continue
            try:
                new = list(reply[f].keys())
                for n in new:
                    if n in self.hubInfo.TO_HIDE:
                        continue
                    options.append(f+': '+n)
            except:
                pass

        for i,attribute in enumerate(options):
            option = document.createElement("option")
            option.value = attribute
            option.text = attribute
            self.dropdown.appendChild(option)
        return
    
    async def send(self, fmt, ID, val = None):
        window.console.log(fmt, ID)
        payload = [ID]
        if val:
            payload.extend(val['values'].values())
        message = self.hubInfo.pack(struct.pack(fmt, *payload))
        #packet_size = info['MaxSize']['packet'] if info else len(message) - issue here with TechElements
        packet_size = len(message)  # send the frame in packets of packet_size
        for i in range(0, len(message), packet_size):
            packet = message[i : i + packet_size]
            window.console.log(f"Sending: {packet}")
            await self.myble.send([p for p in packet])

    async def feed_rate(self, update = 1000):
        fmt, ID, val = self.hubInfo.commands.get('feed')
        val['values']['updateTime'] = update
        await self.send(fmt, ID, val)
    
    def my_callback(self, characteristic, data):
        if self.hubInfo.hubType == 'SPIKEPrime':
            if data[-1] != 0x02:  # for simplicity, this example does not implement buffering
                print(f"Received incomplete message:\n {un_xor}")
                return
        data = [d for d in data]
        reply = self.hubInfo.unpack(data)
        #print(f'Received: {[r for r in reply]}')
        ID = reply[0]
    
        if ID == 1:
            data = bytes(reply[1:])
            info = self.info_response(data)
            print(info)
            self.name.innerHTML = f'{self.hubInfo.hubType} ({info['Firmware']['major']}.{info['Firmware']['minor']}b{info['Firmware']['build']})'
            self.info = info
            self.activity.innerText = json.dumps(info)
            
        if ID == 60:
            if not self.info:
                return
            length = struct.unpack('<H',reply[1:3])[0]
            data = bytes(reply[3:])
            if length > len(data):
                print(f'error - {length} > {len(data)}')
                return
            self.reply = self.device_message(data, False)
            if not self.list_update:
                self.makeList(self.reply)
            if ':' in self.dropdown.value:
                a = self.dropdown.value.split(': ')
                self.value = self.reply[a[0]][a[1]]
            else:
                self.value = self.reply[self.dropdown.value]
            self.latest.innerHTML = json.dumps(self.value)
            self.activity.innerText = json.dumps(self.reply)
        if self.final_callback:
            await self.final_callback(self.reply)
            
