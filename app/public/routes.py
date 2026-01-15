from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required,current_user
from app.extensions import db

from app.models import Event, Team, Sport, Venue

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    # Fetch Data for Filters
    stats = {
        'events': Event.query.filter(Event.status != 'completed').count(),
        'active_now': Event.query.filter_by(status='live').count()
    }
    sports = Sport.query.all()
    venues = Venue.query.all()  # For the venue filter

    # Initial load (Recent 6)
    upcoming_events = Event.query.order_by(Event.start_date.desc()).limit(9).all()

    return render_template('public/index.html',
                           stats=stats,
                           sports=sports,
                           venues=venues,
                           events=upcoming_events)


# ==========================================
# 1. ADVANCED FILTER API
# ==========================================
@public_bp.route('/api/filter_events', methods=['POST'])
def filter_events():
    # 1. Get Filter Values
    sport_id = request.form.get('sport_id')
    venue_id = request.form.get('venue_id')
    date_filter = request.form.get('date_filter')  # 'today', 'week', 'month'
    search_query = request.form.get('search')

    # 2. Base Query
    query = Event.query

    # 3. Apply Filters
    if sport_id and sport_id != 'all':
        query = query.filter_by(sport_id=sport_id)

    if venue_id and venue_id != 'all':
        query = query.filter_by(venue_id=venue_id)

    if search_query:
        query = query.filter(Event.title.ilike(f"%{search_query}%"))

    # Date Logic (simplified for example)
    from datetime import datetime, timedelta
    today = datetime.now()
    if date_filter == 'week':
        query = query.filter(Event.start_date <= today + timedelta(days=7))
    elif date_filter == 'month':
        query = query.filter(Event.start_date <= today + timedelta(days=30))

    # Execute
    events = query.order_by(Event.start_date.asc()).all()

    return jsonify({'html': render_template('partials/event_cards.html', events=events)})


@public_bp.route('/api/get_event_details', methods=['POST'])
def get_event_details():
    event_id = request.form.get('event_id')
    event = Event.query.get_or_404(event_id)

    # Render the specific content for the modal
    modal_html = render_template('partials/event_details_modal_body.html', event=event)

    return jsonify({'html': modal_html})


# ==========================================
# 2. SAVE / FOLLOW EVENT API
# ==========================================
@public_bp.route('/api/event/toggle_save', methods=['POST'])
@login_required
def toggle_save_event():
    event_id = request.form.get('event_id')
    event = Event.query.get_or_404(event_id)

    # Check if already saved
    if event in current_user.saved_events:
        current_user.saved_events.remove(event)
        action = 'removed'
    else:
        current_user.saved_events.append(event)
        action = 'saved'

    db.session.commit()
    return jsonify({'status': 'success', 'action': action})