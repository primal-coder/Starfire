from random import (
    choice as _choice,
    randint as _randint,
    triangular as _triangular,
    uniform as _uniform,
    gauss as _gauss
)
from subprocess import call
from typing import (
    Callable as _Callable,
    Any as _Any
)
import pyxel
import pymunk
from pymunk import (
    constraints, 
    Body, 
    Poly, 
    Space, 
    Vec2d as Vec
)



from .core import *



class configuration:
    FPS = 60
    SCREENx, SCREENy = (
        1280,                                   # Screen width(x)
        720                                     # Screen height(y)
    )
    SCREENx_CENTER, SCREENy_CENTER = (
        SCREENx // 2, 
        SCREENy // 2
    )
    vCENTER = Vec(                              # Vector coordinates for screen center
        SCREENx_CENTER, 
        SCREENy_CENTER
    )
    DBOD, SBOD, KBOD = (                          # Dynamic, Static, Kinematic body types
        Body.DYNAMIC,
        Body.STATIC,
        Body.KINEMATIC
    )
    def __init__(
        self,
        app: _Callable[[_Any], None] = None,
        *args,**kwargs
    ):    
        self._is_init = False
        self._is_running = False    
        self.init_pyxel()
        self.run = self.run_pyxel(app) if app is not None else None

    def init_pyxel(self):
        self._is_init = True
        pyxel.init(configuration.SCREENx, configuration.SCREENy, fps=configuration.FPS)
        pyxel.fullscreen(False)

    def run_pyxel(self, app: _Callable[[_Any], None]):
        self._is_running = True
        if app is not None:
            app = app()
            pyxel.run(app.update, app.draw)
        else:
            pass

if __name__ != '__main__':
    app = mainProcess
    config = configuration(app)