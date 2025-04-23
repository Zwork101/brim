from asyncio import get_event_loop
from functools import wraps
from pathlib import Path
from typing import Optional

from backend.db import Base
from seeds import get_seeds, group_seeds, plant_seeds

import click
from pytailwindcss import run as tailwind_run, install as tailwind_install
from sqlalchemy.ext.asyncio import async_sessionmaker
from quart import Quart, current_app
from quart.cli import with_appcontext


def run_sync(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        return get_event_loop().run_until_complete(func(*args, **kwargs))
    return _wrapper


def setup_cli(app: Quart):
    
    @app.cli.group()
    def tailwind():
        pass
    
    @tailwind.command()
    @click.option("--version")
    def install(version: Optional[str] = None):
        tailwind_install(version)  # pyright: ignore [reportArgumentType]
        
    @tailwind.command()
    @click.option("--no-minify", default=False)
    @click.option("--no-optimize", default=False)
    @with_appcontext
    def generate(no_minify: bool, no_optimize: bool):
        tailwind_run(
            ['--input', str(Path(current_app.static_folder).parent.joinpath(Path("_src/input.css")))] + # pyright: ignore [reportArgumentType]
            ['--output', str(Path(current_app.static_folder).joinpath("css/output.css"))] + # pyright: ignore [reportArgumentType]
            (['--minify'] if not no_minify else []) +
            (['--optimize'] if not no_optimize else []) +
            ['--cwd', str(Path(current_app.template_folder).resolve())]  # pyright: ignore [reportArgumentType]
        )
    
    @app.cli.group()
    def db():
        pass
    
    @db.command()
    @run_sync
    async def init() -> None:
        async with app.config['SQL_ENGINE'].begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        print("Created Database Metadata")
        
    @db.command()
    @click.option("-s", "--skip", default=[], multiple=True)
    @click.option("-i", "--include", default=[], multiple=True)
    @run_sync
    async def seed(skip, include) -> None:
        if skip and include:
            raise ValueError("Cannot skip and include seeds, only one or the other.") 
            
        async with app.app_context():
            seeds = get_seeds()
        
            if skip:
                seeds = tuple(seed for seed in seeds if seed.module.__name__ not in skip)
            elif include:
                seeds = tuple(seed for seed in seeds if seed.module.__name__ in include)
            
            grouped = group_seeds(*seeds)
            for group in grouped:
                await plant_seeds(async_sessionmaker(app.config['SQL_ENGINE'], expire_on_commit=False), *group)
