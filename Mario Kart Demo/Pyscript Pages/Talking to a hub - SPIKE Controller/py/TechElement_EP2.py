import struct
from pyConst import *
from TechElement import *

hubType = 'TechElement-old'


DEVICE_MESSAGE_MAP = {  # B = u8, b = i8, H = u16, h = i16, i = i32
    0x00: ("hub info",     "<BB",           ['Battery']),
    0x01: ("hub imu",      "<BBBhhhhhhhhh", ['face up', 'yaw face', 'yaw', 'pitch', 'roll', 'Ax', 'Ay', 'Az', 'gyro_x', 'gyro_y', 'gyro_z']),
    0x03: ("hub tags",     "<BBH",          ['color', 'tag']),
    0x04: ("btn state",    "<BB",           None),
    0x0A: ("Motor",        "<BBhhbi",       ['port', 'angle', 'power', 'speed', 'position']),
    0x0C: ("Color",        "<BBBHHHHHBBB",  ['color', 'reflection', 'red', 'green', 'blue', 'clear', 'infrared', 'hue', 'saturation', 'value']),
    0x0F: ("Joystick",     "<Bbbhh",        ['leftStep', 'rightStep','leftAngle','rightAngle']),
    0x10: ("imu gesture",  "<BB",           None),
    0x11: ("motor gesture","<BBB",          None),
}

# edited hub info, motor, and color