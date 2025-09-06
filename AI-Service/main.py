from flask import Flask, request, jsonify
from app.utils.io import load_text
from app.services.glucose_service import calculate_glucose_metrics, analyze_glucose
from app.services.record_service import calculate_food_metrics, analyze_food
from app.db import SessionLocal
from app.models.database_models import GlucoseLog, FoodLog, ExerciseLog, User
from datetime import datetime
import random
import json
import re

app = Flask(__name__)


def get_user_age(user_id: int):
    """사용자 나이 조회"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return user.age if user else None
    finally:
        db.close()


def get_today_glucose_data(user_id: int, today: str):
    """오늘의 혈당 데이터 조회"""
    db = SessionLocal()
    try:
        readings = (
            db.query(GlucoseLog)
            .filter(GlucoseLog.user_id == user_id, GlucoseLog.date == today)
            .order_by(GlucoseLog.time.asc())
            .all()
        )
        return readings
    finally:
        db.close()


def get_today_record_data(user_id: int, today: str):
    """오늘의 음식 및 운동 데이터 조회"""
    db = SessionLocal()
    try:
        foods = (
            db.query(FoodLog)
            .filter(FoodLog.user_id == user_id, FoodLog.date == today)
            .order_by(FoodLog.time.asc())
            .all()
        )
        exercises = (
            db.query(ExerciseLog)
            .filter(ExerciseLog.user_id == user_id, ExerciseLog.exercise_date == today)
            .order_by(ExerciseLog.exercise_date.asc())
            .all()
        )
        return foods, exercises
    finally:
        db.close()


def format_glucose_data(readings):
    """혈당 데이터를 CGM 형식으로 변환"""
    cgm_readings = []
    for r in readings:
        iso_time = f"{r.date}T{r.time}" if r.time else f"{r.date}T00:00:00"
        cgm_readings.append({
            "time": iso_time,
            "glucose_mg_dl": r.glucose_mg_dl,
        })
    return {"cgm_data": {"readings": cgm_readings}}


def format_record_data(foods, exercises, today):
    """음식 및 운동 데이터를 기록 형식으로 변환"""
    food_list = []
    for f in foods:
        food_list.append({
            "meal": f.type,
            "time": f.time or "",
            "items": [{
                "name": f.name,
                "calories": f.calories or 0,
                "carbs": f.carbs or 0,
            }],
        })
    
    exercise_list = []
    for e in exercises:
        exercise_list.append({
            "name": e.exercise_name,
            "duration": e.exercise_duration or 0,
            "date": e.exercise_date
        })
    
    return {
        "records": [{
            "date": today, 
            "food": food_list,
            "exercise": exercise_list
        }]
    }


def select_random_quests(glucose_quests_dict, record_quests_dict, count=2):
    """퀘스트를 무작위로 선택"""
    glucose_items = list(glucose_quests_dict.items())
    record_items = list(record_quests_dict.items())
    
    selected_glucose = random.sample(glucose_items, min(count, len(glucose_items)))
    selected_record = random.sample(record_items, min(count, len(record_items)))
    
    result = {}
    for key, value in selected_glucose:
        result[key] = value
    for key, value in selected_record:
        result[key] = value
    
    return result

@app.route("/quest", methods=["GET"])
def combined_quest():
    """혈당 퀘스트와 기록 퀘스트를 통합하여 총 4개 퀘스트 반환"""
    try:
        # Query parameters
        user_id = int(request.args.get("user_id", 1))
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 혈당 퀘스트 생성
        glucose_readings = get_today_glucose_data(user_id, today)
        blood_sugar_data = format_glucose_data(glucose_readings)
        glucose_metrics = calculate_glucose_metrics(blood_sugar_data)
        user_age = get_user_age(user_id)
        
        glucose_prompt = load_text("prompts/glucose_quest_prompt.txt")
        glucose_result = analyze_glucose(glucose_metrics, glucose_prompt, user_age)
        
        # 기록 퀘스트 생성
        foods, exercises = get_today_record_data(user_id, today)
        record_data = format_record_data(foods, exercises, today)
        record_metrics = calculate_food_metrics(record_data)
        
        record_prompt = load_text("prompts/record_quest_prompt.txt")
        record_result = analyze_food(record_metrics, record_prompt, user_age)
        
        # 퀘스트 무작위 선택
        glucose_quests_dict = glucose_result.get("result", {})
        record_quests_dict = record_result.get("result", {})
        
        result = select_random_quests(glucose_quests_dict, record_quests_dict)
        
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def calculate_glucose_metrics_from_readings(readings):
    """혈당 측정값에서 지표 계산"""
    glucose_values = [r.glucose_mg_dl for r in readings if r.glucose_mg_dl is not None]
    
    if not glucose_values:
        return 0, 0, 0, 0
    
    avg_glucose = sum(glucose_values) / len(glucose_values)
    max_glucose = max(glucose_values)
    min_glucose = min(glucose_values)
    
    # 급상승 횟수 계산 (이전 값보다 30mg/dL 이상 증가한 경우)
    spike_count = 0
    for i in range(1, len(glucose_values)):
        if glucose_values[i] - glucose_values[i-1] >= 30:
            spike_count += 1
    
    return avg_glucose, max_glucose, min_glucose, spike_count


def format_analyze_prompt(prompt, avg_glucose, max_glucose, min_glucose, spike_count, measurement_count):
    """분석 프롬프트에 실제 데이터 포맷팅"""
    formatted_prompt = prompt.replace("{{avg_glucose}}", str(round(avg_glucose, 1) if avg_glucose > 0 else 0))
    formatted_prompt = formatted_prompt.replace("{{max_glucose}}", str(round(max_glucose, 1) if max_glucose > 0 else 0))
    formatted_prompt = formatted_prompt.replace("{{min_glucose}}", str(round(min_glucose, 1) if min_glucose > 0 else 0))
    formatted_prompt = formatted_prompt.replace("{{spike_count}}", str(spike_count))
    formatted_prompt = formatted_prompt.replace("{{measurement_count}}", str(measurement_count))
    return formatted_prompt


def extract_json_from_ai_response(ai_response):
    """AI 응답에서 JSON 추출"""
    try:
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        else:
            raise json.JSONDecodeError("No JSON found", ai_response, 0)
    except (json.JSONDecodeError, AttributeError):
        return None


@app.route("/analyze", methods=["GET"])
def glucose_analyze():
    """혈당 종합 분석 및 비서 코칭"""
    try:
        # Query parameters
        user_id = int(request.args.get("user_id", 1))
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 혈당 데이터 조회 및 지표 계산
        readings = get_today_glucose_data(user_id, today)
        avg_glucose, max_glucose, min_glucose, spike_count = calculate_glucose_metrics_from_readings(readings)
        glucose_values = [r.glucose_mg_dl for r in readings if r.glucose_mg_dl is not None]
        
        # AI 분석 시도
        prompt = load_text("prompts/glucose_analysis_prompt.txt")
        formatted_prompt = format_analyze_prompt(prompt, avg_glucose, max_glucose, min_glucose, spike_count, len(glucose_values))
        
        from app.ai import call_openai_api
        ai_response = call_openai_api(formatted_prompt, "당신은 혈당 관리를 도와주는 친근한 비서입니다. 반드시 JSON 형식으로만 응답해주세요.")
        
        analysis_result = extract_json_from_ai_response(ai_response)
        
        # AI 분석 실패 시 기본 응답 반환
        if not analysis_result:
            analysis_result = {
                "result": {
                    "혈당 스파이크": "오늘은 혈당 측정 기록이 없어요 📝 정기적인 혈당 체크로 건강을 관리해보세요!" if not glucose_values else (
                        "오늘은 급상승이 없었어요! 안정적인 하루였네요 😊" if spike_count == 0 else
                        f"오늘 {spike_count}번의 급상승이 있었어요 ⚡ 식사 후 혈당 관리를 더 신경써보세요!" if spike_count == 1 else
                        f"오늘 {spike_count}번의 급상승이 있었어요 ⚡ 식사량과 탄수화물 섭취를 조절해보세요!"
                    ),
                    "평균 혈당": ["혈당 측정 기록이 없어 평균을 계산할 수 없어요 📊", "하루 3-4회 혈당을 측정해보세요!"] if not glucose_values else [
                        f"오늘 하루 평균: {avg_glucose:.0f}mg/dL",
                        "정상 범위로 매우 좋아요! 🎉" if avg_glucose <= 100 else
                        "정상 범위보다 조금 높아요 📈" if avg_glucose <= 140 else
                        "정상 범위보다 높아요 📈",
                        "원인 힌트: 간식 섭취 시간 간격이 짧았어요." if avg_glucose <= 140 else
                        "원인 힌트: 식사량과 탄수화물 섭취가 많았어요."
                    ],
                    "최고 혈당": "혈당 측정 기록이 없어 최고값을 확인할 수 없어요 📈 식사 전후 혈당 체크를 시작해보세요!" if not glucose_values else (
                        f"가장 높았을 때는 {max_glucose:.0f}mg/dL였지만 곧 안정을 찾았어요 😌" if max_glucose <= 140 else
                        f"가장 높았을 때는 {max_glucose:.0f}mg/dL였어요 📈 식사 후 혈당 상승을 조절해보세요!" if max_glucose <= 180 else
                        f"가장 높았을 때는 {max_glucose:.0f}mg/dL였어요 📈 식사량과 탄수화물 섭취를 줄여보세요!"
                    ),
                    "단짝이의 평가": "혈당 측정이 첫 걸음이에요! 꾸준히 측정하면서 건강한 습관을 만들어가요 💪" if not glucose_values else (
                        "오늘도 훌륭한 혈당 관리였어요! 이 상태를 계속 유지해보세요 💪" if avg_glucose <= 100 and spike_count <= 1 else
                        "혈당 관리가 양호해요! 조금만 더 신경쓰면 완벽할 거예요 🌟" if avg_glucose <= 140 and spike_count <= 2 else
                        "혈당 관리를 위해 식단 조절과 운동을 함께 해보세요! 함께 노력해봐요 🤝"
                    )
                }
            }
        
        return jsonify(analysis_result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Initialize database tables
    try:
        from app.db import init_db
        init_db()
    except Exception as e:
        print("DB init failed:", e)
    app.run(port=5000, debug=True)
