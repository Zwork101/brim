from base64 import b64decode, b64encode
import logging
from pathlib import Path
from pickle import dumps, loads
from getpass import getuser
import os

from itsdangerous.url_safe import URLSafeSerializer
from typing import Any, Optional
from jinja2 import Template
from quart import Quart, before_render_template, current_app, render_template, request


class LiveTemplateLogFilter(logging.Filter):
    
    def filter(self, record: logging.LogRecord) -> bool:
        url: str = record.args.get("R")  # type: ignore
        status: str = record.args.get("s")  # type: ignore
        return not (url.startswith("GET /_brim/live/") or status == "204")

class LiveTemplateHTMX:
    
    def __init__(self, app: Optional[Quart] = None):
        self._app = app
        self.serializer: URLSafeSerializer
        self.templates: dict[str, Template] = {}
        
        if self._app is not None:
            self.init_app(self._app)
            
    def init_app(self, app: Quart):
        self._app = app
        self.serializer = URLSafeSerializer(self._app.config['SECRET_KEY'], salt=getuser())
        
        before_render_template.connect_via(app)(self.before_render)
        app.add_url_rule("/_brim/live/<signature>", "_brim_rerender_template", self._brim_rerender_template)
        
        logging.getLogger("hypercorn.access").addFilter(LiveTemplateLogFilter())
        logging.getLogger("quart.serving").addFilter(LiveTemplateLogFilter())
        
    def before_render(self, _: Quart, template: Template, context: dict[str, Any]):
        if "live-off" in request.args:
            return
        
        self.templates[template.filename] = template  # pyright: ignore [reportArgumentType]
        
        required_context = {k: v for k, v in context.items()}
        required_context.pop("g")
        required_context.pop("session")
        required_context.pop("current_user")
        required_context.pop("request")
        context_pickle = b64encode(dumps(required_context)).decode()
        
        signature_payload = {
            "template": template.filename,
            "timestamp": os.path.getmtime(template.filename),  # pyright: ignore [reportArgumentType]
            "variables": context_pickle
        }
        
        signature = self.serializer.dumps(signature_payload)
        context['__brim_template_signature'] = signature
        context['__brim_template_url'] = f"/_brim/live/{signature}"  # pyright: ignore [reportOptionalMemberAccess]
        
    async def _brim_rerender_template(self, signature: str):
        signature_payload = self.serializer.loads(signature)
        
        if signature_payload['timestamp'] != os.path.getmtime(signature_payload['template']):
            variables = loads(b64decode(signature_payload['variables']))
            
            relative_remplate = str(Path(signature_payload['template']).relative_to(Path(current_app.template_folder).resolve()))  # pyright: ignore [reportArgumentType]
            
            return await render_template(relative_remplate, **variables)
        return "", 204


dev_engine = LiveTemplateHTMX()
