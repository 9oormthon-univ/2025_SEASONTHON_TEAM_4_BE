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


def analyze_food(metrics, prompt_text):
    """음식 데이터를 분석하여 맞춤 퀘스트를 생성"""
    full_prompt = f"{prompt_text}\n\n음식 기록 데이터 지표:\n{json.dumps(metrics, ensure_ascii=False, indent=2)}"
    
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
