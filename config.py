import os


SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Enable debug mode. for the debug toolbar
DEBUG = True

SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:root@localhost:5432/attendance_test'

SQLALCHEMY_TRACK_MODIFICATIONS = False