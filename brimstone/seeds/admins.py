from typing import Awaitable, Callable, Union

from backend.db import User

from config import ProductionConfig

from sqlalchemy.ext.asyncio import AsyncSession
from quart import current_app
from werkzeug.security import generate_password_hash

AsyncFunction = Callable[[AsyncSession], Awaitable[None]]
PriorityFunction = tuple[AsyncFunction, int]


__priority__ = 1000


def operations() -> tuple[Union[AsyncFunction, PriorityFunction]]:
    
    async def create_admin(session: AsyncSession):
        admin = User(
            username = "admin",
            password = generate_password_hash("adminadmin"),
            email = "admin@website"
        )
        
        session.add(admin)
    
    if current_app.config['BRIM_CONFIG_TYPE'] is not ProductionConfig:
        return (create_admin, )
    
    return tuple()
