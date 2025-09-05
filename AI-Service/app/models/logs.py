from sqlalchemy import Column, Integer, String, DateTime, Text, Float, TIMESTAMP
from sqlalchemy.sql import func
from app.db import Base


class GlucoseLog(Base):
    __tablename__ = "glucose"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    glucose_mg_dl = Column(Float, nullable=False)
    time = Column(String(8), nullable=True)  # HH:MM format
    date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class FoodLog(Base):
    __tablename__ = "food"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(20), nullable=False)  # 아침, 점심, 저녁, 간식, 야식 등
    carbs = Column(Float, nullable=True)
    calories = Column(Float, nullable=True)
    time = Column(String(8), nullable=True)  # HH:MM format
    date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class ExerciseLog(Base):
    __tablename__ = "exercise"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    exercise_name = Column(String(100), nullable=False)  # 운동 종류(이름)
    exercise_duration = Column(Integer, nullable=True)  # 운동 시간(분)
    exercise_date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
