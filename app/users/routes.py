import os
from datetime import datetime

from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Event, Venue, Sport
from app.utils import save_avatar  # Import the helper

users_bp = Blueprint('users', __name__)


@users_bp.route("/dashboard")
@login_required
def dashboard():
    # If user is admin/manager, you might want to redirect them 
    # OR let them see this profile page as their "Personal Settings"
    # For now, this is the generic user profile.
    return render_template('users/profile.html', title='My Profile')


@users_bp.route("/update_profile", methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        # 1. Update Text Data
        current_user.username = request.form.get('username')
        current_user.email = request.form.get('email')

        # 2. Update Avatar if provided
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file.filename != '':
                # Delete old avatar if it's not default (Optional cleanup)
                # if current_user.avatar != 'default.png':
                #    os.remove(...) 

                picture_file = save_avatar(file)
                current_user.avatar = picture_file

        try:
            db.session.commit()
            flash('Your profile has been updated!', 'success')
        except:
            flash('Error updating profile. Username or Email might be taken.', 'danger')

    return redirect(url_for('users.dashboard'))


@users_bp.route("/manager/dashboard")
@login_required
def manager_dashboard():
    # Security Check: Ensure only managers can access
    if current_user.role != 'manager' and current_user.role != 'admin':
        flash('Access Denied: Managers only.', 'danger')
        return redirect(url_for('public.index'))

    # Fetch Data for the Overview Tab
    # 1. Total Events Created by this manager
    my_events = Event.query.filter_by(manager_id=current_user.id).all()

    # 2. Total Participants in his events
    total_participants = 0
    for event in my_events:
        # Assuming we have a way to count participants (players) via teams
        # total_participants += len(event.teams) * avg_players... (Simplification for now)
        pass

    return render_template('users/manager_dashboard.html',
                           events=my_events,
                           event_count=len(my_events))


# 1. The Page Route
@users_bp.route("/manager/create_event", methods=['GET', 'POST'])
@login_required
def create_event():
    if current_user.role != 'manager':
        flash('Access Denied', 'danger')
        return redirect(url_for('public.index'))

    if request.method == 'POST':
        # This handles the Final Submit
        try:
            # Basic Info
            title = request.form.get('title')
            sport_id = request.form.get('sport_id')
            venue_id = request.form.get('venue_id')  # Assuming you have a Venue dropdown or logic
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')

            # Dynamic JSON Rules (Collected from Step 2)
            # We iterate through form keys to find 'rule_' prefixed items
            rules_config = {}
            for key in request.form:
                if key.startswith('rule_'):
                    clean_key = key.replace('rule_', '')
                    rules_config[clean_key] = request.form.get(key)

            new_event = Event(
                title=title,
                sport_id=sport_id,
                manager_id=current_user.id,
                venue_id=venue_id if venue_id else None,
                start_date=start_date,
                status='upcoming',
                rules_config=rules_config
            )

            db.session.add(new_event)
            db.session.commit()

            flash('Event created successfully! Now add teams.', 'success')
            return redirect(url_for('users.manager_dashboard'))

        except Exception as e:
            flash(f'Error creating event: {str(e)}', 'danger')

    # GET Request: Show the form
    sports = Sport.query.all()
    venues = Venue.query.all()
    return render_template('users/manager/create_event.html',
                           active_page='create_event',
                           sports=sports,
                           venues=venues)


# 2. The AJAX Route (To get rules for a specific sport)
@users_bp.route("/api/get_sport_config/<int:sport_id>")
@login_required
def get_sport_config(sport_id):
    sport = Sport.query.get_or_404(sport_id)
    # Returns the JSON schema (e.g., {"roles": [...], "stat_fields": [...]})
    return jsonify(sport.config_schema)