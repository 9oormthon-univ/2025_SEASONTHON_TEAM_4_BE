"""퀘스트 관련 API 엔드포인트 - 기존 구조 유지"""

from flask import Blueprint, request
from app.utils.error_handler import log_request_info, safe_json_response, ValidationError, NotFoundError, DatabaseError
from app.utils.user_messages import get_user_friendly_error, get_user_friendly_success
from app.utils.database_utils import (
    get_member_info, get_glucose_data, get_weekly_glucose_data,
    save_quests_to_db, get_quests_by_date
)
from app.utils.glucose_utils import (
    format_glucose_data, calculate_weekly_glucose_summary,
    get_default_date_range
)
from app.services.glucose_service import calculate_glucose_metrics
from app.utils.quest_utils import generate_llm_quests
from datetime import datetime

quests_bp = Blueprint('quests', __name__)


@quests_bp.route("/", methods=["GET"])
@log_request_info
def combined_quest():
    """혈당 퀘스트와 기록 퀘스트를 통합하여 총 4개 퀘스트 반환"""
    try:
        # 파라미터 검증
        member_id = request.args.get("member_id")
        if not member_id:
            raise ValidationError("member_id 파라미터가 필요합니다")
        
        try:
            member_id = int(member_id)
        except ValueError:
            raise ValidationError("member_id는 숫자여야 합니다")
        
        today = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        # 회원 정보 조회
        member_info = get_member_info(member_id)
        if not member_info:
            raise NotFoundError("회원을 찾을 수 없습니다")
        
        # 해당 날짜에 이미 퀘스트가 있는지 확인
        existing_quests = get_quests_by_date(member_id, today)
        if "error" not in existing_quests and existing_quests.get("total_count", 0) > 0:
            # 기존 퀘스트가 있으면 기존 퀘스트를 반환
            quest_list = existing_quests.get("quests", [])
            result = {}
            for quest in quest_list:
                result[quest["quest_title"]] = quest["quest_content"]
            
            return safe_json_response({
                "result": result
            })
        
        # 혈당 데이터 기반 퀘스트 생성
        try:
            glucose_readings = get_glucose_data(member_id, today)
            blood_sugar_data = format_glucose_data(glucose_readings)
            glucose_metrics = calculate_glucose_metrics(blood_sugar_data)
        except Exception as e:
            raise DatabaseError(f"혈당 데이터 조회 실패: {str(e)}")
        
        # 기본 LLM을 사용하여 개인화된 퀘스트 생성
        try:
            result = generate_llm_quests(glucose_metrics, member_info, member_id, use_rag=False)
        except Exception as e:
            raise DatabaseError(f"퀘스트 생성 실패: {str(e)}")
        
        # 퀘스트를 데이터베이스에 저장
        try:
            save_quests_to_db(member_id, result, today)
        except Exception as e:
            raise DatabaseError(f"퀘스트 저장 실패: {str(e)}")
        
        return safe_json_response({
            "result": result
        })
        
    except ValidationError as e:
        return safe_json_response(get_user_friendly_error("VALIDATION_ERROR", str(e)), 400)
    except NotFoundError as e:
        return safe_json_response(get_user_friendly_error("NOT_FOUND", str(e)), 404)
    except DatabaseError as e:
        return safe_json_response(get_user_friendly_error("DATABASE_ERROR", str(e)), 500)
    except Exception as e:
        return safe_json_response(get_user_friendly_error("INTERNAL_SERVER_ERROR", str(e)), 500)


@quests_bp.route("/list", methods=["GET"])
@log_request_info
def get_quests_api():
    """날짜별 퀘스트 조회 API (LLM 분석 포함)"""
    try:
        # 파라미터 검증
        member_id = request.args.get("member_id")
        if not member_id:
            raise ValidationError("member_id 파라미터가 필요합니다")
        
        try:
            member_id = int(member_id)
        except ValueError:
            raise ValidationError("member_id는 숫자여야 합니다")
        
        date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        # 퀘스트 조회
        try:
            result = get_quests_by_date(member_id, date_str)
        except Exception as e:
            raise DatabaseError(f"퀘스트 조회 실패: {str(e)}")
        
        if "error" in result:
            raise DatabaseError(result["error"])
        
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
        
        return safe_json_response({
            "result": result
        })
        
    except ValidationError as e:
        return safe_json_response(get_user_friendly_error("VALIDATION_ERROR", str(e)), 400)
    except DatabaseError as e:
        return safe_json_response(get_user_friendly_error("DATABASE_ERROR", str(e)), 500)
    except Exception as e:
        return safe_json_response(get_user_friendly_error("INTERNAL_SERVER_ERROR", str(e)), 500)