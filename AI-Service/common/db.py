from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 데이터베이스 URL 가져오기
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:1234@localhost:3306/danjjang")

# SQLAlchemy 엔진 생성
engine = create_engine(DATABASE_URL, echo=True)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()

def get_db():
    """데이터베이스 세션을 가져오는 함수"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """데이터베이스 테이블을 생성하고 샘플 데이터를 삽입하는 함수"""
    from common.models.database_models import Member, GlucoseLog, FoodLog, ExerciseLog, Quest
    
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    # 세션 생성
    db = SessionLocal()
    
    try:
        # 기존 데이터 확인
        existing_member = db.query(Member).first()
        if existing_member:
            print("데이터베이스에 이미 데이터가 있습니다.")
            return
        
        # 샘플 회원 데이터 삽입
        sample_members = [
            Member(
                member_id=1,
                username="김당뇨",
                email="user1@example.com",
                password="password123",
                birth="1985-03-15",
                gender="FEMALE",
                height=160.0,
                weight=55.0,
                diabetes_type="DM_2",
                sensor="CA",
                status="ACTIVE",
                code="USER001"
            ),
            Member(
                member_id=2,
                username="이혈당",
                email="user2@example.com",
                password="password456",
                birth="1990-07-22",
                gender="MALE",
                height=175.0,
                weight=70.0,
                diabetes_type="DM_1",
                sensor="CA",
                status="ACTIVE",
                code="USER002"
            ),
            Member(
                member_id=3,
                username="박건강",
                email="user3@example.com",
                password="password789",
                birth="1988-11-08",
                gender="FEMALE",
                height=165.0,
                weight=60.0,
                diabetes_type="DM_2",
                sensor="CA",
                status="ACTIVE",
                code="USER003"
            )
        ]
        
        for member in sample_members:
            db.add(member)
        
        db.commit()
        print("샘플 데이터가 성공적으로 삽입되었습니다.")
        
    except Exception as e:
        print(f"데이터 삽입 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()



