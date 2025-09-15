from sqlalchemy import Column, Integer, String, DateTime, Text, Float, TIMESTAMP, ForeignKey, BigInteger, Enum, Date
from sqlalchemy.sql import func
from app.db import Base


class Member(Base):
    __tablename__ = "member"

    member_id = Column(BigInteger, primary_key=True, index=True)
    created_at = Column(DateTime(6), nullable=True)
    modified_at = Column(DateTime(6), nullable=True)
    birth = Column(Date, nullable=False)
    code = Column(String(10), nullable=False, unique=True)
    diabetes_type = Column(Enum('DM_1', 'DM_2', 'DM_2I', 'DM_P', 'NULL', name='diabetes_type'), nullable=False)
    email = Column(String(255), nullable=False)
    gender = Column(Enum('FEMALE', 'MALE', name='gender'), nullable=False)
    height = Column(Float, nullable=False)
    inactive_date = Column(Date, nullable=True)
    password = Column(String(255), nullable=False)
    sensor = Column(Enum('CA', 'DC', 'FL', name='sensor'), nullable=False)
    status = Column(Enum('ACTIVE', 'INACTIVE', name='status'), nullable=True, default='ACTIVE')
    username = Column(String(50), nullable=False)
    weight = Column(Float, nullable=False)


class GlucoseLog(Base):
    __tablename__ = "glucose"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(BigInteger, ForeignKey("member.member_id"), nullable=False, index=True)
    glucose_mg_dl = Column(Float, nullable=False)
    time = Column(String(8), nullable=True)  # HH:MM format
    date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class FoodLog(Base):
    __tablename__ = "food"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(BigInteger, ForeignKey("member.member_id"), nullable=False, index=True)
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
    member_id = Column(BigInteger, ForeignKey("member.member_id"), nullable=False, index=True)
    exercise_name = Column(String(100), nullable=False)  # 운동 종류(이름)
    exercise_duration = Column(Integer, nullable=True)  # 운동 시간(분)
    exercise_date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
