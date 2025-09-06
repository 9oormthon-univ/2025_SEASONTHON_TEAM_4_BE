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


def analyze_glucose(metrics, prompt_text, user_age=None):
    """혈당 데이터를 분석하여 맞춤 퀘스트를 생성"""
    # 템플릿 변수를 실제 값으로 치환
    formatted_prompt = prompt_text.format(
        average_glucose=metrics.get("average_glucose", 0),
        max_glucose=metrics.get("max_glucose", 0),
        min_glucose=metrics.get("min_glucose", 0),
        spike_count=metrics.get("spike_count", 0),
        health_index=metrics.get("health_index", 0)
    )
    
    # 나이 기반 말투 조정 - 조건문으로 판단하여 프롬프트 추가
    if user_age is not None and user_age < 10:
        # 어린이용 반말 프롬프트 추가
        tone_instruction = f"""

🚨 매우 중요: 사용자가 {user_age}세 어린이입니다! 🚨
반드시 반말로만 말해주세요. 존댓말 절대 금지!

✅ 사용해야 할 반말:
- "~해", "~야", "~지", "~어", "~네", "~자"
- 예시: "혈당을 잘 관리해보자!", "오늘도 화이팅이야!", "조금만 더 노력해!"

❌ 절대 사용하면 안 되는 존댓말:
- "~해요", "~세요", "~입니다", "~되세요" 등
- 예시: "혈당을 잘 관리해보세요" (X), "오늘도 화이팅이에요" (X)

⚠️ 주의: 존댓말을 사용하면 안 됩니다! 반말로만 작성하세요!"""
    else:
        # 성인용 존댓말 프롬프트 추가
        tone_instruction = f"""

🚨 매우 중요: 사용자에게 존댓말로만 말해주세요! 🚨
반말 절대 금지!

✅ 사용해야 할 존댓말:
- "~해요", "~세요", "~입니다", "~되세요"
- 예시: "혈당을 잘 관리해보세요!", "오늘도 화이팅이에요!", "조금만 더 노력하세요!"

❌ 절대 사용하면 안 되는 반말:
- "~해", "~야", "~지", "~어", "~네" 등
- 예시: "혈당을 잘 관리해보자" (X), "오늘도 화이팅이야" (X)

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
- "유지해보세요" → "유지해보자"  
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
- "유지해보자" → "유지해보세요"
- "해보자" → "해보세요"
- "걸어보자" → "걸어보세요"

모든 문장을 존댓말로 변환하여 작성하세요!"""
    
    full_prompt = f"{formatted_prompt}{tone_instruction}\n\n혈당 데이터 지표:\n{json.dumps(metrics, ensure_ascii=False, indent=2)}\n\n{final_instruction}"
    
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
