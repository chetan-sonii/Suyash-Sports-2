import sys
from datetime import datetime
from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Event, Venue, Sport, Team, Player, Fixture
from app.utils import save_avatar
from typing import Any, Dict
from werkzeug.security import generate_password_hash
users_bp = Blueprint('users', __name__)


# ==========================================
# 1. MAIN DASHBOARD ROUTING (FIXED)
# ==========================================

@users_bp.route("/dashboard")
@login_required
def profile():
    # EXPLICIT TYPE HINTING: Tell python this dict can hold anything
    context: Dict[str, Any] = {
        'active_page': 'profile',
        'title': 'My Profile'
    }

    # 2. Manager Specific Data
    if current_user.role == 'manager':
        total_events = Event.query.filter_by(manager_id=current_user.id).count()
        active_events = Event.query.filter_by(manager_id=current_user.id, status='live').count()

        context['stats'] = {
            'total_hosted': total_events,
            'active_live': active_events,
            # 'label': 'Tournaments Hosted' (Optional, managed by template now)
        }
        return render_template('users/manager/profile.html', **context)

    # 3. Public User Specific Data
    else:
        joined_count = len(current_user.saved_events)
        context['stats'] = {
            'total_joined': joined_count,
            'label': 'Events Joined'
        }
        return render_template('users/user/user_profile.html', **context)


@users_bp.route("/update_profile", methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        current_user.username = request.form.get('username')
        current_user.email = request.form.get('email')

        if 'avatar' in request.files:
            file = request.files['avatar']
            if file.filename != '':
                picture_file = save_avatar(file)
                current_user.avatar = picture_file

        try:
            db.session.commit()
            flash('Your profile has been updated!', 'success')
        except Exception as e:  # Catch specific errors is better, but generic Exception handles crashes
            flash('Error updating profile. Username or Email might be taken.', 'danger: ', e)

    return redirect(url_for('users.profile'))


# ==========================================
# 2. MANAGER DASHBOARD
# ==========================================
@users_bp.route("/manager/dashboard")
@login_required
def manager_dashboard():
    if current_user.role != 'manager' and current_user.role != 'admin':
        flash('Access Denied: Managers only.', 'danger')
        return redirect(url_for('public.index'))

    my_events = Event.query.filter_by(manager_id=current_user.id).all()

    return render_template('users/manager/manager_dashboard.html',
                           events=my_events,
                           event_count=len(my_events)
                           )


@users_bp.route("/manager/create_event", methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        try:
            data = request.get_json()

            # Validation
            title = data.get('title')
            sport_id = data.get('sport_id')
            start_date_str = data.get('start_date')

            if not title or not sport_id or not start_date_str:
                return jsonify({'status': 'error', 'message': 'Missing required fields.'}), 400

            # Safe Conversions
            venue_id = data.get('venue_id')
            final_venue_id = int(venue_id) if venue_id and str(venue_id).strip() != "" else None

            try:
                final_start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Invalid date format.'}), 400

            # Create Event
            new_event = Event(
                title=title,
                sport_id=int(sport_id),
                manager_id=current_user.id,
                venue_id=final_venue_id,
                start_date=final_start_date,
                description=data.get('description'),
                status='upcoming',
                rules_config={
                    "standard": data.get('standard_rules', {}),
                    "custom": data.get('custom_rules', []),
                    "teams": data.get('team_config', {})
                }
            )

            db.session.add(new_event)
            db.session.commit()

            return jsonify({
                'status': 'success',
                'message': 'Tournament created successfully!',
                'redirect_url': url_for('users.manager_dashboard')
            })

        except Exception as e:
            print(f"🔥 Error: {str(e)}", file=sys.stderr)
            return jsonify({'status': 'error', 'message': str(e)}), 500

    sports = Sport.query.all()
    venues = Venue.query.all()
    return render_template('users/manager/create_event.html',
                           active_page='create_event',
                           sports=sports, venues=venues, title="Create Event")


@users_bp.route("/api/get_sport_config/<int:sport_id>")
@login_required
def get_sport_config(sport_id):
    sport = Sport.query.get_or_404(sport_id)
    return jsonify(sport.config_schema)


# ==========================================
# 3. MANAGE TOURNAMENTS (My Events)
# ==========================================
@users_bp.route("/manager/my_events")
@login_required
def manager_my_events():
    if current_user.role != 'manager':
        return redirect(url_for('public.index'))

    events = Event.query.filter_by(manager_id=current_user.id).order_by(Event.start_date.desc()).all()
    return render_template('users/manager/my_events.html', events=events, active_page='my_events')


@users_bp.route("/manager/event/<int:event_id>/delete", methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.manager_id != current_user.id:
        flash('Unauthorized Action', 'danger')
        return redirect(url_for('users.manager_my_events'))

    db.session.delete(event)
    db.session.commit()
    flash('Tournament deleted.', 'success')
    return redirect(url_for('users.manager_my_events'))


@users_bp.route("/manager/event/<int:event_id>/manage")
@login_required
def manage_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.manager_id != current_user.id:
        flash('Unauthorized Access', 'danger')
        return redirect(url_for('users.manager_my_events'))

    teams = Team.query.filter_by(event_id=event.id).all()
    return render_template('users/manager/manage_event.html',
                           event=event, teams=teams, sport_schema=event.sport.config_schema, title="Manage Events")


# ==========================================
# 4. API ROUTES (SECURED)
# ==========================================

@users_bp.route("/api/event/<int:event_id>/add_team", methods=['POST'])
@login_required
def add_team(event_id):
    # SECURITY FIX: Check ownership
    event = Event.query.get_or_404(event_id)
    if event.manager_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    data = request.form
    new_team = Team(
        event_id=event_id,
        name=data.get('name'),
        city=data.get('city'),
        coach_name=data.get('coach_name')
    )
    db.session.add(new_team)
    db.session.commit()
    return jsonify({'status': 'success', 'team_id': new_team.id})


@users_bp.route("/api/team/<int:team_id>/add_player", methods=['POST'])
@login_required
def add_player(team_id):
    try:
        team = Team.query.get_or_404(team_id)
        # SECURITY FIX: Check event ownership via the team relation
        if team.event.manager_id != current_user.id:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        data = request.get_json()
        name = data.get('name')
        details = {k: v for k, v in data.items() if k != 'name'}

        new_player = Player(team_id=team.id, name=name, details=details)
        db.session.add(new_player)
        db.session.commit()

        return jsonify({'status': 'success', 'message': f'Player {name} added!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@users_bp.route("/api/team/<int:team_id>/get_players")
@login_required
def get_team_players(team_id):
    team = Team.query.get_or_404(team_id)
    # Note: Read access might be okay for non-owners, but strictly:
    if team.event.manager_id != current_user.id:
        return jsonify({'html': '<div class="text-danger">Unauthorized</div>'}), 403

    players = Player.query.filter_by(team_id=team.id).all()
    html = render_template('users/manager/partials/player_list.html', players=players, sport_type=team.event.sport.name,
                           title="Team Players")
    return jsonify({'html': html})


@users_bp.route("/api/event/<int:event_id>/add_fixture", methods=['POST'])
@login_required
def add_fixture(event_id):
    # SECURITY FIX: Check ownership
    event = Event.query.get_or_404(event_id)
    if event.manager_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    try:
        data = request.form
        start_time = datetime.strptime(data.get('start_time'), '%Y-%m-%dT%H:%M')
        team_a_id = data.get('team_a')
        team_b_id = data.get('team_b')

        if event.sport.type == 'team':
            if not team_a_id or not team_b_id:
                return jsonify({'status': 'error', 'message': 'Both teams required'}), 400
            if team_a_id == team_b_id:
                return jsonify({'status': 'error', 'message': 'Cannot play against same team'}), 400

        # LOGIC FIX: Use 'round_name' as the title if provided (e.g. "Semi-Final")
        # Since the database has no 'round_name' column, we recycle the 'title' column.
        match_title = data.get('round_name') if data.get('round_name') else data.get('title')

        new_fixture = Fixture(
            event_id=event.id,
            venue_id=data.get('venue_id') or event.venue_id,
            team_a_id=team_a_id if team_a_id else None,
            team_b_id=team_b_id if team_b_id else None,
            start_time=start_time,
            title=match_title, # <--- Changed this
            # round_name=...  <--- REMOVED THIS LINE causing the error
        )

        db.session.add(new_fixture)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Match scheduled!'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@users_bp.route("/manager/event/<int:event_id>/update_settings", methods=['POST'])
@login_required
def update_event_settings(event_id):
    event = Event.query.get_or_404(event_id)
    # Existing Security Check was correct here
    if event.manager_id != current_user.id:
        return redirect(url_for('users.manager_my_events'))

    event.status = request.form.get('status')
    event.title = request.form.get('title')
    event.description = request.form.get('description')

    db.session.commit()
    flash('Event settings updated.', 'success')
    return redirect(url_for('users.manage_event', event_id=event.id))


@users_bp.route("/change_password", methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not current_user.check_password(current_password):
        flash('Incorrect current password.', 'danger')
        return redirect(url_for('users.profile'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('users.profile'))

    # Update Password
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()

    flash('Password updated successfully!', 'success')
    return redirect(url_for('users.profile'))