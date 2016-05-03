"""
Routes and views for the flask application.
"""

from flask import render_template, request
from Final_Project import app, sioapp
from flask_socketio import emit
from Final_Project.classes import Game, Player, np, random
import threading
import eventlet
import time
import colorsys

eventlet.monkey_patch()
current_game = Game((40,40))
current_loop = None

def gen_color():
    color = colorsys.hls_to_rgb(random.random(), 0.6, 1)
    color_255 = tuple([round(i * 255) for i in color])
    return "0x%0.2x%0.2x%0.2x" % color_255

def game_loop():
    frame = 0
    fps = 20
    start = time.perf_counter()
    while True:
        current_game.process_input()
        current_game.run_physics()
        sioapp.emit('game_snapshot', current_game.dump_json())
        frame += 1
        target = frame / fps
        passed = time.perf_counter() - start
        differ = target - passed
        if frame % 200 == 0:
            print('Game loop tick: %5.2f/%2d' % (frame/passed, fps))
        if differ < 0:
            differ = 0
        time.sleep(differ)

@sioapp.on('connect')
def show_connection():
    global current_loop
    print('connected to', request.sid)
    current_game.add_players(Player(request.sid, gen_color(), np.array((random.randint(0, 40), random.randint(0, 40)))))
    if current_loop == None:
        current_loop = threading.Thread(target=game_loop, args = ())
        current_loop.daemon = True
        current_loop.start()
    #emit('send_sid', request.sid)
    #emit('message', 'We pair you to client {}!'.format(request.sid), room = random.choice(sids))

@sioapp.on('disconnect')
def discon():
    print(request.sid, 'disconnected')
    current_game.remove_sid(request.sid)
    emit('player_disconnect', request.sid, broadcast = True)

@sioapp.on('player_update')
def update_player(event):
    player = current_game.get_player(request.sid)
    if player:
        player.append_input(('dir', event[0]))
        if event[1]:
            player.append_input(('accel', 0))
        if event[2]:
            player.append_input(('shoot', 0))

@app.route('/')
def main_page():
    return render_template('main.html')

