import json
from app.core.ai import call_openai_api
from app.services.chroma_rag_service import get_chroma_rag_service


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


def analyze_glucose(metrics, prompt_text, user_age=None, member_id=None, use_rag=True, analysis_type="child"):
    """혈당 데이터를 분석하여 맞춤 퀘스트를 생성 (Hugging Face RAG 지원)"""
    
    # RAG 사용 여부에 따른 분석 방식 선택
    if use_rag and member_id:
        try:
            # ChromaDB RAG 기반 분석
            rag_service = get_chroma_rag_service()
            return rag_service.generate_rag_enhanced_analysis(metrics, member_id, analysis_type)
        except Exception as e:
            print(f"RAG 분석 실패, 기본 분석으로 전환: {e}")
            # RAG 실패 시 기본 분석으로 fallback
    
    # 기본 분석 방식 (기존 로직)
    # 템플릿 변수를 실제 값으로 치환 (프롬프트의 (n) 형식에 맞춰)
    avg_glucose = metrics.get("average_glucose", 0)
    max_glucose = metrics.get("max_glucose", 0)
    min_glucose = metrics.get("min_glucose", 0)
    spike_count = metrics.get("spike_count", 0)
    health_index = metrics.get("health_index", 0)
    
    # 목표 범위 계산 (평균 ± 20)
    target_min = max(70, int(avg_glucose - 20))
    target_max = int(avg_glucose + 20)
    
    # 프롬프트의 (n) 부분을 실제 수치로 치환 (순서 중요!)
    formatted_prompt = prompt_text.replace("(n)~(n)", f"{target_min}~{target_max}")
    formatted_prompt = formatted_prompt.replace("(n)%", "20%")  # 탄수화물 감소 비율
    formatted_prompt = formatted_prompt.replace("(n)잔", "3잔")  # 수분 보충
    formatted_prompt = formatted_prompt.replace("(n)분", "10분")  # 운동 시간
    formatted_prompt = formatted_prompt.replace("(n)회", "5회")  # 심호흡 횟수
    formatted_prompt = formatted_prompt.replace("(n)", str(int(avg_glucose)))  # 마지막에 단일 (n) 치환
    
    # 반말 + 다정한 말투로 통일 (나이 검증 없음)
    tone_instruction = """

매우 중요: 반말 + 다정한 말투로만 말해주세요!
존댓말 절대 금지!

사용해야 할 반말 + 다정한 말투:
- "~해", "~야", "~지", "~어", "~네", "~자"
- "~해보자", "~해보면 좋겠어", "~해보는 건 어때?"
- 예시: "혈당을 잘 관리해보자!", "오늘도 화이팅이야!", "조금만 더 노력해!"
- 예시: "산책해보면 좋겠어!", "운동해보는 건 어때?", "건강하게 지내자!"

절대 사용하면 안 되는 존댓말:
- "~해요", "~세요", "~입니다", "~되세요" 등
- 예시: "혈당을 잘 관리해보세요" (X), "오늘도 화이팅이에요" (X)

주의: 존댓말을 사용하면 안 됩니다! 반말 + 다정한 말투로만 작성하세요!"""
    
    # 반말 + 다정한 말투 강제 변환
    final_instruction = """

최종 지시사항
반드시 반말 + 다정한 말투로만 작성하세요!

금지: "~해요", "~세요", "~입니다", "~되세요"
필수: "~해", "~야", "~지", "~어", "~자", "~해보자", "~해보면 좋겠어"

예시 변환:
- "도전해보세요" → "도전해보자"
- "유지해보세요" → "유지해보자"  
- "해보세요" → "해보자"
- "걸어보세요" → "걸어보자"
- "관리해보세요" → "관리해보자"
- "노력해보세요" → "노력해보자"

모든 문장을 반말 + 다정한 말투로 변환하여 작성하세요!"""
    
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
