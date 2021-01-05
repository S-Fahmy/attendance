import os


SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Enable debug mode. for the debug toolbar
DEBUG = True
heroku_uri = 'postgres://gxtdvxhtbgetfi:969542fa57489f1c593c478a56f9cd8dff95965787c4e80745f55181e61d0797@ec2-3-231-241-17.compute-1.amazonaws.com:5432/dd10eco1qeka5g'
local_uri = 'postgresql://postgres:root@localhost:5432/attendance_test'

SQLALCHEMY_DATABASE_URI = heroku_uri

SQLALCHEMY_TRACK_MODIFICATIONS = False