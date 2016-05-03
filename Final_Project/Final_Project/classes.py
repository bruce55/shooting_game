import random
import numpy as np
import eventlet

class Entity:
    deceleration = 0.3
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
            mag = 1 - Entity.deceleration/np.linalg.norm(self.vel)
            if mag < 0:
                self.vel = np.array([0,0], 'float64')
                self.static = True
            else:
                self.vel *= mag

    def set_vel(self, vel):
        self.static = False
        self.vel = vel

    def collision_detection(self, object):
        dist = np.linalg.norm(self.pos - object.pos)
        if dist < self.size + object.size:
            return True
        else:
            return False

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
        self.players.remove(player)

    def remove_sid(self, sid):
        player = self.get_player(sid)
        self.remove_player(player)
    
    def generate_entities(self, n):
        for i in range(n):
            self.entities.append(Entity([random.randint(0, self.size[0]), random.randint(0, self.size[1])], random.randint(2, 5)))

    def run_physics(self):
        for player in self.players:
            player.run_physics()
        for entity in self.entities:
            entity.run_physics()
            for player in self.players:
                if player.hp > 0:
                    if player.collision_detection(entity):
                        pass

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
                