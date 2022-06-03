#################################################
# File:    polynode.py
# Author:  Diego Andrade (bets636@gmail.com)
# Date:    June 3, 2022
# Purpose: Manual controller for driving Polyver 
#          rovers
# 
#################################################

from math import floor
from pyPS4Controller.controller import Controller

class PolyverController(Controller):
    # ---- Constants -----------------------
    MAX_SPEED_OUTPUT = 250
    MIN_SPEED_OUTPUT = -250

    MOVE_STEP        = 6

    L3_UP_MAX = -32767
    L3_DOWN_MAX = 32767

    R3_UP_MAX = -32767
    R3_DOWN_MAX = 32767

    JOYSTICK_DEADZONE = 500

    # ---- Members -------------------------
    event_callback=None

    max_val = 0

    def __init__(self, event_callback, **kwargs):
        self.event_callback = event_callback
        Controller.__init__(self, **kwargs)

    def on_x_press(self):
        return

    def on_x_release(self):
        self.event_callback('m: 0')

    def  on_triangle_press(self):
        return

    def on_triangle_release(self):
        self.event_callback('m: 1')

    def on_up_arrow_press(self):
        self.event_callback('x: 0 y: {}'.format(self.MOVE_STEP))

    def on_down_arrow_press(self):
        self.event_callback('x: 0 y: -{}'.format(self.MOVE_STEP))

    def on_up_down_arrow_release(self):
        return 

    def on_left_arrow_press(self):
        self.event_callback('x: -{} y: 0'.format(self.MOVE_STEP))
    
    def on_right_arrow_press(self):
        self.event_callback('x: {} y: 0'.format(self.MOVE_STEP))

    def on_left_right_arrow_release(self):
        return 

    def on_L3_up(self, value):
        out_value = floor(value / self.L3_UP_MAX * self.MAX_SPEED_OUTPUT)
        out_str = 'l: {}'.format(out_value)
        self.event_callback(out_str)

    def on_L3_down(self, value):
        out_value = floor(value / self.L3_DOWN_MAX * self.MIN_SPEED_OUTPUT)
        out_str = 'l: {}'.format(out_value)
        self.event_callback(out_str)

    def on_L3_y_at_rest(self):
        self.event_callback('l: 0')

    def on_L3_left(self, value):
        return 
    def on_L3_right(self, value):
        return
    def on_L3_x_at_rest(self):
        return

    def on_R3_up(self, value):
        out_value = floor(value / self.R3_UP_MAX * self.MAX_SPEED_OUTPUT)
        out_str = 'r: {}'.format(out_value)
        self.event_callback(out_str)

    def on_R3_down(self, value):
        out_value = floor(value / self.R3_DOWN_MAX * self.MIN_SPEED_OUTPUT)
        out_str = 'r: {}'.format(out_value)
        self.event_callback(out_str)

    def on_R3_y_at_rest(self):
        self.event_callback('r: 0')

    def on_R3_left(self, value):
        return 
    def on_R3_right(self, value):
        return
    def on_R3_x_at_rest(self):
        return

    def on_circle_press(self):
        return
    def on_circle_release(self):
        return
    def on_square_press(self):
        return 
    def on_square_release(self):
        return 
    def on_share_press(self):
        return
    def on_share_release(self):
        return
    def on_options_press(self):
        return
    def on_options_release(self):
        return
    def on_playstation_button_press(self):
        return
    def on_playstation_button_release(self):
        return

    def on_L1_press(self):
        return
    def on_L1_release(self):
        return
    def on_L2_press(self, value):
        return
    def on_L2_release(self):
        return
    def on_L3_press(self):
        return
    def on_L3_release(self):
        return

    def on_R1_press(self):
        return
    def on_R1_release(self):
        return
    def on_R2_press(self, value):
        return
    def on_R2_release(self):
        return
    def on_R3_press(self):
        return
    def on_R3_release(self):
        return

