"""공통 API 라우트"""

from flask import request, jsonify
from common.utils.database_utils import (
    get_member_info, get_glucose_data, get_weekly_glucose_data,
    save_quests_to_db, get_quests_by_date
)
from common.utils.glucose_utils import (
    format_glucose_data, calculate_weekly_glucose_summary,
    get_default_date_range
)
from common.services.glucose_service import calculate_glucose_metrics
from common.utils.quest_utils import generate_llm_quests
from datetime import datetime


def combined_quest():
    """혈당 퀘스트와 기록 퀘스트를 통합하여 총 4개 퀘스트 반환"""
    try:
        member_id = int(request.args.get("member_id", 1))
        today = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        # 회원 정보 조회
        member_info = get_member_info(member_id)
        if not member_info:
            return jsonify({"error": "회원을 찾을 수 없습니다."}), 404
        
        # 해당 날짜에 이미 퀘스트가 있는지 확인
        existing_quests = get_quests_by_date(member_id, today)
        if "error" not in existing_quests and existing_quests.get("total_count", 0) > 0:
            # 기존 퀘스트가 있으면 기존 퀘스트를 반환
            quest_list = existing_quests.get("quests", [])
            result = {}
            for quest in quest_list:
                result[quest["quest_title"]] = quest["quest_content"]
            return jsonify({"result": result})
        
        # 혈당 데이터 기반 퀘스트 생성
        glucose_readings = get_glucose_data(member_id, today)
        blood_sugar_data = format_glucose_data(glucose_readings)
        glucose_metrics = calculate_glucose_metrics(blood_sugar_data)
        
        # LLM을 사용하여 개인화된 퀘스트 생성
        result = generate_llm_quests(glucose_metrics, member_info)
        
        # 퀘스트를 데이터베이스에 저장
        save_quests_to_db(member_id, result, today)
        
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_quests_api():
    """날짜별 퀘스트 조회 API (LLM 분석 포함)"""
    try:
        member_id = int(request.args.get("member_id", 1))
        date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        result = get_quests_by_date(member_id, date_str)
        
        if "error" in result:
            return jsonify(result), 500
        
        # LLM을 사용한 퀘스트 완료율 분석
        completion_rate = result.get("completion_rate", 0)
        completed_count = result.get("completed_count", 0)
        total_count = result.get("total_count", 0)
        
        # 완료율에 따른 격려 메시지 생성
        if completion_rate == 100:
            encouragement = "완벽해! 모든 퀘스트를 완료했어! 정말 대단해!"
        elif completion_rate >= 75:
            encouragement = "거의 다 했어! 조금만 더 노력하면 완벽할 거야!"
        elif completion_rate >= 50:
            encouragement = "절반 이상 완료했어! 계속 화이팅이야!"
        elif completion_rate >= 25:
            encouragement = "시작이 반이야! 조금씩 꾸준히 해보자!"
        else:
            encouragement = "오늘부터 시작해보자! 작은 걸음부터 차근차근!"
        
        # 결과에 격려 메시지 추가
        result["encouragement"] = encouragement
        result["analysis"] = {
            "completion_rate": completion_rate,
            "completed_count": completed_count,
            "total_count": total_count,
            "remaining_count": total_count - completed_count
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
