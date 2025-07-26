
# ---------------------------------Display-----------------------------
from hub import light_matrix
from hub import light
import color

# Change the power button light to red (light.CONNECT gives the BLE btn)
light.color(light.POWER, color.RED)

light_matrix.clear()
light_matrix.write("LEGO")
row,col,bright = 1,2,100
light_matrix.set_pixel(col,row,bright)
print(light_matrix.get_pixel(row,col))

# ---------------------------------Buttons /Sound-----------------------------
from hub import button
from hub import sound

fred = button.pressed(button.LEFT)  # or btn = { 0:'power', 1:'left', 2:'right', 3:'connect'}
print('pressed for %d msec'% (fred))

sound.beep(220)

# ---------------------------------Motors-----------------------------
from hub import port
import motor

motor.run(port.E, 500) # essentials motor: -660 to 660, Medium motor: -1110 to 1110, Large motor: -1050 to 1050
time.sleep(1)
motor.stop(port.E)

motor.absolute_position(port.E) # -180 to 180
motor.velocity(port.E)  # essentialn motor: -660 to 660, Medium motor: -1110 to 1110, Large motor: -1050 to 1050
motor.relative_position(port.E) # -infinity to + infinity
motor.reset_relative_position(port.E)

import motor_pair

motor_pair.unpair(motor_pair.PAIR_1)   # remove any old pairing
motor_pair.pair(motor_pair.PAIR_1, port.E, port.F)

motor_pair.move(motor_pair.PAIR_1, 0, velocity=280, acceleration=100) #0 is steering - go straight (-100 to 100)            
motor_pair.stop(motor_pair.PAIR_1)

# ---------------------------------Sensors-----------------------------
import force_sensor as fs

fs.pressed(port.B)
fs.raw(port.B)
fs.force(port.B)

import color_sensor

color_sensor.color(port.B) # -1:'ERR',0:"BLACK",1:"MAGENTA",2:"PURPLE",3:"BLUE",4:"AZURE",5:"TURQUOISE",6:"GREEN",7:"YELLOW",8:"ORANGE",9:"RED",10:"WHITE",11:"DIM_WHITE",
color_sensor.reflection(port.B)
color_sensor.rgbi(port.B)  #RGBI

import distance_sensor as ds

ds.distance(port.B)

from hub import motion_sensor

motion_sensor.gesture() #    motion_sensor.TAPPED,DOUBLE_TAPPED,SHAKEN,FALLING,UNKNOWN
motion_sensor.tilt_angles() # yaw pitch and roll values as integers. Values are decidegrees
motion_sensor.acceleration() #The values are mili G, so 1 / 1000 G
motion_sensor.angular_velocity() # The values are decidegrees per second
    