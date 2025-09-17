"""퀘스트 관련 API 엔드포인트 - 기존 구조 유지"""

from flask import Blueprint, request, g
from app.utils.error import (
    log_request_info, safe_json_response, ValidationError, NotFoundError, DatabaseError,
    DataIntegrityError, TimeoutError, ServiceUnavailableError, QuestError,
    get_user_friendly_error, get_user_friendly_success
)
from app.utils.auth import jwt_auth_member_id
from app.database import (
    get_member_info, get_glucose_data, get_weekly_glucose_data,
    save_quests_to_db, get_quests_by_date
)
from app.utils.business import (
    format_glucose_data, calculate_weekly_glucose_summary,
    get_default_date_range, generate_llm_quests
)
from app.services.glucose_service import calculate_glucose_metrics
from datetime import datetime

quests_bp = Blueprint('quests', __name__)


@quests_bp.route("/", methods=["GET"])
@jwt_auth_member_id
@log_request_info
def combined_quest():
    """혈당 퀘스트와 기록 퀘스트를 통합하여 총 4개 퀘스트 반환"""
    try:
        # JWT에서 member_id 가져오기
        member_id = g.member_id
        member_info = g.member_info
        
        today = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
        
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
            if not glucose_readings:
                raise DataIntegrityError("혈당 데이터가 없습니다")
            blood_sugar_data = format_glucose_data(glucose_readings)
            glucose_metrics = calculate_glucose_metrics(blood_sugar_data)
        except DataIntegrityError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"혈당 데이터 조회 실패: {str(e)}")
        
        # 기본 LLM을 사용하여 개인화된 퀘스트 생성
        try:
            result = generate_llm_quests(glucose_metrics, member_info, member_id, use_rag=False)
            if not result or not isinstance(result, dict):
                raise QuestError("퀘스트 생성 결과가 올바르지 않습니다")
        except QuestError as e:
            raise e
        except TimeoutError as e:
            raise TimeoutError(f"퀘스트 생성 시간 초과: {str(e)}")
        except Exception as e:
            raise ServiceUnavailableError(f"퀘스트 생성 서비스 오류: {str(e)}")
        
        # 퀘스트를 데이터베이스에 저장
        try:
            save_quests_to_db(member_id, result, today)
        except DataIntegrityError as e:
            raise DataIntegrityError(f"퀘스트 저장 데이터 오류: {str(e)}")
        except Exception as e:
            raise DatabaseError(f"퀘스트 저장 실패: {str(e)}")
        
        return safe_json_response({
            "result": result
        })
        
    except ValidationError as e:
        return safe_json_response(get_user_friendly_error("VALIDATION_ERROR", str(e)), 400)
    except NotFoundError as e:
        return safe_json_response(get_user_friendly_error("NOT_FOUND", str(e)), 404)
    except DataIntegrityError as e:
        return safe_json_response(get_user_friendly_error("GLUCOSE_DATA_ERROR", str(e)), 422)
    except QuestError as e:
        return safe_json_response(get_user_friendly_error("QUEST_ERROR", str(e)), 422)
    except TimeoutError as e:
        return safe_json_response(get_user_friendly_error("TIMEOUT_ERROR", str(e)), 408)
    except ServiceUnavailableError as e:
        return safe_json_response(get_user_friendly_error("SERVICE_UNAVAILABLE", str(e)), 503)
    except DatabaseError as e:
        return safe_json_response(get_user_friendly_error("DATABASE_ERROR", str(e)), 500)
    except Exception as e:
        return safe_json_response(get_user_friendly_error("INTERNAL_SERVER_ERROR", str(e)), 500)


@quests_bp.route("/list", methods=["GET"])
@jwt_auth_member_id
@log_request_info
def get_quests_api():
    """날짜별 퀘스트 조회 API (LLM 분석 포함)"""
    try:
        # JWT에서 member_id 가져오기
        member_id = g.member_id
        
        date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        # 퀘스트 조회
        try:
            result = get_quests_by_date(member_id, date_str)
        except Exception as e:
            raise DatabaseError(f"퀘스트 조회 실패: {str(e)}")
        
        if "error" in result:
            raise DatabaseError(result["error"])
        
        # 결과 유효성 검증
        if not isinstance(result, dict):
            raise DataIntegrityError("퀘스트 조회 결과가 올바르지 않습니다")
        
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
    except DataIntegrityError as e:
        return safe_json_response(get_user_friendly_error("GLUCOSE_DATA_ERROR", str(e)), 422)
    except DatabaseError as e:
        return safe_json_response(get_user_friendly_error("DATABASE_ERROR", str(e)), 500)
    except Exception as e:
        return safe_json_response(get_user_friendly_error("INTERNAL_SERVER_ERROR", str(e)), 500)