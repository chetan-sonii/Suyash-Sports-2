# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# -------------------------------------------------
# Base directory & env loader
# -------------------------------------------------
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / ".env")   # auto-load .env file

def env(key, default=None):
    return os.environ.get(key, default)

# -------------------------------------------------
# Config
# -------------------------------------------------
class Config:
    # -------------------------
    # Flask / App
    # -------------------------
    SECRET_KEY = env("SECRET_KEY", "change-me-to-a-secure-value")
    DEBUG = env("FLASK_DEBUG", "0") == "1"
    TESTING = env("FLASK_TESTING", "0") == "1"

    # -------------------------
    # Database (separate values)
    # -------------------------
    DB_ENGINE = env("DB_ENGINE")
    DB_USER = env("DB_USER")
    DB_PASSWORD = env("DB_PASSWORD")
    DB_HOST = env("DB_HOST")
    DB_PORT = env("DB_PORT")
    DB_NAME = env("DB_NAME", )

    SQLALCHEMY_DATABASE_URI = (
        f"{DB_ENGINE}://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMIN_PASSWORD = env("ADMIN_PASSWORD", "admin123")
    MANAGER_PASSWORD = env("MANAGER_PASSWORD", "pass123")
    USER_PASSWORD = env("USER_PASSWORD", "pass123")

    # Config to send reset email link
    # MAIL_SERVER = 'smtp.googlemail.com'
    # MAIL_PORT = 587
    # MAIL_USE_TLS = True
    # MAIL_USERNAME = os.environ.get('EMAIL_USER')
    # MAIL_PASSWORD = os.environ.get('EMAIL_PASS')
