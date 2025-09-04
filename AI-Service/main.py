from dotenv import load_dotenv
from flask import Flask, jsonify, request
import json
from openai import OpenAI
import os

# =========================
# 환경 변수 로드
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

app = Flask(__name__)

# =========================
# 데이터 읽기
# =========================
def load_json_data(file_path="data/blood_sugar.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": f"{file_path} 파일이 존재하지 않습니다."}
    except json.JSONDecodeError:
        return {"error": f"{file_path} 파일의 JSON 형식이 올바르지 않습니다."}

def load_prompt(file_path="prompts/daily_quest.txt"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "데이터를 분석해 혈당 건강 퀘스트를 생성해 주세요."

def load_food_prompt(file_path="prompts/food_quest.txt"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "음식 기록을 분석해 건강 관리 퀘스트를 생성해 주세요."

# =========================
# 혈당 지표 계산
# =========================
def calculate_glucose_metrics(data):
    """
    data는 [{"time": "2025-09-03T08:00", "glucose": 95}, ...] 형식
    """
    glucose_values = [entry["glucose"] for entry in data if "glucose" in entry]

    if not glucose_values:
        return {
            "error": "혈당 데이터가 없습니다."
        }

    avg_glucose = sum(glucose_values) / len(glucose_values)
    max_glucose = max(glucose_values)
    min_glucose = min(glucose_values)

    # 혈당 스파이크: 이전 값 대비 30 이상 증가한 경우 카운트
    spike_count = 0
    for i in range(1, len(glucose_values)):
        if glucose_values[i] - glucose_values[i-1] >= 30:
            spike_count += 1

    # 혈당 건강 지수: 예시로 평균과 스파이크 기반 간단 계산
    health_index = max(0, 100 - (avg_glucose - 100) - (spike_count * 5))

    return {
        "average_glucose": round(avg_glucose, 2),
        "max_glucose": max_glucose,
        "min_glucose": min_glucose,
        "spike_count": spike_count,
        "health_index": round(health_index, 2)
    }

# =========================
# 음식 기록 분석
# =========================
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

def analyze_food_data(data, prompt_text):
    metrics = calculate_food_metrics(data)
    full_prompt = f"{prompt_text}\n\n음식 기록 데이터 지표:\n{json.dumps(metrics, ensure_ascii=False, indent=2)}\n\n원본 데이터:\n{json.dumps(data, ensure_ascii=False, indent=2)}"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "너는 영양 및 식사 습관 관리 전문가야."},
                {"role": "user", "content": full_prompt}
            ]
        )

        answer_text = response.choices[0].message.content

        # analyze_data와 동일한 단순 JSON 파싱
        try:
            result_json = json.loads(answer_text)
        except json.JSONDecodeError:
            result_json = {
                "error": "GPT가 올바른 JSON을 반환하지 않았습니다.",
                "text": answer_text
            }

        return result_json
    except Exception as e:
        return {"error": str(e)}

# =========================
# OpenAI 요청
# =========================
def analyze_data(data, prompt_text):
    metrics = calculate_glucose_metrics(data)
    full_prompt = f"{prompt_text}\n\n혈당 데이터 지표:\n{json.dumps(metrics, ensure_ascii=False, indent=2)}\n\n원본 데이터:\n{json.dumps(data, ensure_ascii=False, indent=2)}"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "너는 혈당 데이터 분석 및 맞춤 퀘스트 전문가야."},
                {"role": "user", "content": full_prompt}
            ]
        )

        answer_text = response.choices[0].message.content

        # JSON 변환 시도
        try:
            result_json = json.loads(answer_text)
        except json.JSONDecodeError:
            result_json = {
                "error": "GPT가 올바른 JSON을 반환하지 않았습니다.",
                "text": answer_text
            }

        return result_json
    except Exception as e:
        return {"error": str(e)}

# =========================
# Flask 라우트
# =========================
@app.route("/analyze", methods=["GET", "POST"])
def analyze_endpoint():
    if request.method == "POST":
        data = request.json or []
    else:
        data = load_json_data()
        if "error" in data:
            return jsonify({"result": data})

    prompt_text = load_prompt()
    analysis_result = analyze_data(data, prompt_text)
    return jsonify({"result": analysis_result})

@app.route("/food-analyze", methods=["GET", "POST"])
def food_analyze_endpoint():
    if request.method == "POST":
        data = request.json or {}
    else:
        data = load_json_data("data/daily_food_log.json")
        if "error" in data:
            return jsonify({"result": data})

    prompt_text = load_food_prompt()
    analysis_result = analyze_food_data(data, prompt_text)
    return jsonify({"result": analysis_result})

# =========================
# 앱 실행
# =========================
if __name__ == "__main__":
    app.run(port=5000, debug=True)