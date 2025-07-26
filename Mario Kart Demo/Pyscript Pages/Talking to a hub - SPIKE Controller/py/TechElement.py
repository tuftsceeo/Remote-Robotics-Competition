import struct
from pyConst import *

hubType = 'TechElement'

port_lut = { 0: '0',
             1: '1',  
             2: '2',}  

DEVICE_MESSAGE_MAP = {  # B = u8, b = i8, H = u16, h = i16, i = i32
    0x00: ("hub info",     "<BBB",          ['Battery','USB']),
    0x01: ("hub imu",      "<BBBhhhhhhhhh", ['face up', 'yaw face', 'yaw', 'pitch', 'roll', 'Ax', 'Ay', 'Az', 'gyro_x', 'gyro_y', 'gyro_z']),
    0x03: ("hub tags",     "<BBH",          ['color', 'tag']),
    0x04: ("btn state",    "<BB",           None),
    0x0A: ("Motor",        "<BBBhhbi",      ['port', 'type', 'angle', 'power', 'speed', 'position']),
    0x0C: ("Color",        "<BBBHHHHBB",    ['color', 'reflection', 'red', 'green', 'blue', 'hue', 'saturation', 'value']),
    0x0F: ("Joystick",     "<Bbbhh",        ['leftStep', 'rightStep','leftAngle','rightAngle']),
    0x10: ("imu gesture",  "<BB",           None),
    0x11: ("motor gesture","<BBB",          None),  #not sure why there is an extra B here...
}

INFO_MESSAGE = [
    ("RPC",      "<BBH", ['major','minor','build']),
    ("Firmware", "<BBH", ['major','minor','build']),
    ("MaxSize",  "<HHH", ['packet','message','chunk']),
    ("GroupID",  "<H",   None),
]

commands = {
    'info':         ('<B',     INFO_REQUEST, None),
    'feed':         ('<BH',    DEVICE_NOTIFICATION_REQUEST, {'values':{'updateTime':1000}}),
    'beep':         ('<BHI',   BEEP_COMMAND, {'values':{'frequency':1000, 'duration': 1000}}),
    'motor_speed':  ('<BBB',   MOTOR_SET_SPEED_COMMAND, {'values':{'port':1, 'speed':100}}),
    'motor_angle':  ('<BBIB',  MOTOR_RUN_FOR_DEGREES_COMMAND, {'values':{'port':1, 'angle':100, 'direction':1}}),
    'motor_abs_pos':('<BBHB',  MOTOR_RUN_TO_ABSOLUTE_POSITION_COMMAND, {'values':{'port':1, 'pos':100, 'direction':1}}),
    'motor_stop':   ('<BBB',   MOTOR_STOP_COMMAND, {'values':{'port':1, 'end state':0}}),
    'motor_run':    ('<BBB',   MOTOR_RUN_COMMAND, {'values':{'port':1, 'direction':2}}),  #dir - 0=CW, 1=CCW, 2=shortest, 3=longest
}

TO_HIDE = []

##### no need for packing and unpacking with tech elements
def pack(message):
    return message

def unpack(message):
    return bytes(message)

