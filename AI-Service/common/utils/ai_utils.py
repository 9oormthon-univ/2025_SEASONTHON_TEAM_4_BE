"""AI 관련 유틸리티 함수들"""

import json
import re
from common.ai import call_openai_api
from common.utils.io import load_text


def format_analyze_prompt(prompt, avg_glucose, max_glucose, min_glucose, spike_count, measurement_count):
    """분석 프롬프트에 실제 데이터 포맷팅"""
    formatted_prompt = prompt.replace("{{avg_glucose}}", str(round(avg_glucose, 1) if avg_glucose > 0 else 0))
    formatted_prompt = formatted_prompt.replace("{{max_glucose}}", str(round(max_glucose, 1) if max_glucose > 0 else 0))
    formatted_prompt = formatted_prompt.replace("{{min_glucose}}", str(round(min_glucose, 1) if min_glucose > 0 else 0))
    formatted_prompt = formatted_prompt.replace("{{spike_count}}", str(spike_count))
    formatted_prompt = formatted_prompt.replace("{{measurement_count}}", str(measurement_count))
    return formatted_prompt


def extract_json_from_ai_response(ai_response):
    """AI 응답에서 JSON 추출"""
    try:
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        else:
            raise json.JSONDecodeError("No JSON found", ai_response, 0)
    except (json.JSONDecodeError, AttributeError):
        return None


def get_default_analysis_result(glucose_values, avg_glucose, max_glucose, spike_count):
    """AI 분석 실패 시 기본 응답 반환"""
    return {
        "result": {
            "혈당 스파이크": "오늘은 혈당 측정 기록이 없어요 정기적인 혈당 체크로 건강을 관리해보세요!" if not glucose_values else (
                "오늘은 급상승이 없었어요! 안정적인 하루였네요" if spike_count == 0 else
                f"오늘 {spike_count}번의 급상승이 있었어요 식사 후 혈당 관리를 더 신경써보세요!" if spike_count == 1 else
                f"오늘 {spike_count}번의 급상승이 있었어요 식사량과 탄수화물 섭취를 조절해보세요!"
            ),
            "평균 혈당": ["혈당 측정 기록이 없어 평균을 계산할 수 없어요", "하루 3-4회 혈당을 측정해보세요!"] if not glucose_values else [
                f"오늘 하루 평균: {avg_glucose:.0f}mg/dL",
                "정상 범위로 매우 좋아요!" if avg_glucose <= 100 else
                "정상 범위보다 조금 높아요" if avg_glucose <= 140 else
                "정상 범위보다 높아요",
                "원인 힌트: 간식 섭취 시간 간격이 짧았어요." if avg_glucose <= 140 else
                "원인 힌트: 식사량과 탄수화물 섭취가 많았어요."
            ],
            "최고 혈당": "혈당 측정 기록이 없어 최고값을 확인할 수 없어요 식사 전후 혈당 체크를 시작해보세요!" if not glucose_values else (
                f"가장 높았을 때는 {max_glucose:.0f}mg/dL였지만 곧 안정을 찾았어요" if max_glucose <= 140 else
                f"가장 높았을 때는 {max_glucose:.0f}mg/dL였어요 식사 후 혈당 상승을 조절해보세요!" if max_glucose <= 180 else
                f"가장 높았을 때는 {max_glucose:.0f}mg/dL였어요 식사량과 탄수화물 섭취를 줄여보세요!"
            ),
            "단짝이의 평가": "혈당 측정이 첫 걸음이에요! 꾸준히 측정하면서 건강한 습관을 만들어가요" if not glucose_values else (
                "오늘도 훌륭한 혈당 관리였어요! 이 상태를 계속 유지해보세요" if avg_glucose <= 100 and spike_count <= 1 else
                "혈당 관리가 양호해요! 조금만 더 신경쓰면 완벽할 거예요" if avg_glucose <= 140 and spike_count <= 2 else
                "혈당 관리를 위해 식단 조절과 운동을 함께 해보세요! 함께 노력해봐요"
            )
        }
    }


def get_default_child_summary(summary):
    """아이용 기본 요약 템플릿"""
    if summary['average_glucose'] <= 120 and summary['tir_percentage'] >= 70:
        summary_text = f"이번 주 네 혈당은 평균적으로 아주 잘 유지됐어!\n({summary['average_glucose']}mg/dL, 안정 구간 {summary['tir_percentage']}%)\n"
    elif summary['average_glucose'] <= 140 and summary['tir_percentage'] >= 60:
        summary_text = f"이번 주 네 혈당은 괜찮게 유지됐어!\n({summary['average_glucose']}mg/dL, 안정 구간 {summary['tir_percentage']}%)\n"
    else:
        summary_text = f"이번 주 네 혈당은 조금 신경써야 할 것 같아.\n({summary['average_glucose']}mg/dL, 안정 구간 {summary['tir_percentage']}%)\n"
    
    if summary['hyperglycemia_count'] > 0:
        summary_text += f"밥 먹고 나서 몇 번({summary['hyperglycemia_count']}번) 혈당이 조금 올라갔지만,\n너무 걱정할 정도는 아니야.\n"
    else:
        summary_text += "밥 먹고 나서도 혈당이 잘 조절됐어!\n"
    
    summary_text += f"가볍게 몸을 움직일 때마다 혈당이 차분하게 돌아오는\n모습이 보여서 참 잘했어!"
    
    return summary_text
