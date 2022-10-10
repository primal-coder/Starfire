import math
import random

import pyxel
import pymunk
from pymunk import (
    constraints, 
    Body, 
    Poly, 
    Space, 
    Vec2d as Vec
)

from .primary import *

class mainProcess:
    def __init__(self):
        self.bgc = 0
        self.time_scale = 0
        self.space = Space()
        self.space.gravity = (0, 1000)
        self.rmass = 1.0
        self.g = 0
        self.orbit = gravWell(pyxel.width/2, pyxel.height/2, 100, 100)
        self.sensor = True
        self.party = False
        self.gun = cannon(self)
        self.border = self.generate_forms()

    def generate_forms(self):
        top = platform(0, 0, pyxel.width-50, 50, self,"top")
        bottom = platform(0, pyxel.height-50, pyxel.width, 50, self,"bottom")
        left = platform(0, 0, 50, pyxel.height-50, self,"left")
        right = platform(pyxel.width-50, 0, 50, pyxel.height-50, self,"right")
        return top, bottom, left, right
    
    def switch_(self,var):
        return bool(abs(int(var)-1))

    def switch_party(self):
        self.party = self.switch_(self.party)

    def switch_sensor(self):
        self.sensor = self.switch_(self.sensor)
        
    def switches(self):
        if pyxel.btnp(pyxel.KEY_S):
            self.switch_sensor()
        if pyxel.btnp(pyxel.KEY_P):
            self.switch_party()

    def alter_time(self):
        if pyxel.btn(pyxel.KEY_8):
            if pyxel.btn(pyxel.KEY_RSHIFT):
                self.time_scale -= 1e-06
            elif pyxel.btn(pyxel.KEY_RALT):
                self.time_scale = 0
        elif pyxel.btn(pyxel.KEY_7):
            if pyxel.btn(pyxel.KEY_RSHIFT):
                self.time_scale += 1e-06

    def move_orbit(self):
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.orbit.alter_pos(pyxel.mouse_x, self.mouse_y)


    def invert_color(self):
        if pyxel.btnp(pyxel.KEY_I):
            self.bgc = 7 if self.bgc == 0 else 0

    def conflagrate(self):
        [b.conflag() for b in fireballs if pyxel.btnp(pyxel.KEY_E)]


    def recv_input(self):
        self.switches()
        self.alter_time()
        self.invert_color()
        self.conflagrate()

    def update(self):
        if self.time_scale >= 4:
            self.time_scale = 3.9999999 
        self.space.step(1 / 240 + (self.time_scale * 60))
        self.recv_input()
        self.gun.update()
        [fb.update() for fb in fireballs]
        [b.explode() for b in fireballs if b.contact]
        [part.update() for part in particles]
        self.orbit.update()

    def firemark(self, x, y):
        for i in range(25):
            marks.append((Vec(tri(uni(x-rndi(100, 300), x), uni(x, x+rndi(100, 300))),
                         tri(uni(y-rndi(100, 300), y), uni(y, y+rndi(100, 300)))), Vec(x, y)))

    def draw(self):
        pyxel.cls(self.bgc)
        if self.bgc == 0:
            for i in range(10):
                [pyxel.line(p.x, p.y, s.x, s.y, round(p.x) % 15)
                 for p, s in marks]
        else:
            [pyxel.line(p.x, p.y, s.x, s.y, 0) for p, s in marks]
        [fb.draw() for fb in fireballs]
        [part.draw() for part in particles]
        [plat.draw() for plat in platforms]
        self.gun.draw()
        pyxel.circb(self.gun.aim.x, self.gun.aim.y, 10, 7)