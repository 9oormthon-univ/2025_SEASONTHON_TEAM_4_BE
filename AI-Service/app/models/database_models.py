"""데이터베이스 모델 정의"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, Date, Time
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Member(Base):
    """회원 모델"""
    __tablename__ = "member"
    
    member_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(255), nullable=False)
    birth = Column(Date)
    gender = Column(String(10))
    height = Column(Float)
    weight = Column(Float)
    diabetes_type = Column(String(20))
    sensor = Column(String(50))
    code = Column(String(20))
    status = Column(String(20), default="active")
    inactive_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Glucose(Base):
    """혈당 모델"""
    __tablename__ = "glucose"
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, nullable=False, index=True)
    glucose_mg_dl = Column(Float, nullable=False)
    time = Column(String(8), nullable=False)  # varchar(8) in database
    date = Column(String(10), nullable=False, index=True)  # varchar(10) in database
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Food(Base):
    """음식 모델"""
    __tablename__ = "food"
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, nullable=False, index=True)
    food_name = Column(String(100), nullable=False)
    calories = Column(Float)
    carbs = Column(Float)
    protein = Column(Float)
    fat = Column(Float)
    fiber = Column(Float)
    sugar = Column(Float)
    meal_type = Column(String(20))  # breakfast, lunch, dinner, snack
    date = Column(String(10), nullable=False, index=True)  # varchar(10) in database
    time = Column(String(8), nullable=False)  # varchar(8) in database
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Exercise(Base):
    """운동 모델"""
    __tablename__ = "exercise"
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, nullable=False, index=True)
    exercise_type = Column(String(50), nullable=False)
    duration_minutes = Column(Integer)
    intensity = Column(String(20))  # low, medium, high
    calories_burned = Column(Float)
    date = Column(String(10), nullable=False, index=True)  # varchar(10) in database
    time = Column(String(8), nullable=False)  # varchar(8) in database
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Quest(Base):
    """퀘스트 모델"""
    __tablename__ = "quest"
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, nullable=False, index=True)
    quest_type = Column(String(50), nullable=False)
    quest_title = Column(String(200), nullable=False)
    quest_content = Column(Text)
    quest_date = Column(String(10), nullable=False, index=True)  # varchar(10) in database
    is_completed = Column(Boolean, default=False)
    approval_status = Column(String(20), default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

