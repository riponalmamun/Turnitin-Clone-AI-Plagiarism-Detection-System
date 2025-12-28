from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class
Base = declarative_base()


def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    # CRITICAL: Import ALL models here so SQLAlchemy registers them
    # Import order matters - import Institution first since others reference it
    import app.models.institution  # noqa
    import app.models.user  # noqa
    import app.models.document  # noqa
    import app.models.submission  # noqa
    import app.models.match  # noqa
    import app.models.report  # noqa
    
    # Now create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")