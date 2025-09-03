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
def load_json_data(file_path="data/mock.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": f"{file_path} 파일이 존재하지 않습니다."}
    except json.JSONDecodeError:
        return {"error": f"{file_path} 파일의 JSON 형식이 올바르지 않습니다."}

def load_prompt(file_path="daily_quest.txt"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "데이터를 분석해 혈당 건강 퀘스트를 생성해 주세요."

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

# =========================
# 앱 실행
# =========================
if __name__ == "__main__":
    app.run(port=5000, debug=True)
