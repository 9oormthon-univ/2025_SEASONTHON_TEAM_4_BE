import json
from app.ai import chat_complete


def calculate_glucose_metrics(data):
    glucose_values = [entry["glucose"] for entry in data if "glucose" in entry]
    if not glucose_values:
        return {"error": "혈당 데이터가 없습니다."}

    avg_glucose = sum(glucose_values) / len(glucose_values)
    max_glucose = max(glucose_values)
    min_glucose = min(glucose_values)

    spike_count = 0
    for i in range(1, len(glucose_values)):
        if glucose_values[i] - glucose_values[i - 1] >= 30:
            spike_count += 1

    health_index = max(0, 100 - (avg_glucose - 100) - (spike_count * 5))
    return {
        "average_glucose": round(avg_glucose, 2),
        "max_glucose": max_glucose,
        "min_glucose": min_glucose,
        "spike_count": spike_count,
        "health_index": round(health_index, 2),
    }


def analyze_glucose(data, prompt_text):
    metrics = calculate_glucose_metrics(data)
    user_prompt = (
        f"{prompt_text}\n\n혈당 데이터 지표:\n"
        f"{json.dumps(metrics, ensure_ascii=False, indent=2)}\n\n원본 데이터:\n"
        f"{json.dumps(data, ensure_ascii=False, indent=2)}"
    )

    answer_text = chat_complete(
        system_prompt="너는 혈당 데이터 분석 및 맞춤 퀘스트 전문가야.",
        user_prompt=user_prompt,
    )
    try:
        return json.loads(answer_text)
    except json.JSONDecodeError:
        return {"error": "GPT가 올바른 JSON을 반환하지 않았습니다.", "text": answer_text}


