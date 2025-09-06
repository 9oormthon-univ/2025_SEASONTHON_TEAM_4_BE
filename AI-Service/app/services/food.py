import json
from app.ai import call_openai_api


def calculate_food_metrics(data):
    """
    음식 기록 데이터를 분석하여 지표를 계산
    """
    if not isinstance(data, dict) or "records" not in data:
        return {"error": "올바르지 않은 음식 기록 데이터 형식입니다."}
    
    records = data["records"]
    if not records:
        return {"error": "음식 기록 데이터가 없습니다."}
    
    total_meals = 0
    total_calories = 0
    high_sugar_foods = 0
    late_night_snacks = 0
    irregular_meals = 0
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
    
    avg_calories = total_calories / recorded_days if recorded_days > 0 else 0
    record_completeness = (total_meals / (recorded_days * 3)) * 100 if recorded_days > 0 else 0
    
    return {
        "total_meals": total_meals,
        "avg_calories": round(avg_calories, 1),
        "high_sugar_foods": high_sugar_foods,
        "late_night_snacks": late_night_snacks,
        "irregular_meals": irregular_meals,
        "record_completeness": round(record_completeness, 1)
    }


def analyze_food(metrics, prompt_text, user_age=None):
    """음식 데이터를 분석하여 맞춤 퀘스트를 생성"""
    # 템플릿 변수를 실제 값으로 치환
    formatted_prompt = prompt_text.format(
        total_meals=metrics.get("total_meals", 0),
        avg_calories=metrics.get("avg_calories", 0),
        high_sugar_foods=metrics.get("high_sugar_foods", 0),
        late_night_snacks=metrics.get("late_night_snacks", 0),
        irregular_meals=metrics.get("irregular_meals", 0),
        record_completeness=metrics.get("record_completeness", 0)
    )
    
    # 나이 기반 말투 조정 - 조건문으로 판단하여 프롬프트 추가
    if user_age is not None and user_age < 10:
        # 어린이용 반말 프롬프트 추가
        tone_instruction = f"""

🚨 매우 중요: 사용자가 {user_age}세 어린이입니다! 🚨
반드시 반말로만 말해주세요. 존댓말 절대 금지!

✅ 사용해야 할 반말:
- "~해", "~야", "~지", "~어", "~네", "~자"
- 예시: "음식을 골고루 먹어보자!", "오늘도 맛있게 먹어!", "조금만 더 신경써!"

❌ 절대 사용하면 안 되는 존댓말:
- "~해요", "~세요", "~입니다", "~되세요" 등
- 예시: "음식을 골고루 드셔보세요" (X), "오늘도 맛있게 드세요" (X)

⚠️ 주의: 존댓말을 사용하면 안 됩니다! 반말로만 작성하세요!"""
    else:
        # 성인용 존댓말 프롬프트 추가
        tone_instruction = f"""

🚨 매우 중요: 사용자에게 존댓말로만 말해주세요! 🚨
반말 절대 금지!

✅ 사용해야 할 존댓말:
- "~해요", "~세요", "~입니다", "~되세요"
- 예시: "음식을 골고루 드셔보세요!", "오늘도 맛있게 드세요!", "조금만 더 신경써주세요!"

❌ 절대 사용하면 안 되는 반말:
- "~해", "~야", "~지", "~어", "~네" 등
- 예시: "음식을 골고루 먹어보자" (X), "오늘도 맛있게 먹어" (X)

⚠️ 주의: 반말을 사용하면 안 됩니다! 존댓말로만 작성하세요!"""
    
    # 나이에 따른 강제 말투 변환
    if user_age is not None and user_age < 10:
        # 어린이용 - 반말 강제
        final_instruction = f"""

🔥🔥🔥 최종 지시사항 🔥🔥🔥
사용자 나이: {user_age}세 (어린이)
반드시 반말로만 작성하세요!

❌ 금지: "~해요", "~세요", "~입니다", "~되세요"
✅ 필수: "~해", "~야", "~지", "~어", "~자"

예시 변환:
- "도전해보세요" → "도전해보자"
- "드셔보세요" → "먹어보자"  
- "해보세요" → "해보자"
- "걸어보세요" → "걸어보자"

모든 문장을 반말로 변환하여 작성하세요!"""
    else:
        # 성인용 - 존댓말 강제
        final_instruction = f"""

🔥🔥🔥 최종 지시사항 🔥🔥🔥
사용자 나이: {user_age if user_age else '알 수 없음'}세 (성인)
반드시 존댓말로만 작성하세요!

❌ 금지: "~해", "~야", "~지", "~어", "~자"
✅ 필수: "~해요", "~세요", "~입니다", "~되세요"

예시 변환:
- "도전해보자" → "도전해보세요"
- "먹어보자" → "드셔보세요"
- "해보자" → "해보세요"
- "걸어보자" → "걸어보세요"

모든 문장을 존댓말로 변환하여 작성하세요!"""
    
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
