import random
from datetime import datetime, timedelta
from faker import Faker
from app import create_app, db
from app.models import User, Sport, Venue, Event, Team, Player, Fixture
import sqlalchemy
from config import Config

# Initialize Faker
fake = Faker('en_IN')

# Configuration
TOTAL_USERS = 20
TOTAL_MANAGERS = 5
TOTAL_VENUES = 10
EVENTS_PER_MANAGER = 2


def create_database():
    """Creates the database using credentials from config.py"""
    print("Checking database...")

    # Build URI from Config
    db_uri = f"{Config.DB_ENGINE}://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}"

    engine = sqlalchemy.create_engine(db_uri)
    conn = engine.connect()

    db_name = Config.DB_NAME
    try:
        conn.execute(sqlalchemy.text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))
        print(f"✅ Database '{db_name}' is ready.")
    except Exception as e:
        print(f"❌ Error creating database: {e}")
    finally:
        conn.close()


def seed_data():
    app = create_app()
    with app.app_context():
        # 1. WIPE EVERYTHING CLEAN
        print("🗑️  Dropping old tables...")
        db.drop_all()
        print("🔨 Creating new tables...")
        db.create_all()

        # 2. SPORTS
        print("🏆 Seeding Sports...")
        sports_data = [
            {'name': 'Cricket', 'type': 'team',
             'config_schema': {"roles": ["Batsman", "Bowler", "Wicketkeeper"], "scoring_unit": "runs"}},
            {'name': 'Football', 'type': 'team',
             'config_schema': {"roles": ["Striker", "Midfielder", "Defender", "Goalie"], "scoring_unit": "goals"}},
            {'name': 'Kabaddi', 'type': 'team',
             'config_schema': {"roles": ["Raider", "Defender"], "scoring_unit": "points"}},
            {'name': 'Badminton', 'type': 'individual',
             'config_schema': {"roles": ["Single", "Double"], "scoring_unit": "sets"}}
        ]

        db_sports = []
        for s in sports_data:
            sport = Sport(name=s['name'], type=s['type'], config_schema=s['config_schema'])
            db.session.add(sport)
            db_sports.append(sport)
        db.session.commit()

        # 3. USERS (Admin, Managers, Public)
        print("busts Seeding Users...")

        # --- A. ADMIN ---
        admin = User(username='admin', email='admin@suyash.com', role='admin')
        admin.set_password(Config.ADMIN_PASSWORD)
        db.session.add(admin)

        # --- B. MANAGERS ---
        managers = []

        # Specific Manager
        suyash_mgr = User(username='suyashmanager', email='suyashmanager@gmail.com', role='manager')
        suyash_mgr.set_password(Config.MANAGER_PASSWORD)
        db.session.add(suyash_mgr)
        managers.append(suyash_mgr)

        # Random Managers
        for _ in range(TOTAL_MANAGERS - 1):
            mgr = User(username=fake.first_name(), email=fake.unique.email(), role='manager')
            mgr.set_password(Config.MANAGER_PASSWORD)
            db.session.add(mgr)
            managers.append(mgr)

        # --- C. PUBLIC USERS ---
        public_users = []

        # Specific User
        suyash_user = User(username='suyashuser', email='suyashuser@gmail.com', role='user')
        suyash_user.set_password(Config.USER_PASSWORD)
        db.session.add(suyash_user)
        public_users.append(suyash_user)

        # Random Users
        for _ in range(TOTAL_USERS - 1):
            usr = User(username=fake.user_name(), email=fake.unique.email(), role='user')
            usr.set_password(Config.USER_PASSWORD)
            db.session.add(usr)
            public_users.append(usr)

        db.session.commit()

        # 4. VENUES
        print("🏟️  Seeding Venues...")
        venues = []
        cities = ['Mumbai', 'Delhi', 'Raipur', 'Bangalore', 'Chennai', 'Pune', 'Jaipur', 'Hyderabad']
        for _ in range(TOTAL_VENUES):
            city = random.choice(cities)
            v_name = f"{fake.company()} Stadium"
            venue = Venue(name=v_name, city=city, address=fake.address())
            db.session.add(venue)
            venues.append(venue)
        db.session.commit()

        # 5. EVENTS
        print("📅 Seeding Events...")
        events = []
        for mgr in managers:
            for _ in range(EVENTS_PER_MANAGER):
                sport = random.choice(db_sports)
                start_date = fake.date_between(start_date='-2m', end_date='+2m')

                today = datetime.now().date()
                if start_date < today:
                    status = 'completed'
                elif start_date == today:
                    status = 'live'
                else:
                    status = 'upcoming'

                event = Event(
                    title=f"{fake.city()} {sport.name} Cup {start_date.year}",
                    sport_id=sport.id, manager_id=mgr.id, venue_id=random.choice(venues).id,
                    start_date=start_date, description=fake.paragraph(nb_sentences=2),
                    status=status, rules_config={"standard": {"overs": 20}, "custom": []}
                )
                db.session.add(event)
                events.append(event)
        db.session.commit()

        # 6. TEAMS & PLAYERS
        print("👕 Seeding Teams & Players...")
        for event in events:
            if event.sport.type == 'team':
                teams_in_event = []
                for _ in range(random.randint(4, 6)):
                    t_name = f"{fake.city()} {random.choice(['Lions', 'Tigers', 'Royals', 'Stars'])}"
                    team = Team(event_id=event.id, name=t_name, city=event.venue.city, coach_name=fake.name())
                    db.session.add(team)
                    teams_in_event.append(team)
                db.session.commit()

                for team in teams_in_event:
                    roles = event.sport.config_schema.get('roles', ['Player'])
                    for _ in range(12):
                        p = Player(team_id=team.id, name=fake.name_male(), details={"role": random.choice(roles)})
                        db.session.add(p)

            # 7. FIXTURES
            if event.sport.type == 'team' and len(teams_in_event) >= 2:
                for _ in range(3):
                    t1, t2 = random.sample(teams_in_event, 2)
                    match_time = datetime.combine(event.start_date, datetime.min.time()) + timedelta(
                        days=random.randint(0, 5), hours=random.randint(10, 20))

                    fixture = Fixture(
                        event_id=event.id, venue_id=event.venue_id,
                        team_a_id=t1.id, team_b_id=t2.id,
                        start_time=match_time, title=f"{t1.name} vs {t2.name}",
                        score_data={}
                    )
                    db.session.add(fixture)

            # 8. SAVED EVENTS
            for user in public_users:
                if random.random() > 0.8:
                    user.saved_events.append(event)

        db.session.commit()

        print("\n✨ SUCCESS! Database seeded.")
        print(f"   - Specific Manager: suyashmanager@gmail.com")
        print(f"   - Specific User: suyashuser@gmail.com")
        print(f"   - Total Managers: {len(managers)}")
        print(f"   - Total Users: {len(public_users)}")


def seed_weightlifting():
    """
    Adds Weightlifting sport and its specific weight categories.
    """
    print("🏋️ Seeding Weightlifting...")

    # 1. Create the Sport
    weightlifting = Sport.query.filter_by(name="Weightlifting").first()
    if not weightlifting:
        weightlifting = Sport(
            name="Weightlifting",
            type="Individual",  # It's an individual sport
            description="Olympic weightlifting consisting of Snatch and Clean & Jerk."
        )
        db.session.add(weightlifting)
        db.session.commit()

    # 2. Define Standard Weight Categories (Olympic Classes)
    # You can adjust these based on your college/tournament rules
    categories = [
        # Men's Categories
        "Men's 55kg", "Men's 61kg", "Men's 67kg", "Men's 73kg",
        "Men's 81kg", "Men's 89kg", "Men's 96kg", "Men's 102kg",
        "Men's 109kg", "Men's +109kg",

        # Women's Categories
        "Women's 45kg", "Women's 49kg", "Women's 55kg", "Women's 59kg",
        "Women's 64kg", "Women's 71kg", "Women's 76kg", "Women's 81kg",
        "Women's 87kg", "Women's +87kg"
    ]

    # 3. Create Events for each Category
    for cat_name in categories:
        exists = Event.query.filter_by(name=cat_name, sport_id=weightlifting.id).first()
        if not exists:
            event = Event(
                name=cat_name,
                sport_id=weightlifting.id,
                # If you have a column for max_participants or gender, add it here
                # gender = 'Male' if "Men" in cat_name else 'Female'
            )
            db.session.add(event)

    db.session.commit()
    print("✅ Weightlifting and Categories seeded successfully.")
if __name__ == '__main__':
    create_database()
    seed_weightlifting()
    seed_data()