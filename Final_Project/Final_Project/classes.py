import random
import numpy as np
import eventlet
import json
from Final_Project.views import sioapp

class Entity:
    deceleration = 0.02
    def __init__(self, pos, size):
        self.pos = np.array(pos, 'float64')
        self.size = size
        self.vel = np.array([0,0], 'float64')
        self.static = True

    def __str__(self):
        return str(self.pos)
    def run_physics(self):
        if not self.static:
            self.pos += self.vel
            mag = 1 - self.deceleration / np.linalg.norm(self.vel)
            if mag <= 0:
                self.vel = np.array([0,0], 'float64')
                self.static = True
            else:
                self.vel *= mag
            if self.pos[0] > 40:
                self.vel[0] *= -1
                self.pos[0] = 40
            if self.pos[1] > 40:
                self.vel[1] *= -1
                self.pos[1] = 40
            if self.pos[0] < 0:
                self.vel[0] *= -1
                self.pos[0] = 0
            if self.pos[1] < 0:
                self.vel[1] *= -1
                self.pos[1] = 0

    def set_vel(self, vel):
        self.static = False
        self.vel = vel

    def collision_detection(self, object):
        dist = np.linalg.norm(self.pos - object.pos)
        if dist < self.size + object.size:
            return True
        else:
            return False

    def rotate_vec(self, vec, rad):
        """Rotate the vector clock-wise by the angle defined in rad"""
        vec = np.array([vec[0] * np.math.cos(rad) - vec[1] * np.math.sin(rad), vec[0] * np.math.sin(rad) + vec[1] * np.math.cos(rad)], 'float64')
        return vec
        
class Bullet(Entity):
    deceleration = 0.1

class Game:
    def __init__(self, size):
        self.players = []
        self.size = size
        self.entities = []
        self.generate_entities(5)

    def get_player(self, sid):
        try:
            return list(filter(lambda player: player.sid == sid, self.players))[0]
        except IndexError:
            return None

    def add_players(self, player):
        self.players.append(player)

    def remove_player(self, player):
        try:
            self.players.remove(player)
        except ValueError:
            pass

    def remove_sid(self, sid):
        player = self.get_player(sid)
        self.remove_player(player)
    
    def generate_entities(self, n):
        for i in range(n):
            self.entities.append(Entity([random.randint(0, self.size[0]), random.randint(0, self.size[1])], random.randint(8, 12)))

    def run_physics(self):
        for player in self.players:
            player.run_physics()
            for bullet in player.bullets:
                bullet.run_physics()
                if bullet.static:
                    sioapp.emit('bullet_expire', [player.sid, id(bullet)])
                    player.bullets.remove(bullet)
        for entity in self.entities:
            entity.run_physics()
            for player in self.players:
                if player.hp > 0:
                    if player.collision_detection(entity):
                        pass

    def process_input(self):
        for player in self.players:
            player.process_input()

    def dump_json(self):
        players = [{'sid': player.sid, 
                    'phys': (tuple(player.pos), 
                             tuple(player.vel), 
                             player.size, 
                             player.dir), 
                    'color': player.color,
                    'bullets': [{'id': id(bullet), 
                                 'phys': (tuple(bullet.pos), 
                                          tuple(bullet.vel), 
                                          bullet.size)
                                 } for bullet in player.bullets]} for player in self.players]
        entities = [{'id': id(entity), 
                     'phys': (tuple(entity.pos), 
                              tuple(entity.vel), 
                              entity.size)
                     } for entity in self.entities]
        return json.dumps({'players': players, 'entities':entities})

class Player(Entity):
    def __init__(self, sid, color, pos):
        self.sid = sid
        self.score = 0
        self.color = color
        self.pos = np.array(pos, 'float64')
        self.size = 5
        self.vel = np.array([0,0], 'float64')
        self.static = True
        self.dir = 0.0
        self.inputQueue = eventlet.Queue()
        self.hp = 100
        self.bullets = []

    def get_session(self):
        return self.sid

    def append_input(self, event):
        self.inputQueue.put(event)

    def process_input(self):
        while not self.inputQueue.empty():
            event = self.inputQueue.get()
            if event[0] == 'dir':
                self.dir = float(event[1])
            elif event[0] == 'accel':
                accel = self.rotate_vec(np.array([0, 0.05], 'float64'), float(self.dir))
                self.set_vel(self.vel + accel)
                if np.linalg.norm(self.vel) > 1:
                    self.set_vel(1 / np.linalg.norm(self.vel) * self.vel)
            elif event[0] == 'shoot':
                bullet = Bullet(self.pos, 2)
                vel = self.rotate_vec(np.array([0, 3], 'float64'), float(self.dir)) + self.vel
                bullet.set_vel(vel)
                self.bullets.append(bullet)
