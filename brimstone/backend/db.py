from functools import wraps
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import String
from werkzeug.local import LocalProxy
from quart import Quart, g

class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "User"
    
    id: Mapped[int]         = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str]   = mapped_column(String(32))
    email: Mapped[str]      = mapped_column(String(320))
    password: Mapped[str]


def require_app(func):
        @wraps(func)
        def check_app(self: "Database", *args, **kwargs):
            if self._app is None:
                raise NotImplementedError(f"Cannot use {func.__name__} before it's been initialized")
            return func(self, *args, **kwargs)
        return check_app

class Database:
    
    def __init__(self) -> None:
        self._app: Optional[Quart] = None    
        
    @require_app
    def get_db(self) -> async_sessionmaker[AsyncSession]:
        if 'db' not in g:
            g.db = async_sessionmaker(self._app.config['SQL_ENGINE'], expire_on_commit=False)  # pyright: ignore [reportOptionalMemberAccess]
        return g.db

    # def teardown_db(self, exception):
    #     db = g.pop('db', None)
        
    #     if db is not None:
    #         db.dispose()
    
    def init_app(self, app: Quart):
        self._app = app
        # self._app.teardown_appcontext(self.teardown_db)


db_app = Database()
db: async_sessionmaker[AsyncSession] = LocalProxy(db_app.get_db)  # type: ignore [reportAssignmentType]
