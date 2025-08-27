import os

class Appconfig(object):
    SECRET_KEY = os.getenv("SECRET_KEY", 'fallback_secret_key')
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", 'mysql+mysqlconnector://root@localhost/seenITApp')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
