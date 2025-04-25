from base64 import b64decode, b64encode
import logging
from pathlib import Path
from getpass import getuser
from subprocess import PIPE, Popen
import os
from typing import Any, Optional

from dill import dumps, loads
from itsdangerous.url_safe import URLSafeSerializer
from jinja2 import Template
from pytailwindcss import get_bin_path
from quart import Quart, before_render_template, current_app, g, render_template, request


class LiveTemplateLogFilter(logging.Filter):
    
    def filter(self, record: logging.LogRecord) -> bool:
        url: str = record.args.get("R")  # type: ignore
        status: str = record.args.get("s")  # type: ignore
        return not (url.startswith("GET /_brim/live/") or status == "204")


class LiveTemplateHTMX:
    
    def __init__(self, app: Optional[Quart] = None):
        self._app = app
        self.serializer: URLSafeSerializer
        self.tailwind_process: Popen
        self.templates: dict[str, list[Template]] = {}
        
        if self._app is not None:
            self.init_app(self._app)
            
    def init_app(self, app: Quart):
        self._app = app
        self.serializer = URLSafeSerializer(self._app.config['SECRET_KEY'], salt=getuser())
        
        before_render_template.connect_via(app)(self.before_render)
        app.add_url_rule("/_brim/live/<signature>", "_brim_rerender_template", self._brim_rerender_template)
        
        logging.getLogger("hypercorn.access").addFilter(LiveTemplateLogFilter())
        logging.getLogger("quart.serving").addFilter(LiveTemplateLogFilter())
        
        self.start_tailwind_task(app)
        
    def before_render(self, _: Quart, template: Template, context: dict[str, Any]):
        if "live-off" in request.args:
            return
        
        primary_template = g.get('_BRIM_PRIMARY_TEMPLATE')
        
        if primary_template is None:
            self.templates[template.filename] = [template]  # pyright: ignore [reportArgumentType]
            g._BRIM_PRIMARY_TEMPLATE = template
        else:
            self.templates[primary_template.filename].append(template)
        
        file_timestamp = os.path.getmtime(template.filename)  # pyright: ignore [reportArgumentType]
        
        if file_timestamp > g.get("_brim_template_timestamp", 0):
            if template == g._BRIM_PRIMARY_TEMPLATE:
                required_context = {k: v for k, v in context.items()}
                required_context.pop("g")
                required_context.pop("session")
                required_context.pop("current_user")
                required_context.pop("request")
                context_pickle = b64encode(dumps(required_context)).decode()
                
                signature_payload = {
                    "template": template.filename,
                    "timestamp": file_timestamp,  
                    "variables": context_pickle
                } 
            else:
                signature_payload = self.serializer.loads(g._brim_template_signature)
                signature_payload['timestamp'] = file_timestamp
            
            signature = self.serializer.dumps(signature_payload)
            g._brim_template_signature = signature
            g._brim_template_timestamp = file_timestamp
            g._brim_template_url = f"/_brim/live/{signature}"  # pyright: ignore [reportOptionalMemberAccess]
        
    def create_tailwind_args(self, app: Quart, no_minify: bool = False, no_optimize: bool = False, watch: bool = False):
        return (['--input', str(Path(app.static_folder).parent.joinpath(Path("_src/input.css")))] + # pyright: ignore [reportArgumentType]
                ['--output', str(Path(app.static_folder).joinpath("css/output.css"))] + # pyright: ignore [reportArgumentType]
                (['--minify'] if not no_minify else []) +
                (['--optimize'] if not no_optimize else []) +
                ['--cwd', str(Path(app.template_folder).resolve())] +  # pyright: ignore [reportArgumentType]
                (['--watch'] if watch else [])
        )
        
    def start_tailwind_task(self, app: Quart):
        version = app.config.get("TAILWIND_VERSION", "latest")
        tailwind_bin = get_bin_path(
            version
        )
        
        if tailwind_bin is None:
            raise NotImplementedError(f"Tailwind version '{version}' not installed. Run `quart tailwind install --version {version}` to install it.")
                
        self.tailwind_process = Popen([str(tailwind_bin)] + self.create_tailwind_args(
            app,
            no_minify=not app.config.get('TAILWIND_MINIFY', True),
            no_optimize=not app.config.get('TAILWIND_OPTIMIZE', True),
            watch=True
        ), stdout=PIPE, stderr=PIPE)
        
        
    async def _brim_rerender_template(self, signature: str):
        signature_payload = self.serializer.loads(signature)
        template_modify_times = tuple(os.path.getmtime(t.filename) for t in self.templates[signature_payload['template']])  # pyright: ignore [reportArgumentType]
        
        if signature_payload['timestamp'] < max(template_modify_times):
            variables = loads(b64decode(signature_payload['variables']))
            
            relative_remplate = str(Path(signature_payload['template']).relative_to(Path(current_app.template_folder).resolve()).as_posix())  # pyright: ignore [reportArgumentType]
            
            return await render_template(relative_remplate, **variables)
        return "", 204


dev_engine = LiveTemplateHTMX()
