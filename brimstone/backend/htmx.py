from functools import wraps
from types import CoroutineType
from typing import Any, Callable, Optional
import sys

from markupsafe import Markup
from quart import Quart, make_response


class HTMX:
    
    def __init__(self, app: Optional[Quart] = None):
        if app is not None:
            self.init_app(app)
            
        self._components = {}
            
    def init_app(self, app: Quart):
        for component_name, component_method in self._components.items():
            app.jinja_env.globals[component_name] = component_method
    
    @classmethod
    async def redirect(cls, location: str):
        resp = await make_response("")
        resp.headers["HX-Redirect"] = location
        return resp
    
    def component(self, route: "Callable[..., CoroutineType[Any, Any, Any]]") -> "Callable[..., CoroutineType[Any, Any, Any]]":
        @wraps(route)
        async def mark_safe(*args, **kwargs):
            result = await route(*args, **kwargs)
            if isinstance(result, str):
                return Markup(result)
            return result
        
        component_jinja_name = 'htmx_' + route.__name__
        
        if component_jinja_name in self._components:
            existing_func_module = sys.modules[self._components[component_jinja_name].__module__]
            current_func_module = sys.modules[route.__module__]
            raise KeyError(f"Matching component name in {existing_func_module.__name__} and {current_func_module.__name__} for component '{route.__name__}'")
        
        self._components[component_jinja_name] = mark_safe
        return route

htmx = HTMX()
