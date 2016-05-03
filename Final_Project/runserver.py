"""
This script runs the Final_Project application using a development server.
"""

from os import environ
from Final_Project import app, sioapp

if __name__ == '__main__':
    HOST = environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    sioapp.run(app, '0.0.0.0', PORT)
