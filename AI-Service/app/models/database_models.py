"""데이터베이스 모델 정의"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, Date, Time, ForeignKey, Enum, BigInteger
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()


class ExerciseType(enum.Enum):
    """운동 타입 열거형"""
    WALKING = "WALKING"
    RUNNING = "RUNNING"
    CYCLING = "CYCLING"
    SWIMMING = "SWIMMING"
    WEIGHT_TRAINING = "WEIGHT_TRAINING"
    YOGA = "YOGA"
    PILATES = "PILATES"
    DANCE = "DANCE"
    OTHER = "OTHER"


class BaseTimeEntity:
    """기본 시간 엔티티 (Java BaseTimeEntity와 동일)"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Member(Base, BaseTimeEntity):
    """회원 모델"""
    __tablename__ = "member"
    
    member_id = Column(BigInteger, primary_key=True, index=True)
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
    
    # 관계 설정
    parent_children = relationship("ParentChild", back_populates="member")
    exercises = relationship("Exercise", back_populates="member")


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
    name = Column(String(200), nullable=False)  # 실제 DB 컬럼명에 맞춤
    type = Column(String(20))  # 실제 DB 컬럼명에 맞춤 (breakfast, lunch, dinner, snack)
    calories = Column(Float)
    carbs = Column(Float)
    # 실제 DB에 없는 컬럼들은 제거
    date = Column(String(10), nullable=False, index=True)  # varchar(10) in database
    time = Column(String(8), nullable=False)  # varchar(8) in database
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Parent(Base, BaseTimeEntity):
    """부모 모델"""
    __tablename__ = "parent"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 관계 설정
    parent_children = relationship("ParentChild", back_populates="parent")


class ParentChild(Base, BaseTimeEntity):
    """부모-자녀 관계 모델"""
    __tablename__ = "parent_child"
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(BigInteger, ForeignKey("member.member_id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("parent.id"), nullable=False)
    
    # 관계 설정
    member = relationship("Member", back_populates="parent_children")
    parent = relationship("Parent", back_populates="parent_children")


class Exercise(Base):
    """운동 모델 (기존 DB 구조 유지)"""
    __tablename__ = "exercise"
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(BigInteger, ForeignKey("member.member_id"), nullable=False, index=True)
    exercise_name = Column(String(100), nullable=False)  # 기존 DB 컬럼명 유지
    exercise_duration = Column(Integer)  # 기존 DB 컬럼명 유지
    exercise_date = Column(String(10), nullable=False, index=True)  # 기존 DB 컬럼명 유지
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    member = relationship("Member", back_populates="exercises")


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

