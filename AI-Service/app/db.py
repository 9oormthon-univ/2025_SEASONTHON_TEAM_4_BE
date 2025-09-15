from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import config

# Database URL from config
DATABASE_URL = config.DATABASE_URL

# Create SQLAlchemy engine (MySQL only)
engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

def init_db():
    """Initialize database tables"""
    # Import all models here to ensure they are registered with Base
    from app.models.database_models import Member, GlucoseLog, FoodLog, ExerciseLog, Quest
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Check if data already exists
    db = SessionLocal()
    try:
        existing_members = db.query(Member).count()
        if existing_members > 0:
            return
        
        # Create sample data only if no data exists
        
        # Create sample data
        from datetime import datetime, timedelta
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Create sample members
        from datetime import date
        members = [
            Member(
                member_id=1,
                birth=date(1990, 1, 1),
                code="USER001",
                diabetes_type="DM_2",
                email="test@example.com",
                gender="MALE",
                height=175.0,
                password="hashed_password",
                sensor="CA",
                status="ACTIVE",
                username="testuser",
                weight=70.0
            ),
            Member(
                member_id=2,
                birth=date(1985, 3, 15),
                code="USER002",
                diabetes_type="DM_1",
                email="user2@example.com",
                gender="FEMALE",
                height=165.0,
                password="hashed_password2",
                sensor="DC",
                status="ACTIVE",
                username="user2",
                weight=55.0
            ),
            Member(
                member_id=3,
                birth=date(1992, 5, 20),
                code="USER003",
                diabetes_type="DM_2",
                email="user3@example.com",
                gender="MALE",
                height=180.0,
                password="hashed_password3",
                sensor="FL",
                status="ACTIVE",
                username="user3",
                weight=80.0
            )
        ]
        for member in members:
            db.add(member)
        
        # Create sample glucose logs (오늘과 어제 데이터)
        glucose_logs = [
            # 오늘 데이터 (member_id=1)
            GlucoseLog(member_id=1, glucose_mg_dl=95.0, time="07:00", date=today),
            GlucoseLog(member_id=1, glucose_mg_dl=120.0, time="08:30", date=today),
            GlucoseLog(member_id=1, glucose_mg_dl=140.0, time="12:00", date=today),
            GlucoseLog(member_id=1, glucose_mg_dl=135.0, time="14:00", date=today),
            GlucoseLog(member_id=1, glucose_mg_dl=110.0, time="18:00", date=today),
            GlucoseLog(member_id=1, glucose_mg_dl=105.0, time="20:00", date=today),
            # 어제 데이터 (member_id=1)
            GlucoseLog(member_id=1, glucose_mg_dl=100.0, time="07:30", date=yesterday),
            GlucoseLog(member_id=1, glucose_mg_dl=125.0, time="08:45", date=yesterday),
            GlucoseLog(member_id=1, glucose_mg_dl=160.0, time="12:30", date=yesterday),
            GlucoseLog(member_id=1, glucose_mg_dl=145.0, time="15:00", date=yesterday),
            GlucoseLog(member_id=1, glucose_mg_dl=130.0, time="18:30", date=yesterday),
            GlucoseLog(member_id=1, glucose_mg_dl=115.0, time="21:00", date=yesterday),
            # 다른 회원 데이터
            GlucoseLog(member_id=2, glucose_mg_dl=90.0, time="08:00", date=today),
            GlucoseLog(member_id=2, glucose_mg_dl=110.0, time="12:00", date=today),
            GlucoseLog(member_id=2, glucose_mg_dl=95.0, time="18:00", date=today),
        ]
        for log in glucose_logs:
            db.add(log)
        
        # Create sample food logs (오늘과 어제 데이터)
        food_logs = [
            # 오늘 데이터 (member_id=1)
            FoodLog(member_id=1, name="현미밥", type="아침", carbs=50.0, calories=200.0, time="08:00", date=today),
            FoodLog(member_id=1, name="닭가슴살", type="아침", carbs=0.0, calories=150.0, time="08:00", date=today),
            FoodLog(member_id=1, name="시금치나물", type="아침", carbs=5.0, calories=30.0, time="08:00", date=today),
            FoodLog(member_id=1, name="김치찌개", type="점심", carbs=30.0, calories=250.0, time="12:30", date=today),
            FoodLog(member_id=1, name="잡곡밥", type="점심", carbs=45.0, calories=180.0, time="12:30", date=today),
            FoodLog(member_id=1, name="연어구이", type="저녁", carbs=5.0, calories=300.0, time="18:30", date=today),
            FoodLog(member_id=1, name="브로콜리", type="저녁", carbs=8.0, calories=40.0, time="18:30", date=today),
            FoodLog(member_id=1, name="사과", type="간식", carbs=20.0, calories=80.0, time="15:00", date=today),
            # 어제 데이터 (member_id=1)
            FoodLog(member_id=1, name="토스트", type="아침", carbs=35.0, calories=150.0, time="08:15", date=yesterday),
            FoodLog(member_id=1, name="계란프라이", type="아침", carbs=2.0, calories=120.0, time="08:15", date=yesterday),
            FoodLog(member_id=1, name="라면", type="점심", carbs=60.0, calories=400.0, time="12:45", date=yesterday),
            FoodLog(member_id=1, name="김밥", type="점심", carbs=40.0, calories=200.0, time="12:45", date=yesterday),
            FoodLog(member_id=1, name="삼겹살", type="저녁", carbs=0.0, calories=500.0, time="19:00", date=yesterday),
            FoodLog(member_id=1, name="소주", type="저녁", carbs=15.0, calories=200.0, time="19:00", date=yesterday),
            FoodLog(member_id=1, name="아이스크림", type="간식", carbs=25.0, calories=150.0, time="21:30", date=yesterday),
            # 다른 회원 데이터
            FoodLog(member_id=2, name="샐러드", type="아침", carbs=10.0, calories=100.0, time="08:00", date=today),
            FoodLog(member_id=2, name="요거트", type="점심", carbs=15.0, calories=120.0, time="12:00", date=today),
            FoodLog(member_id=2, name="생선구이", type="저녁", carbs=5.0, calories=250.0, time="18:00", date=today),
        ]
        for log in food_logs:
            db.add(log)
        
        # Create sample exercise logs (오늘과 어제 데이터)
        exercise_logs = [
            # 오늘 데이터 (member_id=1)
            ExerciseLog(member_id=1, exercise_name="걷기", exercise_duration=30, exercise_date=today),
            ExerciseLog(member_id=1, exercise_name="자전거", exercise_duration=45, exercise_date=today),
            ExerciseLog(member_id=1, exercise_name="요가", exercise_duration=20, exercise_date=today),
            # 어제 데이터 (member_id=1)
            ExerciseLog(member_id=1, exercise_name="수영", exercise_duration=60, exercise_date=yesterday),
            ExerciseLog(member_id=1, exercise_name="헬스장", exercise_duration=90, exercise_date=yesterday),
            ExerciseLog(member_id=1, exercise_name="조깅", exercise_duration=25, exercise_date=yesterday),
            # 다른 회원 데이터
            ExerciseLog(member_id=2, exercise_name="필라테스", exercise_duration=40, exercise_date=today),
            ExerciseLog(member_id=2, exercise_name="산책", exercise_duration=20, exercise_date=today),
        ]
        for log in exercise_logs:
            db.add(log)
        
        db.commit()
    except Exception as e:
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