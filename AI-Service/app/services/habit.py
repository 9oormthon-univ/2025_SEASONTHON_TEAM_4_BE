import json
from datetime import datetime, timedelta
from collections import OrderedDict
from app.ai import call_openai_api
from app.db import SessionLocal
from app.models.logs import GlucoseLog, FoodLog, ExerciseLog


def calculate_habit_metrics(user_id: str = "demo_user", days: int = 7):
    """최근 N일간의 혈당, 음식, 운동 데이터를 종합 분석"""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days-1)).strftime("%Y-%m-%d")
    
    db = SessionLocal()
    try:
        # 혈당 데이터 조회
        glucose_data = (
            db.query(GlucoseLog)
            .filter(
                GlucoseLog.user_id == user_id,
                GlucoseLog.date >= start_date,
                GlucoseLog.date <= end_date
            )
            .order_by(GlucoseLog.date.asc(), GlucoseLog.time.asc())
            .all()
        )
        
        # 음식 데이터 조회
        food_data = (
            db.query(FoodLog)
            .filter(
                FoodLog.user_id == user_id,
                FoodLog.date >= start_date,
                FoodLog.date <= end_date
            )
            .order_by(FoodLog.date.asc(), FoodLog.time.asc())
            .all()
        )
        
        # 운동 데이터 조회
        exercise_data = (
            db.query(ExerciseLog)
            .filter(
                ExerciseLog.user_id == user_id,
                ExerciseLog.exercise_date >= start_date,
                ExerciseLog.exercise_date <= end_date
            )
            .order_by(ExerciseLog.exercise_date.asc())
            .all()
        )
        
    finally:
        db.close()
    
    # 패턴 감지를 위한 상세 분석
    patterns = analyze_patterns(glucose_data, food_data, exercise_data)
    
    # 혈당 지표 계산
    glucose_values = [g.glucose_mg_dl for g in glucose_data]
    glucose_metrics = {
        "total_readings": len(glucose_values),
        "avg_glucose": round(sum(glucose_values) / len(glucose_values), 1) if glucose_values else 0,
        "max_glucose": max(glucose_values) if glucose_values else 0,
        "min_glucose": min(glucose_values) if glucose_values else 0,
        "high_glucose_days": len(set(g.date for g in glucose_data if g.glucose_mg_dl > 140)),
        "low_glucose_days": len(set(g.date for g in glucose_data if g.glucose_mg_dl < 70))
    }
    
    # 음식 지표 계산
    total_calories = sum(f.calories or 0 for f in food_data)
    total_carbs = sum(f.carbs or 0 for f in food_data)
    meal_types = [f.type for f in food_data]
    
    food_metrics = {
        "total_meals": len(food_data),
        "avg_daily_calories": round(total_calories / days, 1) if days > 0 else 0,
        "avg_daily_carbs": round(total_carbs / days, 1) if days > 0 else 0,
        "breakfast_count": meal_types.count("아침"),
        "lunch_count": meal_types.count("점심"),
        "dinner_count": meal_types.count("저녁"),
        "snack_count": meal_types.count("간식") + meal_types.count("야식"),
        "irregular_meals": len([d for d in set(f.date for f in food_data) 
                               if len([f for f in food_data if f.date == d]) < 3])
    }
    
    # 운동 지표 계산
    total_exercise_minutes = sum(e.exercise_duration or 0 for e in exercise_data)
    exercise_days = len(set(e.exercise_date for e in exercise_data))
    exercise_types = [e.exercise_name for e in exercise_data]
    
    exercise_metrics = {
        "total_exercise_sessions": len(exercise_data),
        "total_exercise_minutes": total_exercise_minutes,
        "avg_daily_exercise": round(total_exercise_minutes / days, 1) if days > 0 else 0,
        "exercise_days": exercise_days,
        "exercise_consistency": round((exercise_days / days) * 100, 1) if days > 0 else 0,
        "most_common_exercise": max(set(exercise_types), key=exercise_types.count) if exercise_types else "없음",
        "cardio_count": len([e for e in exercise_data if e.exercise_name in ["달리기", "걷기", "자전거", "수영"]]),
        "strength_count": len([e for e in exercise_data if e.exercise_name in ["헬스", "웨이트", "근력운동"]])
    }
    
    return {
        "period": f"{start_date} ~ {end_date}",
        "glucose_metrics": glucose_metrics,
        "food_metrics": food_metrics,
        "exercise_metrics": exercise_metrics,
        "patterns": patterns
    }


def analyze_patterns(glucose_data, food_data, exercise_data):
    """혈당, 음식, 운동 데이터에서 패턴 감지"""
    patterns = []
    
    # 혈당 패턴 분석
    if glucose_data:
        glucose_values = [g.glucose_mg_dl for g in glucose_data]
        avg_glucose = sum(glucose_values) / len(glucose_values)
        
        # 고혈당 패턴
        high_glucose_count = len([g for g in glucose_values if g > 140])
        if high_glucose_count > len(glucose_values) * 0.3:  # 30% 이상이 고혈당
            patterns.append(f"고혈당 빈도가 높습니다 (전체의 {high_glucose_count/len(glucose_values)*100:.1f}%)")
        
        # 저혈당 패턴
        low_glucose_count = len([g for g in glucose_values if g < 70])
        if low_glucose_count > 0:
            patterns.append(f"저혈당 발생 {low_glucose_count}회 감지")
        
        # 혈당 변동성
        if len(glucose_values) > 1:
            glucose_range = max(glucose_values) - min(glucose_values)
            if glucose_range > 100:
                patterns.append(f"혈당 변동성이 큽니다 (범위: {glucose_range:.0f}mg/dL)")
    
    # 식사 패턴 분석
    if food_data:
        # 야식 패턴
        late_night_foods = [f for f in food_data if f.time and int(f.time.split(':')[0]) >= 21]
        if late_night_foods:
            patterns.append(f"야식 섭취 {len(late_night_foods)}회 감지")
        
        # 불규칙한 식사 패턴
        daily_meals = {}
        for f in food_data:
            daily_meals[f.date] = daily_meals.get(f.date, 0) + 1
        
        irregular_days = len([d for d, count in daily_meals.items() if count < 3])
        if irregular_days > 0:
            patterns.append(f"불규칙한 식사 {irregular_days}일 감지")
        
        # 고칼로리 패턴
        high_calorie_foods = [f for f in food_data if f.calories and f.calories > 500]
        if high_calorie_foods:
            patterns.append(f"고칼로리 식사 {len(high_calorie_foods)}회 감지")
    
    # 운동 패턴 분석
    if exercise_data:
        # 운동 일관성
        exercise_days = len(set(e.exercise_date for e in exercise_data))
        total_days = len(set(g.date for g in glucose_data)) if glucose_data else 7
        consistency = (exercise_days / total_days) * 100 if total_days > 0 else 0
        
        if consistency < 50:
            patterns.append(f"운동 일관성이 낮습니다 ({consistency:.1f}%)")
        elif consistency >= 80:
            patterns.append(f"운동 일관성이 훌륭합니다 ({consistency:.1f}%)")
        
        # 운동 강도 패턴
        total_exercise_time = sum(e.exercise_duration or 0 for e in exercise_data)
        avg_daily_exercise = total_exercise_time / total_days if total_days > 0 else 0
        
        if avg_daily_exercise < 20:
            patterns.append("운동량이 부족합니다")
        elif avg_daily_exercise > 60:
            patterns.append("운동량이 충분합니다")
    
    # 상관관계 패턴 (간단한 예시)
    if glucose_data and food_data:
        # 야식 후 다음날 아침 혈당 패턴 (간단한 예시)
        late_night_dates = set(f.date for f in food_data if f.time and int(f.time.split(':')[0]) >= 21)
        morning_glucose_after_late_night = []
        morning_glucose_normal = []
        
        for g in glucose_data:
            if g.time and int(g.time.split(':')[0]) < 10:  # 아침 시간대
                prev_date = (datetime.strptime(g.date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
                if prev_date in late_night_dates:
                    morning_glucose_after_late_night.append(g.glucose_mg_dl)
                else:
                    morning_glucose_normal.append(g.glucose_mg_dl)
        
        if morning_glucose_after_late_night and morning_glucose_normal:
            avg_after_late_night = sum(morning_glucose_after_late_night) / len(morning_glucose_after_late_night)
            avg_normal = sum(morning_glucose_normal) / len(morning_glucose_normal)
            if avg_after_late_night > avg_normal + 20:
                patterns.append(f"야식 후 다음날 아침 혈당이 평균 {avg_after_late_night - avg_normal:.0f}mg/dL 높습니다")
    
    return patterns


def analyze_habits(metrics: dict):
    """생활 습관을 종합 분석하여 코칭 제공"""
    from app.utils.io import load_text
    
    # 프롬프트 파일 로드
    base_prompt = load_text("prompts/habit_quest.txt")
    
    prompt = f"""
    {base_prompt}

    다음은 사용자의 최근 생활 습관 데이터입니다. 위 가이드라인에 따라 종합 분석하여 개인화된 생활 습관 코칭을 제공해주세요.

    분석 기간: {metrics['period']}

    혈당 지표:
    - 총 측정 횟수: {metrics['glucose_metrics']['total_readings']}회
    - 평균 혈당: {metrics['glucose_metrics']['avg_glucose']} mg/dL
    - 최고 혈당: {metrics['glucose_metrics']['max_glucose']} mg/dL
    - 최저 혈당: {metrics['glucose_metrics']['min_glucose']} mg/dL
    - 고혈당 일수: {metrics['glucose_metrics']['high_glucose_days']}일
    - 저혈당 일수: {metrics['glucose_metrics']['low_glucose_days']}일

    음식 지표:
    - 총 식사 횟수: {metrics['food_metrics']['total_meals']}회
    - 일평균 칼로리: {metrics['food_metrics']['avg_daily_calories']} kcal
    - 일평균 탄수화물: {metrics['food_metrics']['avg_daily_carbs']} g
    - 아침 식사: {metrics['food_metrics']['breakfast_count']}회
    - 점심 식사: {metrics['food_metrics']['lunch_count']}회
    - 저녁 식사: {metrics['food_metrics']['dinner_count']}회
    - 간식/야식: {metrics['food_metrics']['snack_count']}회
    - 불규칙한 식사 일수: {metrics['food_metrics']['irregular_meals']}일

    운동 지표:
    - 총 운동 횟수: {metrics['exercise_metrics']['total_exercise_sessions']}회
    - 총 운동 시간: {metrics['exercise_metrics']['total_exercise_minutes']}분
    - 일평균 운동 시간: {metrics['exercise_metrics']['avg_daily_exercise']}분
    - 운동한 날: {metrics['exercise_metrics']['exercise_days']}일
    - 운동 일관성: {metrics['exercise_metrics']['exercise_consistency']}%
    - 가장 많이 한 운동: {metrics['exercise_metrics']['most_common_exercise']}
    - 유산소 운동: {metrics['exercise_metrics']['cardio_count']}회
    - 근력 운동: {metrics['exercise_metrics']['strength_count']}회

    감지된 패턴:
    {chr(10).join(f"- {pattern}" for pattern in metrics['patterns']) if metrics['patterns'] else "- 특별한 패턴이 감지되지 않았습니다"}

    위 가이드라인에 따라 감지된 패턴을 바탕으로 개인화된 코칭을 제공해주세요.
    """
    
    try:
        response = call_openai_api(prompt)
        
        # JSON 변환 시도 (마크다운 코드 블록 처리)
        try:
            # 마크다운 코드 블록에서 JSON 추출
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            result_json = json.loads(json_str)
        except json.JSONDecodeError as e:
            # JSON 파싱 실패 시 기본 응답 구조로 반환
            result_json = {
                "result": {
                    "종합 건강 점수": "분석 중 오류가 발생했습니다",
                    "혈당 관리": "데이터 분석에 문제가 있어 정확한 코칭을 제공할 수 없습니다.",
                    "식사 습관": "데이터 분석에 문제가 있어 정확한 코칭을 제공할 수 없습니다.",
                    "운동 습관": "데이터 분석에 문제가 있어 정확한 코칭을 제공할 수 없습니다.",
                    "패턴 감지": "패턴 분석 중 오류가 발생했습니다.",
                    "우선 개선사항": "정확한 분석을 위해 더 많은 데이터가 필요합니다.",
                    "주간 목표": "규칙적인 생활 패턴 유지, 데이터 기록 지속, 건강한 습관 형성",
                    "건강 팁": "정기적으로 혈당, 식사, 운동을 기록하여 더 정확한 분석을 받아보세요."
                }
            }
            print(f"JSON 파싱 오류: {e}")
            print(f"원본 응답: {response}")
        
        # JSON 직렬화 시 순서 보장을 위해 ensure_ascii=False와 sort_keys=False 사용
        return result_json
    except Exception as e:
        return {"error": str(e)}
