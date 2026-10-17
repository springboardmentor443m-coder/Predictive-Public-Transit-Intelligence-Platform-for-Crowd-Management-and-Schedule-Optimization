import logging
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
import app.db.base  # Ensure all models are imported before Base.metadata.create_all
from app.models.user import User, UserRole
from app.services.user_service import UserService
from app.schemas.user import UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("metroflow.init_db")


def init_db(db: Session) -> None:
    # Create all database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized.")

    # Check if initial admin account exists
    admin_user = UserService.get_by_email(db, settings.INITIAL_ADMIN_EMAIL)
    if not admin_user:
        logger.info(f"Creating initial system ADMIN account: {settings.INITIAL_ADMIN_EMAIL}")
        user_in = UserCreate(
            email=settings.INITIAL_ADMIN_EMAIL,
            name=settings.INITIAL_ADMIN_NAME,
            password=settings.INITIAL_ADMIN_PASSWORD,
            role=UserRole.ADMIN,
            is_active=True
        )
        admin_user = UserService.create(db, user_in=user_in)
        logger.info(f"Initial ADMIN user created successfully with ID {admin_user.id}.")
    else:
        logger.info(f"Initial ADMIN user ({settings.INITIAL_ADMIN_EMAIL}) already exists.")


def main() -> None:
    logger.info("Initializing database schema and seed data...")
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    logger.info("Database initialization finished successfully.")


if __name__ == "__main__":
    main()
