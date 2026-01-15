from flask_login import UserMixin
from sqlalchemy.dialects.mysql import JSON
from app.extensions import db


registrations = db.Table('registrations',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True)
)


# ==========================================
# 1. USERS & ROLES
# ==========================================
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='public')  # 'admin', 'manager', 'public'
    avatar = db.Column(db.String(20), default='default.png')
    events = db.relationship('Event', backref='manager', lazy=True)

    # Relationship to access saved events
    saved_events = db.relationship('Event', secondary=registrations, lazy='subquery',
                                   backref=db.backref('participants_users', lazy=True))

    @property
    def avatar_url(self):
        """Helper to return full path for templates"""
        return f"images/uploads/avatars/{self.avatar}"
# ==========================================
# 2. MASTER DATA (The 4 Sports Definition)
# ==========================================
class Sport(db.Model):
    __tablename__ = 'sports'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)  # "Cricket", "Football", "Kabaddi", "Weightlifting"
    type = db.Column(db.String(20))  # 'team' or 'individual'

    # JSON RULEBOOK: Defines what fields are visible in the frontend
    # Cricket: { "roles": ["Batsman", "Bowler"], "stat_fields": ["runs", "wickets"] }
    # Lifting: { "roles": ["Lifter"], "stat_fields": ["snatch", "jerk", "total"] }
    config_schema = db.Column(JSON, nullable=False)

    events = db.relationship('Event', backref='sport', lazy=True)


class Venue(db.Model):
    __tablename__ = 'venues'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200))


# ==========================================
# 3. TOURNAMENTS / EVENTS
# ==========================================
class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    sport_id = db.Column(db.Integer, db.ForeignKey('sports.id'), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    title = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='upcoming')

    # Foreign Key
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=True)

    # JSON Settings
    rules_config = db.Column(JSON, nullable=True)

    # === ADD THIS RELATIONSHIP ===
    venue = db.relationship('Venue', backref='event_list', lazy=True)
    # =============================

    teams = db.relationship('Team', backref='event', lazy=True)
    fixtures = db.relationship('Fixture', backref='event', lazy=True)


# ==========================================
# 4. TEAMS & PLAYERS
# ==========================================
class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)

    name = db.Column(db.String(100), nullable=False)  # "Mumbai Indians" or "Gold Gym Lifters"
    city = db.Column(db.String(50))
    coach_name = db.Column(db.String(100))

    # Captain logic: We store the player_id of the captain here
    captain_id = db.Column(db.Integer, nullable=True)

    players = db.relationship('Player', backref='team', lazy=True)


class Player(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    # DYNAMIC PLAYER DETAILS (This solves your specific problem)
    # Cricket: { "role": "Wicketkeeper", "batting_style": "Right" }
    # Football: { "position": "Midfielder", "jersey_no": 10 }
    # Kabaddi: { "position": "Raider", "weight": 78 }
    # Weightlifting: { "weight_class": "96kg", "entry_total": 200 }
    details = db.Column(JSON, nullable=True)


# ==========================================
# 5. MATCHES / FIXTURES (The Polymorphic Part)
# ==========================================
class Fixture(db.Model):
    __tablename__ = 'fixtures'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=True)

    start_time = db.Column(db.DateTime, nullable=False)

    # --- LOGIC FOR TEAM SPORTS (Cricket, Football, Kabaddi) ---
    team_a_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    team_b_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)

    # --- LOGIC FOR INDIVIDUAL SPORTS (Weightlifting) ---
    # Weightlifting matches are "Sessions" (e.g., "Men's 85kg Group A")
    # We leave team_a/team_b NULL and use the title.
    title = db.Column(db.String(100))  # e.g. "Final Match" or "Session 1"

    # DYNAMIC SCORECARD
    # Cricket: { "team_a_runs": 200, "team_b_runs": 150, "overs": 20 }
    # Football: { "team_a_goals": 2, "team_b_goals": 1 }
    # Weightlifting: { "results": [ { "player_id": 5, "snatch": 100, "jerk": 130 } ] }
    score_data = db.Column(JSON, nullable=True)