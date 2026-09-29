import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY              = os.getenv("SECRET_KEY", "careeriq-secret-dev-2024")
    JWT_SECRET_KEY          = os.getenv("JWT_SECRET_KEY", "careeriq-jwt-dev-2024")
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BCRYPT_LOG_ROUNDS       = 10

    # SendGrid
    SENDGRID_API_KEY    = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@careeriq.com")
    SENDGRID_FROM_NAME  = os.getenv("SENDGRID_FROM_NAME", "CareerIQ")
    APP_BASE_URL        = os.getenv("APP_BASE_URL", "http://localhost:5001")

    # Upload folder
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB for video uploads


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'data', 'careeriq.db')}"
    )


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "")


config = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
}
