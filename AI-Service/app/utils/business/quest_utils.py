"""퀘스트 관련 유틸리티 함수들"""

import json
import random
from app.core.ai import call_openai_api
from app.utils.common import load_text


def generate_llm_quests(glucose_metrics, member_info=None, member_id=None, use_rag=False):
    """기본 LLM을 사용하여 개인화된 퀘스트 생성"""
    try:
        # 기본 LLM 퀘스트 생성 방식
        return generate_basic_llm_quests(glucose_metrics, member_info)
        
    except Exception as e:
        print(f"퀘스트 생성 오류: {e}")
        return get_fallback_quests(glucose_metrics)




def generate_basic_llm_quests(glucose_metrics, member_info):
    """기본 LLM 퀘스트 생성"""
    try:
        # 프롬프트 로드
        prompt_text = load_text("app/prompts/quest_generation_prompt.txt")
        
        # 프롬프트에 실제 데이터 치환
        avg_glucose = glucose_metrics.get('average_glucose', 120)
        max_glucose = glucose_metrics.get('max_glucose', 180)
        min_glucose = glucose_metrics.get('min_glucose', 80)
        spike_count = glucose_metrics.get('spike_count', 0)
        measurement_count = glucose_metrics.get('measurement_count', 0)
        
        formatted_prompt = prompt_text.replace("{{average_glucose}}", str(round(avg_glucose, 1)))
        formatted_prompt = formatted_prompt.replace("{{max_glucose}}", str(round(max_glucose, 1)))
        formatted_prompt = formatted_prompt.replace("{{min_glucose}}", str(round(min_glucose, 1)))
        formatted_prompt = formatted_prompt.replace("{{spike_count}}", str(spike_count))
        formatted_prompt = formatted_prompt.replace("{{measurement_count}}", str(measurement_count))
        
        # LLM 호출
        system_prompt = "당신은 당뇨 관리 전문가입니다. 반드시 JSON 형식으로만 응답하고, 반말 + 다정한 말투를 사용하세요."
        ai_response = call_openai_api(formatted_prompt, system_prompt)
        
        # JSON 파싱
        try:
            result = json.loads(ai_response)
            if "result" in result and isinstance(result["result"], dict):
                return result["result"]
        except json.JSONDecodeError:
            pass
        
        # LLM 실패 시 기본 퀘스트 반환
        return get_fallback_quests(glucose_metrics)
        
    except Exception as e:
        print(f"기본 LLM 퀘스트 생성 오류: {e}")
        return get_fallback_quests(glucose_metrics)




def get_fallback_quests(glucose_metrics):
    """LLM 실패 시 사용할 기본 퀘스트들"""
    avg_glucose = glucose_metrics.get('average_glucose', 120)
    max_glucose = glucose_metrics.get('max_glucose', 180)
    spike_count = glucose_metrics.get('spike_count', 0)
    
    quests = {}
    
    # 혈당 상태에 따른 기본 퀘스트
    if avg_glucose > 140:
        quests["혈당 안정화 퀘스트"] = f"현재 평균 {avg_glucose:.0f}mg/dL로 높아! 물을 하루 8잔 마셔서 혈당을 안정시켜보자"
    elif avg_glucose > 120:
        quests["혈당 유지 퀘스트"] = f"현재 평균 {avg_glucose:.0f}mg/dL로 양호해! 이 상태를 계속 유지해보자"
    else:
        quests["혈당 관리 우수 퀘스트"] = f"현재 평균 {avg_glucose:.0f}mg/dL로 아주 좋아! 이 우수한 관리를 계속해보자"
    
    if max_glucose > 180:
        quests["최고 혈당 관리 퀘스트"] = f"최고 혈당이 {max_glucose:.0f}mg/dL로 높아! 식사 후 가벼운 산책으로 혈당을 낮춰보자"
    else:
        quests["최고 혈당 유지 퀘스트"] = f"최고 혈당이 {max_glucose:.0f}mg/dL로 안정적이야! 이 상태를 계속 유지해보자"
    
    if spike_count > 2:
        quests["혈당 스파이크 방지 퀘스트"] = f"오늘 {spike_count}번의 급상승이 있었어! 심호흡 5회로 스트레스를 줄여보자"
    else:
        quests["혈당 안정 챌린지 퀘스트"] = f"혈당이 안정적이야! 규칙적인 생활로 이 상태를 유지해보자"
    
    # 추가 생활 습관 퀘스트
    quests["수분 섭취 퀘스트"] = "혈당 관리를 위해 하루 8잔 이상 물 마셔보자"
    
    return quests


def select_quests_from_pool(quest_pool, count=4):
    """퀘스트 풀에서 지정된 개수만큼 선택"""
    quest_items = list(quest_pool.items())
    
    if len(quest_items) <= count:
        return dict(quest_items)
    
    # 랜덤하게 선택
    selected = random.sample(quest_items, count)
    return dict(selected)
