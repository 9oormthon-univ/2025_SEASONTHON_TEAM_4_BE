"""데이터베이스 관련 유틸리티 함수들"""

from .database import SessionLocal
from app.models.database_models import Member, Glucose, Quest, Food, Exercise
from datetime import datetime


def get_member_info(member_id: int):
    """회원 정보 조회"""
    db = SessionLocal()
    try:
        member = db.query(Member).filter(Member.member_id == member_id).first()
        if member:
            # 생년월일에서 나이 계산
            if isinstance(member.birth, int):
                birth_year = member.birth // 10000
            else:
                birth_year = member.birth.year
            current_year = datetime.now().year
            age = current_year - birth_year
            return {
                'age': age,
                'diabetes_type': member.diabetes_type,
                'gender': member.gender,
                'height': member.height,
                'weight': member.weight
            }
        return None
    finally:
        db.close()


def get_glucose_data(member_id: int, date: str):
    """혈당 데이터 조회"""
    db = SessionLocal()
    try:
        readings = (
            db.query(Glucose)
            .filter(Glucose.member_id == member_id, Glucose.date == date)
            .order_by(Glucose.time.asc())
            .all()
        )
        return readings
    finally:
        db.close()


def get_weekly_glucose_data(member_id: int, start_date: str, end_date: str):
    """주간 혈당 데이터 조회"""
    db = SessionLocal()
    try:
        readings = (
            db.query(Glucose)
            .filter(
                Glucose.member_id == member_id,
                Glucose.date >= start_date,
                Glucose.date <= end_date
            )
            .order_by(Glucose.date.asc(), Glucose.time.asc())
            .all()
        )
        return readings
    finally:
        db.close()


def save_quests_to_db(member_id, quests, date_str):
    """퀘스트를 데이터베이스에 저장"""
    try:
        db = SessionLocal()
        
        # 기존 퀘스트가 있으면 삭제
        existing_quests = db.query(Quest).filter(
            Quest.member_id == member_id,
            Quest.quest_date == date_str
        ).all()
        
        if existing_quests:
            for quest in existing_quests:
                db.delete(quest)
            db.commit()
        
        # 새 퀘스트 저장
        for title, content in quests.items():
            quest_type = "GLUCOSE" if "혈당" in title else "RECORD"
            
            quest = Quest(
                member_id=member_id,
                quest_type=quest_type,
                quest_title=title,
                quest_content=content,
                quest_date=date_str
            )
            db.add(quest)
        
        db.commit()
        print(f"퀘스트 저장 완료: {len(quests)}개")
        
    except Exception as e:
        print(f"퀘스트 저장 오류: {e}")
        db.rollback()
    finally:
        db.close()


def get_quests_by_date(member_id, date_str):
    """특정 날짜의 퀘스트 조회"""
    try:
        db = SessionLocal()
        
        quests = db.query(Quest).filter(
            Quest.member_id == member_id,
            Quest.quest_date == date_str
        ).order_by(Quest.created_at.asc()).all()
        
        result = []
        completed_count = 0
        
        for quest in quests:
            quest_data = {
                "quest_id": quest.id,
                "quest_title": quest.quest_title,
                "quest_content": quest.quest_content,
                "is_completed": quest.is_completed,
                "approval_status": quest.approval_status
            }
            result.append(quest_data)
            
            if quest.is_completed:
                completed_count += 1
        
        # 완료율 계산
        total_quests = len(quests)
        completion_rate = round((completed_count / total_quests * 100), 1) if total_quests > 0 else 0
        
        return {
            "quests": result, 
            "date": date_str,
            "completion_rate": completion_rate,
            "completed_count": completed_count,
            "total_count": total_quests
        }
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


def get_food_data(member_id: int, date: str):
    """음식 데이터 조회"""
    db = SessionLocal()
    try:
        foods = (
            db.query(Food)
            .filter(Food.member_id == member_id, Food.date == date)
            .order_by(Food.time.asc())
            .all()
        )
        return foods
    finally:
        db.close()


def get_exercise_data(member_id: int, date: str):
    """운동 데이터 조회"""
    db = SessionLocal()
    try:
        exercises = (
            db.query(Exercise)
            .filter(Exercise.member_id == member_id, Exercise.exercise_date == date)
            .order_by(Exercise.created_at.asc())
            .all()
        )
        return exercises
    finally:
        db.close()


def get_food_data_by_period(member_id: int, start_date: str, end_date: str):
    """기간별 음식 데이터 조회"""
    db = SessionLocal()
    try:
        foods = (
            db.query(Food)
            .filter(
                Food.member_id == member_id,
                Food.date >= start_date,
                Food.date <= end_date
            )
            .order_by(Food.date.asc(), Food.time.asc())
            .all()
        )
        return foods
    finally:
        db.close()


def get_exercise_data_by_period(member_id: int, start_date: str, end_date: str):
    """기간별 운동 데이터 조회"""
    db = SessionLocal()
    try:
        exercises = (
            db.query(Exercise)
            .filter(
                Exercise.member_id == member_id,
                Exercise.exercise_date >= start_date,
                Exercise.exercise_date <= end_date
            )
            .order_by(Exercise.exercise_date.asc(), Exercise.created_at.asc())
            .all()
        )
        return exercises
    finally:
        db.close()


def get_glucose_food_correlation(member_id: int, date: str):
    """특정 날짜의 혈당-음식 상관관계 데이터 조회"""
    db = SessionLocal()
    try:
        # 해당 날짜의 모든 데이터 조회
        glucose_data = (
            db.query(Glucose)
            .filter(Glucose.member_id == member_id, Glucose.date == date)
            .order_by(Glucose.time.asc())
            .all()
        )
        
        food_data = (
            db.query(Food)
            .filter(Food.member_id == member_id, Food.date == date)
            .order_by(Food.time.asc())
            .all()
        )
        
        return {
            'glucose': glucose_data,
            'food': food_data
        }
    finally:
        db.close()


def get_glucose_exercise_correlation(member_id: int, date: str):
    """특정 날짜의 혈당-운동 상관관계 데이터 조회"""
    db = SessionLocal()
    try:
        # 해당 날짜의 모든 데이터 조회
        glucose_data = (
            db.query(Glucose)
            .filter(Glucose.member_id == member_id, Glucose.date == date)
            .order_by(Glucose.time.asc())
            .all()
        )
        
        exercise_data = (
            db.query(Exercise)
            .filter(Exercise.member_id == member_id, Exercise.exercise_date == date)
            .order_by(Exercise.created_at.asc())
            .all()
        )
        
        return {
            'glucose': glucose_data,
            'exercise': exercise_data
        }
    finally:
        db.close()
