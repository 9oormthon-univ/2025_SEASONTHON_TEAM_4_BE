from flask import Flask, request, jsonify
from flask_cors import CORS
from app.utils.io import load_text
from app.services.glucose_service import calculate_glucose_metrics, analyze_glucose
from app.services.record_service import calculate_food_metrics, analyze_food
from app.db import SessionLocal
from app.models.database_models import GlucoseLog, FoodLog, ExerciseLog, Member, Quest
from config import config
from datetime import datetime
import random
import json
import re
import os
import sys


app = Flask(__name__)

# CORS 설정
CORS(app, 
     origins=config.CORS_ORIGINS,
     methods=config.CORS_METHODS,
     allow_headers=config.CORS_HEADERS,
     supports_credentials=True)


def get_member_info(member_id: int):
    """회원 정보 조회"""
    db = SessionLocal()
    try:
        member = db.query(Member).filter(Member.member_id == member_id).first()
        if member:
            # 생년월일에서 나이 계산
            if isinstance(member.birth, int):
                # 기존 BigInteger 형식 처리
                birth_year = member.birth // 10000
            else:
                # Date 형식 처리
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


def get_today_glucose_data(member_id: int, today: str):
    """오늘의 혈당 데이터 조회"""
    db = SessionLocal()
    try:
        readings = (
            db.query(GlucoseLog)
            .filter(GlucoseLog.member_id == member_id, GlucoseLog.date == today)
            .order_by(GlucoseLog.time.asc())
            .all()
        )
        return readings
    finally:
        db.close()


def get_today_record_data(member_id: int, today: str):
    """오늘의 음식 및 운동 데이터 조회"""
    db = SessionLocal()
    try:
        foods = (
            db.query(FoodLog)
            .filter(FoodLog.member_id == member_id, FoodLog.date == today)
            .order_by(FoodLog.time.asc())
            .all()
        )
        exercises = (
            db.query(ExerciseLog)
            .filter(ExerciseLog.member_id == member_id, ExerciseLog.exercise_date == today)
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


def generate_glucose_quest_pool(glucose_metrics):
    """혈당 데이터를 기반으로 개인화된 퀘스트 풀 생성"""
    avg_glucose = glucose_metrics.get('average_glucose', 120)
    max_glucose = glucose_metrics.get('max_glucose', 180)
    min_glucose = glucose_metrics.get('min_glucose', 80)
    spike_count = glucose_metrics.get('spike_count', 3)
    
    # 목표 범위 계산 (정상 범위 80-140mg/dL)
    target_min = 80
    target_max = 140
    
    # 평균 혈당 목표 (현재 평균보다 10-20 낮게)
    target_avg = max(100, avg_glucose - 15)
    
    # 최고 혈당 목표 (현재 최고보다 20-30 낮게)
    target_max_glucose = max(160, max_glucose - 25)
    
    # 스파이크 목표 (현재보다 1-2회 적게)
    target_spikes = max(1, spike_count - 1)
    
    # 소수점 둘째자리까지 포맷팅
    def format_number(num):
        if isinstance(num, (int, float)):
            if num == int(num):
                return str(int(num))
            else:
                return f"{num:.2f}"
        return str(num)
    
    # 혈당 상태 분석 및 개인화된 퀘스트 생성
    quest_pool = {}
    
    # 1. 평균 혈당 기반 퀘스트
    if avg_glucose > 130:
        quest_pool["평균 혈당 개선 퀘스트"] = f"현재 평균 {format_number(avg_glucose)}mg/dL로 조금 높아! {format_number(target_avg)}mg/dL 이하로 낮추기 위해 물을 하루 8잔 마셔보자"
    elif avg_glucose > 120:
        quest_pool["평균 혈당 유지 퀘스트"] = f"현재 평균 {format_number(avg_glucose)}mg/dL로 양호해! {format_number(target_avg)}mg/dL 목표로 혈당을 안정적으로 유지해보자"
    else:
        quest_pool["평균 혈당 유지 퀘스트"] = f"현재 평균 {format_number(avg_glucose)}mg/dL로 아주 좋아! 이 상태를 계속 유지해보자"
    
    # 2. 최고 혈당 기반 퀘스트
    if max_glucose > 200:
        quest_pool["최고 혈당 긴급 관리 퀘스트"] = f"최고 혈당이 {format_number(max_glucose)}mg/dL로 매우 높아! 180mg/dL 이하로 낮추기 위해 심호흡 5회 후 물 2잔 마셔보자"
    elif max_glucose > 180:
        quest_pool["최고 혈당 관리 퀘스트"] = f"최고 혈당이 {format_number(max_glucose)}mg/dL로 높아! 160mg/dL 이하로 낮추기 위해 물을 충분히 마셔보자"
    elif max_glucose > 140:
        quest_pool["최고 혈당 주의 퀘스트"] = f"최고 혈당이 {format_number(max_glucose)}mg/dL로 조금 높아! 140mg/dL 이하로 유지하기 위해 혈당을 안정적으로 관리해보자"
    else:
        quest_pool["최고 혈당 유지 퀘스트"] = f"최고 혈당이 {format_number(max_glucose)}mg/dL로 안정적이야! 이 상태를 계속 유지해보자"
    
    # 3. 스파이크 기반 퀘스트
    if spike_count > 2:
        quest_pool["혈당 스파이크 방지 퀘스트"] = f"오늘 {spike_count}번의 혈당 급상승이 있었어! {target_spikes}회 이하로 줄이기 위해 스트레스를 줄여보자"
    elif spike_count > 0:
        quest_pool["혈당 안정 챌린지 퀘스트"] = f"오늘 {spike_count}번의 혈당 급상승이 있었어! {target_spikes}회 이하로 줄이기 위해 심호흡으로 안정을 찾아보자"
    else:
        quest_pool["혈당 안정 유지 퀘스트"] = f"오늘 급상승이 없어서 아주 좋아! 이 안정적인 패턴을 계속 유지해보자"
    
    # 4. 혈당 변동폭 기반 퀘스트 (현실적인 범위로 조정)
    glucose_range = max_glucose - min_glucose
    if glucose_range > 100:
        quest_pool["혈당 안정화 퀘스트"] = f"혈당 변동폭이 {format_number(glucose_range)}mg/dL로 매우 크네! 80mg/dL 이하로 줄이기 위해 규칙적인 생활을 해보자"
    elif glucose_range > 80:
        quest_pool["혈당 안정 개선 퀘스트"] = f"혈당 변동폭이 {format_number(glucose_range)}mg/dL로 크네! 60mg/dL 이하로 줄이기 위해 안정적인 패턴을 만들어보자"
    elif glucose_range > 60:
        quest_pool["혈당 안정 관리 퀘스트"] = f"혈당 변동폭이 {format_number(glucose_range)}mg/dL야! 더 안정적으로 만들기 위해 꾸준히 관리해보자"
    else:
        quest_pool["혈당 안정 유지 퀘스트"] = f"혈당 변동폭이 {format_number(glucose_range)}mg/dL로 안정적이야! 이 상태를 계속 유지해보자"
    
    # 5. 종합 상태 기반 퀘스트 (정확한 당뇨 기준 적용)
    if avg_glucose > 140 and max_glucose > 180:
        quest_pool["종합 혈당 관리 퀘스트"] = f"평균 혈당이 {format_number(avg_glucose)}mg/dL, 최고 혈당이 {format_number(max_glucose)}mg/dL로 전반적으로 높아! 개선을 위해 꾸준히 관리해보자"
    elif avg_glucose <= 100 and max_glucose <= 140:
        quest_pool["혈당 관리 우수 퀘스트"] = f"평균 혈당이 {format_number(avg_glucose)}mg/dL, 최고 혈당이 {format_number(max_glucose)}mg/dL로 아주 좋아! 이 우수한 관리를 계속 유지해보자"
    else:
        quest_pool["혈당 관리 개선 퀘스트"] = f"현재 상태를 바탕으로 조금씩 개선해보자"
    
    # 6. 추가 혈당 관리 퀘스트들
    quest_pool["수분 섭취 퀘스트"] = "혈당 희석을 위해 하루 8잔 이상 물 마셔보자"
    quest_pool["스트레스 관리 퀘스트"] = "스트레스성 혈당 상승을 방지하기 위해 심호흡 5회 해보자"
    quest_pool["혈당 안정 퀘스트"] = "혈당을 안정적으로 유지하기 위해 규칙적인 생활을 해보자"
    quest_pool["건강 관리 퀘스트"] = "전반적인 건강 관리를 위해 꾸준히 노력해보자"
    

    
    return quest_pool


def select_daily_quests(glucose_quests_dict, record_quests_dict, date_str, count=4):
    """날짜별로 고정된 퀘스트 선택 (같은 날에는 항상 같은 퀘스트)"""
    glucose_items = list(glucose_quests_dict.items())
    record_items = list(record_quests_dict.items())
    
    # 날짜를 시드로 사용하여 일관된 선택
    date_seed = hash(date_str) % (2**32)
    random.seed(date_seed)
    
    # 혈당 퀘스트 2개, 기록 퀘스트 2개 선택
    glucose_count = min(2, len(glucose_items))
    record_count = min(2, len(record_items))
    
    selected_glucose = random.sample(glucose_items, glucose_count)
    selected_record = random.sample(record_items, record_count)
    
    # 시드 초기화 (다른 랜덤 함수에 영향 주지 않도록)
    random.seed()
    
    result = {}
    for key, value in selected_glucose:
        result[key] = value
    for key, value in selected_record:
        result[key] = value
    
    return result

@app.route("/quest", methods=["GET"])
def combined_quest():
    """혈당 퀘스트와 기록 퀘스트를 통합하여 총 4개 퀘스트 반환 (해당 날짜에 한 번만 생성)"""
    try:
        # Query parameters
        member_id = int(request.args.get("member_id", 1))
        today = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        # 회원 정보 조회
        member_info = get_member_info(member_id)
        if not member_info:
            return jsonify({"error": "회원을 찾을 수 없습니다."}), 404
        
        # 해당 날짜에 이미 퀘스트가 있는지 확인
        existing_quests = get_quests_by_date(member_id, today)
        if "error" not in existing_quests and existing_quests.get("count", 0) > 0:
            # 기존 퀘스트가 있으면 기존 퀘스트를 반환
            quest_list = existing_quests.get("quests", [])
            result = {}
            for quest in quest_list:
                result[quest["quest_title"]] = quest["quest_content"]
            return jsonify({"result": result})
        
        # 혈당 데이터 기반 퀘스트 풀 생성
        glucose_readings = get_today_glucose_data(member_id, today)
        blood_sugar_data = format_glucose_data(glucose_readings)
        glucose_metrics = calculate_glucose_metrics(blood_sugar_data)
        
        # 실제 데이터를 기반으로 퀘스트 풀 생성
        glucose_quest_pool = generate_glucose_quest_pool(glucose_metrics)
        
        # 기록 퀘스트 풀 (record_quest_prompt.txt 기반)
        record_quest_pool = {
            "식습관 개선 퀘스트": "저녁은 맛있는 현미밥이나 고구마로 먹어보자!",
            "활동 습관 퀘스트": "식사 후에 가볍게 10분 걷기로 소화를 도와보자!",
            "음식 기록 퀘스트": "오늘 하루 음식 기록 3번(아침, 점심, 저녁) 입력해봐!",
            "패턴 교정 퀘스트": "저녁 늦은 시간 간식을 오늘은 피해보자!",
            "운동 습관 퀘스트": "오늘은 20분 이상 걷기나 달리기로 놀아보자!",
            "식사 습관 개선 퀘스트": "오늘은 식이섬유가 포함된 사과 또는 바나나 꼭 먹어보자!",
            "계단 운동 퀘스트": "계단을 2층씩 3번 오르내리며 놀아보자!",
            "음식 사진 퀘스트": "음식 사진도 찍어서 예쁘게 기록해봐!",
            "단백질 섭취 퀘스트": f"오늘은 고당분 간식 대신 단백질 간식을 먹어보자!",
            "야식 자제 퀘스트": "야식을 자제하고 저녁 7시 이후에는 음식을 조금만 먹어보자!",
            "매일 스트레칭 퀘스트": "매일 3회씩 5분 스트레칭을 시작해보자!",
            "물 마시기 습관 퀘스트": "식사 전에 물 한 잔 마시는 습관을 만들어보자!",
            "걷기 도전 퀘스트": "하루에 5,000보 걷기 도전해보자!",
            "간식 기록 퀘스트": "간식까지 포함해서 모든 먹은 음식을 시간과 함께 기록해보자!",
            "채소 섭취 퀘스트": "채소를 매끼마다 조금씩 먹어보자!",
            "식사 간격 조절 퀘스트": "식사 간격을 일정하게 맞추고 간식은 조금만 먹어보자!",
            "간단한 운동 퀘스트": "15분만 동네 산책 하면서 걸어보는 건 어떨끼?"
        }
        
        result = select_daily_quests(glucose_quest_pool, record_quest_pool, today, count=4)
        
        # 퀘스트를 데이터베이스에 저장
        save_quests_to_db(member_id, result, today)
        
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def save_quests_to_db(member_id, quests, date_str):
    """퀘스트를 데이터베이스에 저장"""
    try:
        db = SessionLocal()
        
        # 기존 퀘스트가 있는지 확인
        existing_quests = db.query(Quest).filter(
            Quest.member_id == member_id,
            Quest.quest_date == date_str
        ).all()
        
        # 기존 퀘스트가 있으면 삭제
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
        for quest in quests:
            quest_data = {
                "quest_title": quest.quest_title,
                "quest_content": quest.quest_content,
                "is_completed": quest.is_completed,
                "approval_status": quest.approval_status
            }
            result.append(quest_data)
        
        return {"quests": result, "date": date_str}
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


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
        member_id = int(request.args.get("member_id", 1))
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 회원 정보 조회
        member_info = get_member_info(member_id)
        if not member_info:
            return jsonify({"error": "회원을 찾을 수 없습니다."}), 404
        
        # 혈당 데이터 조회 및 지표 계산
        readings = get_today_glucose_data(member_id, today)
        blood_sugar_data = format_glucose_data(readings)
        glucose_metrics = calculate_glucose_metrics(blood_sugar_data)
        avg_glucose = glucose_metrics.get('average_glucose', 0)
        max_glucose = glucose_metrics.get('max_glucose', 0)
        min_glucose = glucose_metrics.get('min_glucose', 0)
        spike_count = glucose_metrics.get('spike_count', 0)
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


@app.route("/quest/list", methods=["GET"])
def get_quests_api():
    """날짜별 퀘스트 조회 API"""
    try:
        member_id = int(request.args.get("member_id", 1))
        date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        result = get_quests_by_date(member_id, date_str)
        
        if "error" in result:
            return jsonify(result), 500
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/quest/complete", methods=["POST"])
def complete_quest_api():
    """퀘스트 완료 API"""
    try:
        data = request.get_json()
        quest_id = data.get("quest_id")
        member_id = data.get("member_id")
        
        if not quest_id or not member_id:
            return jsonify({"error": "quest_id와 member_id가 필요합니다."}), 400
        
        db = SessionLocal()
        try:
            # 퀘스트 조회
            quest = db.query(Quest).filter(
                Quest.id == quest_id,
                Quest.member_id == member_id
            ).first()
            
            if not quest:
                return jsonify({"error": "퀘스트를 찾을 수 없습니다."}), 404
            
            # 이미 완료된 퀘스트인지 확인
            if quest.is_completed:
                return jsonify({"error": "이미 완료된 퀘스트입니다."}), 400
            
            # 퀘스트 완료 처리 (자동으로 승인 요청 상태로 변경)
            quest.is_completed = True
            quest.approval_status = '요청 중'  # 완료 시 자동으로 승인 요청 상태
            quest.updated_at = datetime.now()
            
            db.commit()
            
            return jsonify({"message": "퀘스트가 완료되었습니다. 승인 요청이 전송되었습니다.", "quest_id": quest_id})
            
        except Exception as e:
            db.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/quest/approve", methods=["POST"])
def approve_quest_api():
    """퀘스트 승인 완료 API (관리자가 승인 완료 버튼을 누를 때)"""
    try:
        data = request.get_json()
        quest_id = data.get("quest_id")
        member_id = data.get("member_id")
        
        if not quest_id or not member_id:
            return jsonify({"error": "quest_id와 member_id가 필요합니다."}), 400
        
        db = SessionLocal()
        try:
            # 퀘스트 조회
            quest = db.query(Quest).filter(
                Quest.id == quest_id,
                Quest.member_id == member_id
            ).first()
            
            if not quest:
                return jsonify({"error": "퀘스트를 찾을 수 없습니다."}), 404
            
            # 승인 요청 중인 퀘스트인지 확인
            if quest.approval_status != '요청 중':
                return jsonify({"error": "승인 요청 중인 퀘스트가 아닙니다."}), 400
            
            # 퀘스트 승인 완료 처리 (달성 완료 상태로 변경)
            quest.approval_status = '달성 완료'
            quest.updated_at = datetime.now()
            
            db.commit()
            
            return jsonify({"message": "퀘스트가 승인 완료되었습니다.", "quest_id": quest_id})
            
        except Exception as e:
            db.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500




if __name__ == "__main__":
    # 데이터베이스 초기화
    from app.db import init_db
    init_db()
    
    # 서버 시작
    app.run(port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
