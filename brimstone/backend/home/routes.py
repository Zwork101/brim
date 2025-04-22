import time
import sys

from quart_auth import current_user

from backend.htmx import htmx

from quart import Blueprint, current_app, render_template

home = Blueprint("home", __name__)

@home.route("/")
async def index():
    return await render_template("index.html.jinja")


@home.route("/stats")
@htmx.component
async def stats():
    python_version = sys.implementation.name = ' ' + \
        f'{sys.implementation.version.major}.{sys.implementation.version.minor}.{sys.implementation.version.micro}'
    uptime = f"{(time.perf_counter() - current_app.config['BRIM_START_TIME']):.4f}"
    return await render_template("components/update.html.jinja", python_version=python_version, uptime=uptime)
