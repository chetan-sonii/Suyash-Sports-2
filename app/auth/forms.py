from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, Regexp, EqualTo


class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Length(min=3, max=25),
            Regexp(r'^[A-Za-z0-9_]+$', message="Letters, numbers, and underscores only.")
        ]
    )

    email = StringField('Email Address', validators=[DataRequired(), Email()])

    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters.")]
    )

    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match.')]
    )

    # Allow users to choose if they are a Viewer or a Manager
    role = SelectField(
        'I want to...',
        choices=[('public', 'Join/View Events'), ('manager', 'Organize Events')],
        default='public'
    )

    submit = SubmitField('Create Account')