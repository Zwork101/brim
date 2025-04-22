import logging

from backend.auth import LazyUser, current_user
from backend.db import db, User
from backend.htmx import htmx
from .forms import LoginForm

from quart import Blueprint, redirect, render_template, url_for
from quart_auth import login_user
from sqlalchemy import select
from werkzeug.security import check_password_hash

login = Blueprint("login", __name__)

@login.route("/login")
async def login_page():
    if await current_user.is_authenticated:
        return redirect(
            url_for("home.index")
        )
    
    return await render_template("login/index.html.jinja")

@login.route("/login/login_form", methods=["GET", "POST"])
@htmx.component
async def login_form():
    
    form = await LoginForm.create_form()
        
    invalid_username = False
    invalid_password = False
    
    if await form.validate_on_submit():
        async with db() as session:
            claimed_user = (await session.scalars(
                select(User).where(User.username == form.username.data)
            )).one_or_none()
            
            if claimed_user is None:
                invalid_username = True
            else:
                if check_password_hash(claimed_user.password, form.password.data or ""):
                    login_user(LazyUser(str(claimed_user.id)), form.remember_me.data)
                    return await htmx.redirect(
                        url_for("home.index")
                    )
                else:
                    invalid_password = True
    else:
        logging.debug(f"Unsuccessful login attempt from claimed '{form.username.data}'")
        print(f"Unsuccessful login attempt from claimed '{form.username.data}'")
            
    return await render_template("login/components/login.html.jinja", form=form, invalid_username=invalid_username, invalid_password=invalid_password)
