from importlib import import_module
from pathlib import Path
import logging
import time
import os
from typing import Type

from backend.db import db_app
from backend.htmx import htmx
from backend.auth import auth
from cli import setup_cli
from config import Config, DevelopmentConfig
from development import dev_engine

from sqlalchemy.ext.asyncio import create_async_engine
from quart import Quart, Blueprint


def create_app(config: Type[Config] = DevelopmentConfig) -> Quart:
    
    app = Quart(__name__, static_folder="static/dist", static_url_path="/static", template_folder="templates")
    
    app.config.from_object(config)
    app.config['BRIM_START_TIME'] = time.perf_counter()
    app.config['BRIM_CONFIG_TYPE'] = config
    app.config['SQL_ENGINE'] = create_async_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    app.config['QUART_RUN_PORT'] = 8080
        
    for root, _, files in os.walk("backend"):
        for file in files:
            if file.endswith("routes.py"):
                route_module = import_module('.'.join(Path(root).parts) + "." + file[:-3])
                for _, value in route_module.__dict__.items():
                    if isinstance(value, Blueprint):
                        app.register_blueprint(value)
                        logging.debug(f"Added {value.name} blueprint.")
                        
    htmx.init_app(app)
    db_app.init_app(app)
    auth.init_app(app)
    setup_cli(app)  # pyright: ignore [reportArgumentType]
    
    if app.config.get("BRIM_LIVE_RELOAD", False):
        logging.warning("Live template reloading enabled. DO NOT USE IN PRODUCTION, POTENTIALLY VERY UNSECURE.")
        dev_engine.init_app(app)
                            
    return app
