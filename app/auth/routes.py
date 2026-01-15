from urllib.parse import urlparse
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from . import auth_bp
from app.auth.forms import LoginForm, RegisterForm
from app.models import User
from app.extensions import db


def redirect_after_login(user):
    """
    Redirects user based on their specific role.
    """
    if user.role == 'admin':
        return redirect(url_for("admin.dashboard"))
    elif user.role == 'manager':
        # Assuming managers go to a dashboard to create events
        return redirect(url_for("users.manager_dashboard"))
    else:
        # Public users go to homepage
        return redirect(url_for("users.dashboard"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect_after_login(current_user)

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()

        # Check password hash
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash(f"Welcome back, {user.username}!", "success")

            # Handle 'next' parameter safely
            next_page = request.args.get("next")
            if next_page and not urlparse(next_page).netloc:
                return redirect(next_page)

            return redirect_after_login(user)
        else:
            flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect_after_login(current_user)

    form = RegisterForm()

    if form.validate_on_submit():
        # Check if email or username exists
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for("auth.login"))

        if User.query.filter_by(username=form.username.data).first():
            flash("Username already taken.", "warning")
            return redirect(url_for("auth.register"))

        # Create new user
        hashed_password = generate_password_hash(form.password.data)

        new_user = User(
            username=form.username.data,
            email=form.email.data.lower(),
            password_hash=hashed_password,
            role=form.role.data,  # 'manager' or 'public'
            avatar='default.png'
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash("Account created successfully! Welcome aboard.", "success")
        return redirect_after_login(new_user)

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("public.index"))