from flask import Blueprint, render_template, request, jsonify
from app.models import Event, Team, Sport, Venue

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    # Hero Stats
    stats = {
        'events': Event.query.filter(Event.status != 'completed').count(),
        'teams': Team.query.count(),
        'sports': Sport.query.count()
    }

    # Data for Filters and Cards
    sports = Sport.query.all()
    # Initial load: get 6 upcoming events
    upcoming_events = Event.query.filter_by(status='upcoming').order_by(Event.start_date.asc()).limit(6).all()

    return render_template('public/index.html', stats=stats, sports=sports, events=upcoming_events)


# ==========================================
# AJAX ROUTE (Returns JSON with HTML string)
# ==========================================
@public_bp.route('/api/filter_events', methods=['POST'])
def filter_events():
    sport_id = request.form.get('sport_id')

    # Base Query
    query = Event.query.filter_by(status='upcoming')

    # Apply Filter if not 'all'
    if sport_id and sport_id != 'all':
        query = query.filter_by(sport_id=sport_id)

    events = query.order_by(Event.start_date.asc()).all()

    # Render the partial template to a string
    # FIX: Path is now 'partials/event_cards.html'
    events_html = render_template('partials/event_cards.html', events=events)

    # Return JSON so the page doesn't reload
    return jsonify({'html': events_html})


@public_bp.route('/api/get_event_details', methods=['POST'])
def get_event_details():
    event_id = request.form.get('event_id')
    event = Event.query.get_or_404(event_id)

    # Render the specific content for the modal
    modal_html = render_template('partials/event_details_modal_body.html', event=event)

    return jsonify({'html': modal_html})