import os


SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Enable debug mode. for the debug toolbar
DEBUG = True

#TODO: later if i need to connect to this locally make it an OS env variable.
local_uri = 'postgresql://postgres:root@localhost:5432/attendance_test'

SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
SQLALCHEMY_TRACK_MODIFICATIONS = False