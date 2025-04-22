import os

class Config:
    SECRET_KEY = os.environ.get("QUART_SECRET_KEY", "PLEASE_REPLACE_ME")


class DevelopmentConfig(Config):
    DEBUG = True
    SERVER_NAME = "127.0.0.1:8080"
    SQLALCHEMY_DATABASE_URI = "sqlite+aiosqlite:///brimstone.db"
    
    
class TestingConfig(Config):
    DEBUG = False
    SERVER_NAME = "127.0.0.1:8080"
    SQLALCHEMY_DATABASE_URI = "sqlite+aiosqlite:///brimstone.db"


class ProductionConfig(Config):
    DEBUG = False
