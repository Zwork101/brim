from functools import wraps
from typing import TYPE_CHECKING, Any, Optional

from backend.db import db, User

from sqlalchemy import select
from quart_auth import AuthUser, QuartAuth, current_user # type: ignore [reportAssignmentType]

if TYPE_CHECKING:
    base = User
else:
    base = object

class LazyUser(AuthUser, base):
    
    def __init__(self, auth_id: str):
        super().__init__(auth_id)
        self._user: Optional[User] = None
        
        for column in User.__table__.columns.keys():
            
            async def _wrapper(self):
                return await self._get_property(column)
            
            setattr(self, column, property(_wrapper))
            
        
    async def _resolve(self):
       async with db() as session:
           user_query = await session.execute(
               select(User).where(User.id == self.auth_id).limit(1)
           )
           found_user = user_query.scalar_one()
           self._user = found_user       
           
    async def _get_property(self, name: str):
        await self._resolve()
        return getattr(self._user, name)


auth = QuartAuth(user_class=LazyUser)
current_user: LazyUser = current_user

