import json
from app.ai import call_openai_api


def calculate_food_metrics(data):
    """
    음식 및 운동 기록 데이터를 분석하여 지표를 계산
    """
    if not isinstance(data, dict) or "records" not in data:
        return {"error": "올바르지 않은 기록 데이터 형식입니다."}
    
    records = data["records"]
    if not records:
        return {"error": "기록 데이터가 없습니다."}
    
    total_meals = 0
    total_calories = 0
    high_sugar_foods = 0
    late_night_snacks = 0
    irregular_meals = 0
    total_exercise_minutes = 0
    exercise_sessions = 0
    recorded_days = len(records)
    
    # 고당분 음식 키워드
    high_sugar_keywords = ["사탕", "초콜릿", "케이크", "아이스크림", "콜라", "사이다", "주스", "시럽", "꿀", "설탕"]
    
    for record in records:
        if "food" not in record:
            continue
            
        food_records = record["food"]
        daily_meals = len(food_records)
        total_meals += daily_meals
        
        # 불규칙한 식사 체크 (하루 3회 미만)
        if daily_meals < 3:
            irregular_meals += 1
        
        for meal in food_records:
            if "items" not in meal:
                continue
                
            meal_time = meal.get("time", "")
            meal_type = meal.get("meal", "")
            
            # 늦은 시간 간식 체크 (21시 이후)
            if meal_type == "간식" and meal_time:
                try:
                    hour = int(meal_time.split(":")[0])
                    if hour >= 21:
                        late_night_snacks += 1
                except:
                    pass
            
            for item in meal["items"]:
                item_name = item.get("name", "").lower()
                calories = item.get("calories", 0)
                total_calories += calories
                
                # 고당분 음식 체크
                for keyword in high_sugar_keywords:
                    if keyword in item_name:
                        high_sugar_foods += 1
                        break
        
        # 운동 데이터 처리
        if "exercise" in record:
            exercise_records = record["exercise"]
            for exercise in exercise_records:
                total_exercise_minutes += exercise.get("duration", 0)
                if exercise.get("duration", 0) > 0:
                    exercise_sessions += 1
    
    avg_calories = total_calories / recorded_days if recorded_days > 0 else 0
    record_completeness = (total_meals / (recorded_days * 3)) * 100 if recorded_days > 0 else 0
    avg_exercise_minutes = total_exercise_minutes / recorded_days if recorded_days > 0 else 0
    
    return {
        "total_meals": total_meals,
        "avg_calories": round(avg_calories, 1),
        "high_sugar_foods": high_sugar_foods,
        "late_night_snacks": late_night_snacks,
        "irregular_meals": irregular_meals,
        "record_completeness": round(record_completeness, 1),
        "total_exercise_minutes": total_exercise_minutes,
        "exercise_sessions": exercise_sessions,
        "avg_exercise_minutes": round(avg_exercise_minutes, 1)
    }


def analyze_food(metrics, prompt_text, user_age=None):
    """음식 및 운동 데이터를 분석하여 맞춤 퀘스트를 생성"""
    # 실제 수치를 프롬프트에 추가
    total_meals = metrics.get("total_meals", 0)
    avg_calories = metrics.get("avg_calories", 0)
    high_sugar_foods = metrics.get("high_sugar_foods", 0)
    late_night_snacks = metrics.get("late_night_snacks", 0)
    irregular_meals = metrics.get("irregular_meals", 0)
    record_completeness = metrics.get("record_completeness", 0)
    total_exercise_minutes = metrics.get("total_exercise_minutes", 0)
    exercise_sessions = metrics.get("exercise_sessions", 0)
    avg_exercise_minutes = metrics.get("avg_exercise_minutes", 0)
    
    # 프롬프트에 실제 데이터 추가
    data_info = f"""
    
사용자 기록 데이터:
- 총 식사 횟수: {total_meals}회
- 평균 칼로리: {avg_calories}kcal
- 고당분 음식: {high_sugar_foods}회
- 야식: {late_night_snacks}회
- 불규칙한 식사: {irregular_meals}회
- 식사 기록 완성도: {record_completeness}%
- 총 운동 시간: {total_exercise_minutes}분
- 운동 세션: {exercise_sessions}회
- 평균 운동 시간: {avg_exercise_minutes}분

위 데이터를 바탕으로 구체적인 수치를 포함한 퀘스트를 생성해주세요.
"""
    
    formatted_prompt = prompt_text + data_info
    
    # 반말 + 다정한 말투로 통일 (나이 검증 없음)
    tone_instruction = """

🚨 매우 중요: 반말 + 다정한 말투로만 말해주세요! 🚨
존댓말 절대 금지!

✅ 사용해야 할 반말 + 다정한 말투:
- "~해", "~야", "~지", "~어", "~네", "~자"
- "~해보자", "~해보면 좋겠어", "~해보는 건 어때?"
- 예시: "음식을 골고루 먹어보자!", "오늘도 맛있게 먹어!", "조금만 더 신경써!"
- 예시: "건강한 음식 먹어보면 좋겠어!", "규칙적으로 먹어보는 건 어때?", "맛있게 지내자!"

❌ 절대 사용하면 안 되는 존댓말:
- "~해요", "~세요", "~입니다", "~되세요" 등
- 예시: "음식을 골고루 드셔보세요" (X), "오늘도 맛있게 드세요" (X)

⚠️ 주의: 존댓말을 사용하면 안 됩니다! 반말 + 다정한 말투로만 작성하세요!"""
    
    # 반말 + 다정한 말투 강제 변환
    final_instruction = """

🔥🔥🔥 최종 지시사항 🔥🔥🔥
반드시 반말 + 다정한 말투로만 작성하세요!

❌ 금지: "~해요", "~세요", "~입니다", "~되세요"
✅ 필수: "~해", "~야", "~지", "~어", "~자", "~해보자", "~해보면 좋겠어"

예시 변환:
- "도전해보세요" → "도전해보자"
- "드셔보세요" → "먹어보자"  
- "해보세요" → "해보자"
- "걸어보세요" → "걸어보자"
- "관리해보세요" → "관리해보자"
- "노력해보세요" → "노력해보자"

모든 문장을 반말 + 다정한 말투로 변환하여 작성하세요!"""
    
    full_prompt = f"{formatted_prompt}{tone_instruction}\n\n음식 기록 데이터 지표:\n{json.dumps(metrics, ensure_ascii=False, indent=2)}\n\n{final_instruction}"
    
    try:
        response = call_openai_api(full_prompt)
        
        # JSON 변환 시도
        try:
            result_json = json.loads(response)
        except json.JSONDecodeError:
            result_json = {
                "error": "GPT가 올바른 JSON을 반환하지 않았습니다.",
                "text": response
            }
        
        return result_json
    except Exception as e:
        return {"error": str(e)}
