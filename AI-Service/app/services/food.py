import json
from app.ai import chat_complete


def calculate_food_metrics(data):
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

    high_sugar_keywords = ["사탕", "초콜릿", "케이크", "아이스크림", "콜라", "사이다", "주스", "시럽", "꿀", "설탕"]

    for record in records:
        if "food" not in record:
            continue
        food_records = record["food"]
        daily_meals = len(food_records)
        total_meals += daily_meals
        if daily_meals < 3:
            irregular_meals += 1
        for meal in food_records:
            if "items" not in meal:
                continue
            meal_time = meal.get("time", "")
            meal_type = meal.get("meal", "")
            if meal_type == "간식" and meal_time:
                try:
                    hour = int(meal_time.split(":")[0])
                    if hour >= 21:
                        late_night_snacks += 1
                except:
                    pass
            for item in meal["items"]:
                name = item.get("name", "")
                calories = item.get("calories", 0)
                total_calories += calories
                if any(k in name for k in high_sugar_keywords):
                    high_sugar_foods += 1

    avg_calories = total_calories / recorded_days if recorded_days > 0 else 0
    record_completeness = (total_meals / (recorded_days * 3)) * 100 if recorded_days > 0 else 0

    return {
        "total_meals": total_meals,
        "avg_calories": round(avg_calories, 1),
        "high_sugar_foods": high_sugar_foods,
        "late_night_snacks": late_night_snacks,
        "irregular_meals": irregular_meals,
        "record_completeness": round(record_completeness, 1),
    }


def analyze_food(data, prompt_text):
    metrics = calculate_food_metrics(data)
    user_prompt = (
        f"{prompt_text}\n\n음식 기록 데이터 지표:\n"
        f"{json.dumps(metrics, ensure_ascii=False, indent=2)}\n\n원본 데이터:\n"
        f"{json.dumps(data, ensure_ascii=False, indent=2)}"
    )
    answer_text = chat_complete(
        system_prompt="너는 영양 및 식사 습관 관리 전문가야.",
        user_prompt=user_prompt,
    )
    try:
        return json.loads(answer_text)
    except json.JSONDecodeError:
        return {"error": "GPT가 올바른 JSON을 반환하지 않았습니다.", "text": answer_text}


