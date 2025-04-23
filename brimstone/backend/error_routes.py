from quart import Blueprint, render_template
from werkzeug.exceptions import NotFound

errors = Blueprint("errors", __name__)

@errors.app_errorhandler(NotFound)
async def handle_404(exception: NotFound):
    return await render_template("error.html.jinja",
                                 error_name="Page Not Found",
                                 error_description="Unable to locate the desired webpage"
    ), 404
