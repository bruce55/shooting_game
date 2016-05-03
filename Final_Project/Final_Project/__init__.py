"""
The flask application package.
"""

from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
sioapp = SocketIO(app)

import Final_Project.views
