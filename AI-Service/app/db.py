from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL - using SQLite for simplicity
DATABASE_URL = "sqlite:///./data/app.db"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

def init_db():
    """Initialize database tables"""
    # Import all models here to ensure they are registered with Base
    from app.models.database_models import User, GlucoseLog, FoodLog, ExerciseLog
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create default user if not exists
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.id == 1).first()
        if not existing_user:
            default_user = User(id=1, age=30)  # Default age 30
            db.add(default_user)
            db.commit()
            print("Default user created with ID 1")
    except Exception as e:
        print(f"Error creating default user: {e}")
        db.rollback()
    finally:
        db.close()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


