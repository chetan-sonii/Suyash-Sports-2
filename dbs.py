import random
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models import User, Sport, Venue, Event, Team, Player, Fixture

# Initialize App
app = create_app()


def seed_data():
    with app.app_context():
        print("🗑️  Cleaning old data...")
        db.drop_all()
        db.create_all()

        # ==========================================
        # 1. CREATE USERS
        # ==========================================
        print("👤 Creating Users...")
        admin = User(username='admin', email='admin@sports.com', password_hash=generate_password_hash('admin123'),
                     role='admin')
        manager1 = User(username='john_doe', email='john@sports.com',
                        password_hash=generate_password_hash('manager123'), role='manager')
        manager2 = User(username='sarah_smith', email='sarah@sports.com',
                        password_hash=generate_password_hash('manager123'), role='manager')

        db.session.add_all([admin, manager1, manager2])
        db.session.commit()

        # ==========================================
        # 2. CREATE VENUES
        # ==========================================
        print("🏟️  Creating Venues...")
        venues = [
            Venue(name="National Stadium", city="Delhi", address="Gate 4, Stadium Road"),
            Venue(name="City Sports Complex", city="Mumbai", address="Downtown Avenue"),
            Venue(name="Green Field Arena", city="Bangalore", address="Tech Park Side"),
            Venue(name="Iron Gym Hall", city="Pune", address="Fit Street")
        ]
        db.session.add_all(venues)
        db.session.commit()

        # ==========================================
        # 3. CREATE SPORTS (With JSON Schemas)
        # ==========================================
        print("🏆 Defining Sports Configuration...")

        sports_data = [
            {
                "name": "Cricket",
                "type": "team",
                "config_schema": {
                    "roles": ["Batsman", "Bowler", "All-Rounder", "Wicketkeeper"],
                    "stat_fields": ["matches", "runs", "wickets", "batting_avg"],
                    "scoring_unit": "runs/wickets"
                }
            },
            {
                "name": "Football",
                "type": "team",
                "config_schema": {
                    "roles": ["Forward", "Midfielder", "Defender", "Goalkeeper"],
                    "stat_fields": ["matches", "goals", "assists", "clean_sheets"],
                    "scoring_unit": "goals"
                }
            },
            {
                "name": "Kabaddi",
                "type": "team",
                "config_schema": {
                    "roles": ["Raider", "Defender", "All-Rounder"],
                    "stat_fields": ["matches", "raid_points", "tackle_points"],
                    "scoring_unit": "points"
                }
            },
            {
                "name": "Weightlifting",
                "type": "individual",
                "config_schema": {
                    "roles": ["Lifter"],
                    "categories": ["55kg", "61kg", "73kg", "89kg", "102kg", "+102kg"],
                    "stat_fields": ["snatch_pb", "jerk_pb", "total"],
                    "scoring_unit": "kg"
                }
            }
        ]

        sports_objs = {}
        for s in sports_data:
            sport = Sport(name=s['name'], type=s['type'], config_schema=s['config_schema'])
            db.session.add(sport)
            sports_objs[s['name']] = sport

        db.session.commit()

        # ==========================================
        # 4. CREATE EVENTS, TEAMS & PLAYERS
        # ==========================================
        print("📅 Scheduling Events & Drafting Players...")

        # --- Helper Data ---
        team_prefixes = ["Royal", "Super", "Mighty", "City", "United", "Golden"]
        team_suffixes = ["Warriors", "Kings", "Lions", "Strikers", "Panthers", "Eagles"]
        names_first = ["Rahul", "Amit", "Suresh", "David", "Virat", "Lionel", "Cristiano", "Pardeep", "Mirabai"]
        names_last = ["Sharma", "Kohli", "Singh", "Beckham", "Messi", "Ronaldo", "Narwal", "Chanu"]

        for sport_name, sport_obj in sports_objs.items():

            # 1. Create Event
            # Fix: Use datetime.now(timezone.utc)
            event = Event(
                sport_id=sport_obj.id,
                manager_id=manager1.id,
                title=f"Annual {sport_name} Championship 2026",
                start_date=datetime.now(timezone.utc) + timedelta(days=10),
                end_date=datetime.now(timezone.utc) + timedelta(days=20),
                status="upcoming",
                rules_config={"format": "Standard", "max_teams": 8}
            )
            db.session.add(event)
            db.session.commit()  # Commit to get event ID

            # 2. Create Teams
            teams = []
            for i in range(4):
                t_name = f"{random.choice(team_prefixes)} {random.choice(team_suffixes)} {random.randint(1, 99)}"
                team = Team(event_id=event.id, name=t_name, city="Raipur", coach_name="Coach X")
                db.session.add(team)
                teams.append(team)
            db.session.commit()  # Commit to get Team IDs

            # 3. Add Players to Teams
            for team in teams:
                for j in range(5):
                    p_name = f"{random.choice(names_first)} {random.choice(names_last)}"

                    # Custom JSON Data
                    details_json = {}
                    if sport_name == "Cricket":
                        details_json = {"role": random.choice(["Batsman", "Bowler"]), "batting_style": "Right-hand"}
                    elif sport_name == "Football":
                        details_json = {"position": random.choice(["Forward", "Defender"]),
                                        "jersey_no": random.randint(1, 20)}
                    elif sport_name == "Kabaddi":
                        details_json = {"position": "Raider", "weight_kg": random.randint(70, 90)}
                    elif sport_name == "Weightlifting":
                        details_json = {"weight_class": random.choice(["73kg", "89kg"]), "snatch_pb": 100}

                    # FIX: Removed 'event_id=event.id' because Players are linked to Teams, not Events directly
                    player = Player(
                        team_id=team.id,
                        name=p_name,
                        details=details_json
                    )
                    db.session.add(player)

            # 4. Create Fixtures (Matches)
            if len(teams) >= 2:
                match = Fixture(
                    event_id=event.id,
                    venue_id=venues[0].id,
                    team_a_id=teams[0].id,
                    team_b_id=teams[1].id,
                    start_time=datetime.now(timezone.utc) + timedelta(days=12),
                    title=f"Group Stage Match 1"
                )
                db.session.add(match)

        db.session.commit()
        print("✅ Database Seeded Successfully!")


if __name__ == "__main__":
    seed_data()