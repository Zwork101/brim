from quart_wtf import QuartForm
from wtforms import BooleanField, EmailField, HiddenField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

def username_factory(**kwargs):
    return StringField(
        "Username", 
        validators=[DataRequired(), Length(max=32)], 
        render_kw={"autocomplete": "username"},
        **kwargs
    )

def password_factory(label: str = "Password", **kwargs):
    validators = [DataRequired(), Length(min=8, max=64)]
    validators += kwargs.get('validators', [])
    kwargs['validators'] = validators
    return PasswordField(
        label, 
        render_kw={"autocomplete": "password"},
        **kwargs
    )


class LoginForm(QuartForm):
    username = username_factory()
    password = password_factory()
    remember_me = BooleanField("Remember Me")
    
    
class SendResetForm(QuartForm):
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=320)])
    

class ResetPasswordForm(QuartForm):
    reset_token = HiddenField()
    password = password_factory()
    confirm_password = password_factory("Confirm Password", validators=[
        EqualTo("password", message="Passwords must match.")
    ])
    
