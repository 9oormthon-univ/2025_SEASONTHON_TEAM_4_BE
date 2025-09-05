import json
from app.ai import call_openai_api


def calculate_glucose_metrics(data):
    """
    data는 {"cgm_data": {"readings": [{"time": "2025-09-03T08:00", "glucose_mg_dl": 95}, ...]}} 형식
    """
    if not isinstance(data, dict) or "cgm_data" not in data:
        return {"error": "올바르지 않은 혈당 데이터 형식입니다."}
    
    readings = data.get("cgm_data", {}).get("readings", [])
    if not readings:
        return {"error": "혈당 데이터가 없습니다."}
    
    glucose_values = [reading.get("glucose_mg_dl") for reading in readings if reading.get("glucose_mg_dl") is not None]
    
    if not glucose_values:
        return {"error": "혈당 데이터가 없습니다."}
    
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


def analyze_glucose(metrics, prompt_text):
    """혈당 데이터를 분석하여 맞춤 퀘스트를 생성"""
    full_prompt = f"{prompt_text}\n\n혈당 데이터 지표:\n{json.dumps(metrics, ensure_ascii=False, indent=2)}"
    
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
