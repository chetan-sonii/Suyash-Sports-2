# app/admin/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, abort,session
from flask_login import login_required, current_user



admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder="templates"
)

@admin_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("admin/dashboard.html", title="Dashboard")
