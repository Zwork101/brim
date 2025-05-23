import os

class Config:
    SECRET_KEY = os.environ.get("QUART_SECRET_KEY", "PLEASE_REPLACE_ME")


class DevelopmentConfig(Config):
    SERVER_NAME = "127.0.0.1:8080"
    SQLALCHEMY_DATABASE_URI = "sqlite+aiosqlite:///brimstone.db"
    TEMPLATES_AUTO_RELOAD = True
    
    BRIM_LIVE_RELOAD = True
    
class TestingConfig(Config):
    TESTING = True
    SERVER_NAME = "127.0.0.1:8080"
    SQLALCHEMY_DATABASE_URI = "sqlite+aiosqlite:///brimstone.db"


class ProductionConfig(Config):
    DEBUG = False
