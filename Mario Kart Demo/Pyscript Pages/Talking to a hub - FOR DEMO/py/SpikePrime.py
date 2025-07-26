#https://lego.github.io/spike-prime-docs/messages.html#x28-devicenotificationrequest
import struct
from pyConst import *

hubType = 'SPIKEPrime'

port_lut = { 0: 'A',
             1: 'B',
             2: 'C',
             3: 'D',
             4: 'E',
             5: 'F'}  

DEVICE_MESSAGE_MAP = {  # B = u8, b = i8, H = u16, h = i16, i = i32
    0x00: ("Battery",  "<BB",           None),
    0x01: ("IMU",      "<BBBhhhhhhhhh", ['face up', 'yaw face', 'yaw', 'pitch', 'roll', 'Ax', 'Ay', 'Az', 'gyro_x', 'gyro_y', 'gyro_z']),
    0x02: ("LED5x5",   "<B25B",         None),
    0x0A: ("Motor",    "<BBBhhbi",      ['port', 'type', 'angle', 'power', 'speed', 'position']),
    0x0B: ("Force",    "<BBBB",         ['port', 'force', 'pressure']),
    0x0C: ("Color",    "<BBbHHHB",      ['port', 'color', 'red', 'green', 'blue', 'unknown']),
    0x0D: ("Distance", "<BBh",          ['port', 'dist (mm)']),
    0x0E: ("LED3x3",   "<BB9B",         None),
}

INFO_MESSAGE = [
    ("RPC",      "<BBH", ['major','minor','build']),
    ("Firmware", "<BBH", ['major','minor','build']),
    ("MaxSize",  "<HHH", ['packet','message','chunk']),
    ("GroupID",  "<H",   None),
]

commands = {
    'info':('<B',INFO_REQUEST, None),
    'feed':('<BH', DEVICE_NOTIFICATION_REQUEST, {'values':{'updateTime':1000}})
}

TO_HIDE = ['port', 'LED5x5', 'Battery', 'type', 'unknown', ]


"""
Example implementation of the Consistent Overhead Byte Stuffing (COBS) algorithm
used by the SPIKE™ Prime BLE protocol.

This implementation prioritizes readability and simplicity over performance and
should be used for educational purposes only.
"""

DELIMITER = 0x02
"""Delimiter used to mark end of frame"""

NO_DELIMITER = 0xFF
"""Code word indicating no delimiter in block"""

COBS_CODE_OFFSET = DELIMITER
"""Offset added to code word"""

MAX_BLOCK_SIZE = 84
"""Maximum block size (incl. code word)"""

XOR = 3
"""XOR mask for encoding"""


def encode(data: bytes):
    """
    Encode data using COBS algorithm, such that no delimiters are present.
    """
    buffer = bytearray()
    code_index = block = 0
    def begin_block():
        """Append code word to buffer and update code_index and block"""
        nonlocal code_index, block
        code_index = len(buffer)  # index of incomplete code word
        buffer.append(NO_DELIMITER)  # updated later if delimiter is encountered
        block = 1  # no. of bytes in block (incl. code word)

    begin_block()
    for byte in data:
        if byte > DELIMITER:
            # non-delimeter value, write as-is
            buffer.append(byte)
            block += 1

        if byte <= DELIMITER or block > MAX_BLOCK_SIZE:
            # block completed because size limit reached or delimiter found
            if byte <= DELIMITER:
                # reason for block completion is delimiter
                # update code word to reflect block size
                delimiter_base = byte * MAX_BLOCK_SIZE
                block_offset = block + COBS_CODE_OFFSET
                buffer[code_index] = delimiter_base + block_offset
            # begin new block
            begin_block()

    # update final code word
    buffer[code_index] = block + COBS_CODE_OFFSET

    return buffer


def decode(data: bytes):
    """
    Decode data using COBS algorithm.
    """
    buffer = bytearray()

    def unescape(code: int):
        """Decode code word, returning value and block size"""
        if code == 0xFF:
            # no delimiter in block
            return None, MAX_BLOCK_SIZE + 1
        value, block = divmod(code - COBS_CODE_OFFSET, MAX_BLOCK_SIZE)
        if block == 0:
            # maximum block size ending with delimiter
            block = MAX_BLOCK_SIZE
            value -= 1
        return value, block

    value, block = unescape(data[0])
    for byte in data[1:]:  # first byte already processed
        block -= 1
        if block > 0:
            buffer.append(byte)
            continue

        # block completed
        if value is not None:
            buffer.append(value)

        value, block = unescape(byte)

    return buffer


def pack(data: bytes):
    """
    Encode and frame data for transmission.
    """
    buffer = encode(data)

    # XOR buffer to remove problematic ctrl+C
    for i in range(len(buffer)):
        buffer[i] ^= XOR

    # add delimiter
    buffer.append(DELIMITER)
    return bytes(buffer)


def unpack(frame: bytes):
    """
    Unframe and decode frame.
    """
    start = 0
    if frame[0] == 0x01:  # unused priority byte
        start += 1
    # unframe and XOR
    unframed = bytes(map(lambda x: x ^ XOR, frame[start:-1]))
    return bytes(decode(unframed))


