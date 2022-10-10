from math import (
    sin as _sin,
    cos as _cos,
    tan as _tan
)

from random import (
    choice as _choice,
    randint as _randint,
    triangular as _triangular,
    uniform as _uniform,
    gauss as _gauss
)


import itertools
import pyxel
import pymunk
from pymunk import constraints,Body,Poly,Space,Vec2d as Vec

graves = []

blocks = []
balls = []
fireballs = []
particles = []
platforms = []
marks = []

DBOD, SBOD, KBOD = (                          # Dynamic, Static, Kinematic body types
    Body.DYNAMIC,
    Body.STATIC,
    Body.KINEMATIC
    )

class block:
    """
        BLOCK 
        
        Base class of most physical objects within the world that can respond to
        forces extered upon in it. The base shape is rectangular in most cases.
        The body type is by default |DYNAMIC|.
         
        """
    def __init__(
        self,
        x: int = None,
        y: int = None,
        height: int = None,
        width: int = None,
        color: int = None,
        bod_type = None,
        parent = None,
        friction: int = None,
        mass: int = None,
        *args,**kwargs
    ):
        self.x = x                  # establish position of the object
        self.y = y                  # these values will become the 'center of gravity' 
        self.height = height if height is not None else 10  # Size of the object
        self.width = width if width is not None else 10     # These dimensions uniformly
        self.color = color if color is not None else 7      # distribute from the x,y coords outward
        self.parent = parent
        self.space = parent.space
        self.bod_type = bod_type if bod_type is not None else DBOD
        self.mass = mass if mass is not None else 10
        self.density = 1
        self.body = pymunk.Body(self.mass,1,self.bod_type)
        self.body.position = Vec(self.x+self.width//2,self.y+self.height//2) 
        self.poly = pymunk.Poly.create_box(self.body,(self.width,self.height))
        self.body.friction = friction if friction is not None else 1
        self.alive = True
        self.space.add(self.body,self.poly)
        blocks.append(self)

    def get_border(self,init=None):
        lines = []
        for line in self.get_border_coords(init):
            start_end = []
            for point in line:
                x, y = point[0], point[1]
                start_end.append(x)
                start_end.append(y)
            line = x1,y1,x2,y2 = start_end[0],start_end[1],start_end[2],start_end[3]    
            lines.append(line)
        print(str(lines)+"\n")
        return lines
    
    def draw_border(self):
        for line in self.outline:
            for thickness in range(5):
                if line[0] == line[2]:
                    pyxel.line(line[0]+thickness, line[1], line[2]+thickness, line[3], 9)
                else:
                    pyxel.line(line[0], line[1]+thickness, line[2], line[3]+thickness, 9)
            
                
    def get_border_coords(self,init=None):
        points = pD,pC,pB,pA = self.poly.get_vertices()
        if init is not None:
            pass
        else:
            points = [ self.body.local_to_world(p) for p in points ]
            pD,pC,pB,pA = points
        pairs = [(pA,pB),(pB,pC),(pC,pD),(pD,pA)]
        return pairs


    def reflect(self):
        self.x = self.body.position.x-self.width//2
        self.y = self.body.position.y-self.height//2
        
    def update(self):
        self.reflect()
        if 0 > self.x > pyxel.width:
            self.alive = False
        elif 0 > self.y > pyxel.height:
            self.alive = False
        if 0 >= self.width:
            self.alive = False
        elif 0 >= self.height:
            self.alive = False

    def draw(self):
        x,y,w,h,c = self.x,self.y,self.width,self.height,self.color
        pyxel.rect(x,y,w,h,c)
        
class platform(block):
    def __init__(self, x, y, w, h, parent, name=None):
        self.name = name if name is not None else ""
        super().__init__(x,y,h,w,7,SBOD,parent,0.2,10,density=1000)
        self.poly.elasticity = 1
        self.poly.density = 100
        platforms.append(self)
        
    def draw(self):
        x,y,w,h,c = self.x,self.y,self.width,self.height,self.color
        pyxel.rect(x,y,w,h,c)

class ball:
    def __init__(
        self,
        x,
        y,
        radius,
        color,
        space,
        *args,**kwargs
    ):
        self.space = space
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.body = pymunk.Body(100,0,pymunk.Body.DYNAMIC)
        self.body.position = Vec(self.x,self.y)
        self.poly = pymunk.Circle(self.body,self.radius)
        self.poly.density = 5
        self.alive = True
        self.space.add(self.body,self.poly)
        balls.append(self)

    def update(self):
        if self.radius <= 0:
            self.alive = False
        self.x = self.body.position.x
        self.y = self.body.position.y
    
    def draw(self):
        pass


class gravWell:
    def __init__(self,x,y,r,mag):
        self.center = Vec(x,y)
        self.x = x
        self.y = y
        self.aoe_radius = r
        self.body = pymunk.Body()
        self.body.position = (x,y)
        self.poly = pymunk.Circle(self.body,self.aoe_radius)
        self.affected = []
        rrange = (-(self.aoe_radius//2),self.aoe_radius//2)  
        _min = min(range(rrange[0],rrange[1]))
        _max = max(range(rrange[0],rrange[1]))
        self.ymin = self.y + _min
        self.ymax = self.y + _max
        self.xmin = self.x + _min
        self.xmax = self.x + _max
        self.magnitude = mag

    def alter_mag(self,mag):
        self.magnitude += mag

    def alter_pos(self,x,y):
        self.x = x
        self.y = y
        
    def aoe(self):
        self.poly.sensor = True
        [ self.affected.append(other) for other in fireballs if self.poly.point_query(other.body.position) ]

    def update(self):
        if pyxel.btn(pyxel.KEY_PLUS):
            self.alter_mag(10)
        if pyxel.btn(pyxel.KEY_MINUS):
            self.alter_mag(-10)
        rrange = int(-(self.aoe_radius / 2)), int(self.aoe_radius / 2)
        _min = min(range(rrange[0], rrange[1]))
        _max = max(range(rrange[0], rrange[1]))
        self.ymin = self.y + _min
        self.ymax = self.y + _max
        self.xmin = self.x + _min
        self.xmax = self.x + _max
        
class particle(ball):
    def __init__(
        self,
        emitter = None,
        x: int = None,
        y: int = None,
        radius: float = None,
        dissolve: float = None,
        life: int = None,
        transform: tuple = None,
        color: int = None,
        in_orbit: bool = None,
        pyro: bool = None,
        dismax: int = None,
        parent = None,
        *args,**kwargs
    ):
        self.emitter = emitter
        self.parent = parent
        self.space = parent.space if parent is not None else emitter.space
        self.x = x if x is not None and emitter is None else self.emitter.x
        self.y = y if y is not None and emitter is None else self.emitter.y
        self.radius = radius if radius is not None else self.emitter.radius
        self.dissolve = dissolve if dissolve is not None else 5
        self.dismax = dismax if dismax is not None else 70
        self.life = life if life is not None else 30
        self.transform = transform if transform is not None else (0,0)
        self.age = 0
        self.color = color if color is not None else self.emitter.color+1
        if self.emitter is not None:
            super().__init__(self.emitter.x,self.emitter.y,self.radius,self.color,self.emitter.space)
        else:
            super().__init__(self.x,self.y,self.radius,self.color,self.space)
        self.in_orbit = in_orbit if in_orbit is not None else True
        if self.in_orbit:
            self.orbit = emitter.orbit
        self.pyro = pyro if pyro is not None else False
        if self.emitter is not None:
            if self.pyro:
                self.body.position = (_uniform(self.emitter.body.position.x-self.radius*2,self.emitter.body.position.x+self.radius*2),_uniform(self.emitter.body.position.y-self.radius*2,self.emitter.body.position.y+self.radius*2))
                self.body.velocity_func = self.low_invert_grav_wall_coll
                self.poly.sensor = False
                self.poly.friction = 1
                self.poly.density = 0.25
                self.poly.mass = 1
                self.body.apply_impulse_at_local_point(Vec(self.emitter.body.velocity.x*(_randint(1,2)*0.025+self.transform[0]),self.emitter.body.velocity.y*(_randint(1,2)*0.025+self.transform[1])))
            else:
                self.poly.mass = 1
                self.poly.density = 0.15
                self.poly.friction = 0
                self.poly.sensor = True
                self.body.apply_impulse_at_local_point(Vec(self.emitter.body.velocity.x*(_randint(10,20)*-0.125+self.transform[0]),self.emitter.body.velocity.y*(_randint(10,20)*-0.125+self.transform[1])))
        else:
            self.body.apply_impulse_at_local_point(Vec(self.transform[0],self.transform[1]))      
        particles.append(self)


    def get_points(self):
        border = self.emitter.parent.border
        for wall in border:
            shape_ = self.poly.shapes_collide(wall.poly)
            if shape_.points == []:
                return False
            else:
                return True
            
    def collide_with(self):
        border = self.emitter.parent.border
        [  self.slow_bounce(wall) for wall in border if self.get_points() ]

    def slow_bounce(self, other):
        if other.name == "top":
            self.body.apply_impulse_at_local_point(Vec(0,1)*100)
        elif other.name == "bottom":
            self.body.apply_impulse_at_local_point(Vec(0,-1)*100)
        elif other.name == "left":
            self.body.apply_impulse_at_local_point(Vec(1,0)*100)
        elif other.name == "right":
            self.body.apply_impulse_at_local_point(Vec(-1,0)*100)

        
        self.body.velocity = self.body.velocity.interpolate_to((self.body.velocity * -1.5), 0.25)

    def low_invert_grav_wall_coll(self, body, gravity, damping, dt):
        pymunk.Body.update_velocity(body, (0,-175), .99, dt)

        
    def gravitate(self):
        self.orbit = self.emitter.orbit
        if pyxel.frame_count%5 == 0:
            ymin,ymax = self.orbit.ymin,self.orbit.ymax
            xmin,xmax = self.orbit.xmin,self.orbit.xmax
            mag       = self.orbit.magnitude/2
            if self.y <= ymin and self.x <= xmin:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(self.body.velocity.x*.01,self.body.velocity.y*.01),0.01)
                self.body.apply_impulse_at_local_point(Vec(75,75))
                self.body.apply_force_at_local_point(Vec(mag,mag))
            elif self.y >= ymax and self.x >= xmax:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(self.body.velocity.x*.01,self.body.velocity.y*.01),0.01)
                self.body.apply_impulse_at_local_point(Vec(-75,-75))
                self.body.apply_force_at_local_point(Vec(-mag,-mag))
            elif self.y <= ymin and self.x >= xmax:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(self.body.velocity.x*.01,self.body.velocity.y*.01),0.01)
                self.body.apply_impulse_at_local_point(Vec(-75,75))
                self.body.apply_force_at_local_point(Vec(-mag,mag))
            elif self.y >= ymax and self.x <= xmin:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(self.body.velocity.x*.01,self.body.velocity.y*.01),0.01)
                self.body.apply_impulse_at_local_point(Vec(75,-75))
                self.body.apply_force_at_local_point(Vec(mag,-mag))
            elif self.x <= xmin:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(self.body.velocity.x*.01,self.body.velocity.y*.01),0.01)
                self.body.apply_impulse_at_local_point(Vec(75,0))
                self.body.apply_force_at_local_point(Vec(mag,0))
            elif self.x >= xmax:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(self.body.velocity.x*.01,self.body.velocity.y*.01),0.01)
                self.body.apply_impulse_at_local_point(Vec(-75,0))
                self.body.apply_force_at_local_point(Vec(-mag,0))
            elif self.y <= ymin:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(self.body.velocity.x*.01,self.body.velocity.y*.01),0.01)
                self.body.apply_impulse_at_local_point(Vec(0,75))
                self.body.apply_force_at_local_point(Vec(0,mag))
            elif self.y >= ymax:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(self.body.velocity.x*.01,self.body.velocity.y*.01),0.01)
                self.body.apply_impulse_at_local_point(Vec(0,-75))
                self.body.apply_force_at_local_point(Vec(0,-mag))
            else:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(0,0),0.001)
        else:
            self.body.velocity = self.body.velocity.interpolate_to(self.body.velocity*2.5,0.001)            

    def update(self):
        self.age += 1
        self.x = self.body.position.x
        self.y = self.body.position.y
        if self.emitter is not None:
            self.poly.sensor = True
        else:
            self.poly.sensor = False
        if self.in_orbit:
            self.gravitate()
        if self.radius <= 0:
            self.alive = False
            particles.pop(particles.index(self))
        if self.dissolve < 0:
            if pyxel.frame_count%self.dismax == 0:
                if self.color != 13:
                    self.dissolve = -self.dissolve*3.5
                else:
                    self.dissolve = -self.dissolve*.5
        if pyxel.frame_count%3 == 0:
            self.radius -= self.dissolve*0.0025
        if self.pyro:
            self.collide_with()
            self.body.velocity = self.body.velocity.interpolate_to(Vec(0,0), .01)
        self.poly.mass = self.emitter.parent.rmass
        
    def draw(self):
        x, y, r, c = self.x, self.y, self.radius, self.color
        if not self.pyro:
            if self.emitter is not None:
                cs = 7 if self.emitter.parent.bgc == 0 else 0
            else:
                cs = 7
            pyxel.circb(x, y, r + 1, cs)
            pyxel.circ(x, y, r, c)
        else:
                pyxel.circ(x+1,y+1,r+1,1)
                pyxel.circ(x,y,r,c)

class explosion(particle):
    def __init__(self, source):
        self.source = source
        self.smoke_a = [particle(self.source,self.source.x,self.source.y,radius=self.source.radius-3,dissolve=_gauss(_uniform(-250,-1),1.1),transform=(0,0), color=13,in_orbit=False,pyro=True,dismax=_randint(30,200)) for _ in range(3) ]
        self.smoke_b = [particle(self.source,self.source.x,self.source.y,radius=self.source.radius+3,dissolve=_gauss(_uniform(-250,-1),.5),transform=(0,0), color=13,in_orbit=False,pyro=True,dismax=_randint(65,135)) for _ in range(3) ]
        self.smoke_c = [particle(self.source,self.source.x,self.source.y,radius=self.source.radius+3,dissolve=_gauss(_uniform(-250,-1),.5),transform=(_triangular(_uniform(-.25,.25),_uniform(-.25,.25)),_triangular(_uniform(-.25,.25),_uniform(-.25,.25))), color=_choice([9,10]),in_orbit=False,pyro=True,dismax=_randint(65,135)) for _ in range(3) ]
        self.pyrotech = [particle(self.source,self.source.x,self.source.y,radius=self.source.radius,dissolve=_gauss(_uniform(-1000,-500),1.6),transform=(_uniform(-.25,.25),_uniform(-.25,.25)), color=_choice([9, 10]),in_orbit=False,pyro=True,dismax=_randint(25,60))]

class fireball:
    def __init__(
        self, 
        parent,
        in_orbit,
        somatic,
        x: int = None,
        y: int = None,
        radius: float = None,
        color: int = None,
        *args,**kwargs
    ):
        self.age                = 0
        self.parent             = parent
        self.space              = parent.space
        self.in_orbit           = in_orbit if in_orbit is not None else False
        self.orbit              = self.parent.orbit
        self.x                  = x if x is not None else SCREENx_CENTER
        self.y                  = y if y is not None else SCREENy_CENTER
        self.color              = color if color is not None else 9 
        self.radius             = radius if radius is not None else 3
        self.body               = pymunk.Body(10,1,pymunk.Body.DYNAMIC)
        self.poly               = pymunk.Circle(self.body,self.radius)
        self.poly.friction      = 1
        self.poly.density       = 1
        self.alive              = True
        self.spec()
        self.contact            = False
        self.contact_moment     = 0
        self.trail              = []
        self.space.add(self.body,self.poly)
        self.halo               = 0
        self.shot               = self.parent.gun.aim
        self.body.apply_impulse_at_local_point(self.shot)
        fireballs.append(self)

    def get_shot(self):
        angle = self.parent.aim_angle
        x = cos(angle)
        y = tan(x)
        v = Vec(x,y)
        p = self.parent.shot_power
        return v * p

    def spec(self):
        self.body.position = Vec(self.x,self.y)
        self.poly.elasticity += 1
        self.poly.mass = 0.5

    def reflect(self):
        self.x = self.body.position.x
        self.y = self.body.position.y

    def conflag(self):
        self.body.velocity = self.body.velocity.interpolate_to(Vec(0,0),0.1)
        self.contact_moment = self.age
        self.contact = True
        
    def explode(self):
        [ explosion(self) for _ in range(_randint(7,11)) ]
        [ particle(self,self.x,self.y,radius=_gauss(self.radius,0.25), transform=(_triangular(_uniform(-15,0 ), _uniform(0, 15)), _triangular(_uniform(-15, 0 ), _uniform(0, 15))),dissolve=_gauss(_randint(5,100),0.02), color=_choice([7, 9, 10]),in_orbit=False) for _ in range(_randint(35,50)) ]
        self.alive = False
        graves.append((self.x,self.y,self.radius))

    def make_trail(self,x):
        velc = round((abs(self.body.velocity.int_tuple[0])+abs(self.body.velocity.int_tuple[1]))*0.01)
        velc = abs(velc)
        if velc >= 9:
            velc = 8
        if pyxel.frame_count%(9-velc) <= velc*.5:
            
            [ self.trail.append(particle(self,dissolve=100,transform=(i%.25,i%.75),in_orbit=False)) for i in range(7) if x == i ]
            

    def pulse_halo(self):
        if pyxel.frame_count%200 <= 100:
            self.halo += .1
        else:
            self.halo -= .1
            

    def gravitate(self):
        if pyxel.frame_count%2 == 0:
            ymin,ymax = self.orbit.ymin,self.orbit.ymax
            xmin,xmax = self.orbit.xmin,self.orbit.xmax
            mag       = self.orbit.magnitude/2
            if self.y <= ymin and self.x <= xmin:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(self.body.velocity.x*.01,self.body.velocity.y*.01),0.01)
                self.body.apply_impulse_at_local_point(Vec(75,75))
                self.body.apply_force_at_local_point(Vec(mag,mag))
            elif self.y >= ymax and self.x >= xmax:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(self.body.velocity.x*.01,self.body.velocity.y*.01),0.01)
                self.body.apply_impulse_at_local_point(Vec(-75,-75))
                self.body.apply_force_at_local_point(Vec(-mag,-mag))
            elif self.y <= ymin and self.x >= xmax:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(self.body.velocity.x*.01,self.body.velocity.y*.01),0.01)
                self.body.apply_impulse_at_local_point(Vec(-75,75))
                self.body.apply_force_at_local_point(Vec(-mag,mag))
            elif self.y >= ymax and self.x <= xmin:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(self.body.velocity.x*.01,self.body.velocity.y*.01),0.01)
                self.body.apply_impulse_at_local_point(Vec(75,-75))
                self.body.apply_force_at_local_point(Vec(mag,-mag))
            elif self.x <= xmin:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(self.body.velocity.x*.01,self.body.velocity.y*.01),0.01)
                self.body.apply_impulse_at_local_point(Vec(75,0))
                self.body.apply_force_at_local_point(Vec(mag,0))
            elif self.x >= xmax:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(self.body.velocity.x*.01,self.body.velocity.y*.01),0.01)
                self.body.apply_impulse_at_local_point(Vec(-75,0))
                self.body.apply_force_at_local_point(Vec(-mag,0))
            elif self.y <= ymin:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(self.body.velocity.x*.01,self.body.velocity.y*.01),0.01)
                self.body.apply_impulse_at_local_point(Vec(0,75))
                self.body.apply_force_at_local_point(Vec(0,mag))
            elif self.y >= ymax:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(self.body.velocity.x*.01,self.body.velocity.y*.01),0.01)
                self.body.apply_impulse_at_local_point(Vec(0,-75))
                self.body.apply_force_at_local_point(Vec(0,-mag))
            else:
                self.body.velocity = self.body.velocity.interpolate_to(Vec(0,0),0.001)
        else:
            self.body.velocity = self.body.velocity.interpolate_to(self.body.velocity*1.5,0.01)

    def handle_collision(self):
        plist = [self.poly.shapes_collide(plat.poly) for plat in platforms]
        if [ True for p in plist if p.points != [] ]:
            self.explode()     
                   
    def update(self):
        if not self.alive:
            fireballs.pop(fireballs.index(self))
        self.age += 1
        self.pulse_halo()
        self.reflect()
        self.handle_collision()
        [ self.trail.pop(self.trail.index(part)) for part in self.trail if not part.alive ]
        self.make_trail(_randint(0,5))
        if self.in_orbit:
            self.orbit = self.parent.orbit
            self.gravitate()
        if self.radius <= -2:
            self.alive = False
        if self.x > pyxel.width or self.x < 0:
            self.alive = False
        if self.y > pyxel.height or self.y < 0:
            self.alive = False

    def draw(self):
        if self.parent.bgc == 0:
            c = 7
        else:
            c = 0 
        if self.parent.party:
            c = pyxel.frame_count%7    
        [ part.draw() for part in self.trail ]
        pyxel.circ(self.x,self.y,self.radius+2,c)
#        pyxel.circb(self.x,self.y,self.radius + 3 + self.halo,10)
#        pyxel.circb(self.x,self.y,self.radius + 5 + self.halo*1.33,9)
        pyxel.circ(self.x,self.y,self.radius,self.color)

class cannon:
    def __init__(
        self,
        parent = None,
        x: int = None,
        y: int = None,
        *args, **kwargs
    ):
        self.parent = parent
        self.x = x if x is not None else pyxel.width//6 + 50
        self.y = y if y is not None else pyxel.height - 100
        self.aim_x = pyxel.width//2
        self.aim_y = pyxel.height//2
        self.x2 = self.aim_x
        self.y2 = self.aim_y
        self.aim = Vec(self.aim_x, self.aim_y)
        self.aim_angle = self.get_aim_angle()
        self.shot_power = self.aim_x

    def fire_shot(self):
        if not pyxel.btn(pyxel.KEY_LCTRL):
            if pyxel.btnp(pyxel.KEY_SPACE):
                fireball(self.parent, False, False, self.x, self.y)
        else:
            if pyxel.btnp(pyxel.KEY_SPACE):
                fireball(self.parent, True, False, self.x, self.y)                

    def aim_shot(self):
        if pyxel.btn(pyxel.KEY_UP):
            self.aim_y -= 2.5
            self.y2 -= 2.5
        if pyxel.btn(pyxel.KEY_DOWN):
            self.aim_y += 2.5
            self.y2 += 2.5
        if pyxel.btn(pyxel.KEY_LEFT):
            self.aim_x -= 2.5
            self.x2 -= 2.5
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.aim_x += 2.5
            self.x2 += 2.5

    def get_aim_point(self):
        return Vec(self.aim_x-300, self.aim_y)

    def get_aim_angle(self):
        return self.aim.angle


    def recv_input(self):
        self.aim_shot()
        self.fire_shot()

    def update(self):
        self.recv_input()
        self.aim = self.get_aim_point()
        self.aim_angle = self.get_aim_angle()
        self.shot_power = self.aim_x

    def draw(self):
        pyxel.trib(self.x,self.y,self.aim_x,self.y,self.aim_x, self.aim_y,7)
        # for i in range(180):
        #     if i <= 90:
        #         pyxel.line(self.x2+i,self.y2-i*(i%.3),self.x2+i*1.1,self.y2-i*(i%.3),7)
        #     else:
        #         pyxel.line(self.x2+90+i,self.y2-90+i*(i%5*.1),self.x2+90+i*1.25,self.y2-90+i*(i%5*.1),7)


