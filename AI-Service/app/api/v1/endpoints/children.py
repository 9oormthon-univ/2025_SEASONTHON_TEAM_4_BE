"""아이 관련 API 엔드포인트 - 기존 구조 유지"""

from flask import Blueprint, request, g, jsonify
from app.utils.error import (
    log_request_info, safe_json_response, ValidationError, NotFoundError, DatabaseError,
    DataIntegrityError, TimeoutError, ServiceUnavailableError, QuestError, ConflictError,
    get_user_friendly_error, get_user_friendly_success
)
from app.utils.auth import jwt_auth_member_id
from app.database import get_member_info, get_quests_by_date, get_weekly_glucose_data
from app.utils.business import (
    format_glucose_data, calculate_weekly_glucose_summary,
    get_default_date_range
)
from app.services.glucose_service import calculate_glucose_metrics, analyze_glucose
from app.utils.common import load_text
from app.database import SessionLocal
from app.models.database_models import Quest
from datetime import datetime

children_bp = Blueprint('children', __name__)


@children_bp.route("/request", methods=["POST"])
@jwt_auth_member_id
@log_request_info
def child_request_api():
    """아이 퀘스트 완료 요청 API"""
    try:
        # JSON 데이터 검증
        if not request.is_json:
            raise ValidationError("JSON 형식의 데이터가 필요합니다")
        
        data = request.get_json()
        if not data:
            raise ValidationError("요청 데이터가 비어있습니다")
        
        quest_id = data.get("quest_id")
        
        if not quest_id:
            raise ValidationError("quest_id가 필요합니다")
        
        # JWT에서 member_id 가져오기
        member_id = g.member_id
        
        # 데이터 타입 검증
        try:
            quest_id = int(quest_id)
        except (ValueError, TypeError):
            raise ValidationError("quest_id는 숫자여야 합니다")
        
        with SessionLocal() as db:
            quest = db.query(Quest).filter(Quest.id == quest_id, Quest.member_id == member_id).first()
            if not quest:
                raise NotFoundError("퀘스트를 찾을 수 없습니다")
            
            if quest.is_completed:
                raise ConflictError("이미 완료된 퀘스트입니다")
            
            quest.is_completed = True
            quest.approval_status = '요청 중'
            quest.updated_at = datetime.now()
            db.commit()
            db.refresh(quest)
        
        success_msg = get_user_friendly_success("quest_completion_requested")
        return safe_json_response({
            "message": success_msg["message"]["message"],
            "quest_id": quest.id,
            "status": quest.approval_status
        })
        
    except ValidationError as e:
        return safe_json_response(get_user_friendly_error("VALIDATION_ERROR", str(e)), 400)
    except NotFoundError as e:
        return safe_json_response(get_user_friendly_error("NOT_FOUND", str(e)), 404)
    except ConflictError as e:
        return safe_json_response(get_user_friendly_error("CONFLICT_ERROR", str(e)), 409)
    except DatabaseError as e:
        return safe_json_response(get_user_friendly_error("DATABASE_ERROR", str(e)), 500)
    except Exception as e:
        return safe_json_response(get_user_friendly_error("INTERNAL_SERVER_ERROR", str(e)), 500)


@children_bp.route("/report", methods=["GET"])
@jwt_auth_member_id
@log_request_info
def child_report_api():
    """아이를 대상으로 한 주간 혈당 분석 보고서 API"""
    try:
        # JWT에서 member_id 가져오기
        member_id = g.member_id
        member_info = g.member_info
        
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        if not start_date or not end_date:
            start_date, end_date = get_default_date_range()
        
        # 주간 혈당 데이터 조회
        try:
            glucose_data = get_weekly_glucose_data(member_id, start_date, end_date)
            if not glucose_data:
                raise DataIntegrityError("혈당 데이터가 없습니다")
        except Exception as e:
            raise DatabaseError(f"혈당 데이터 조회 실패: {str(e)}")
        
        # 혈당 요약 계산
        try:
            summary = calculate_weekly_glucose_summary(glucose_data)
        except Exception as e:
            raise DataIntegrityError(f"혈당 요약 계산 실패: {str(e)}")
        
        # RAG 강화된 LLM 분석
        try:
            formatted_data = format_glucose_data(glucose_data)
            glucose_metrics = calculate_glucose_metrics(formatted_data)
            prompt_text = load_text("app/prompts/child_report_prompt.txt")
            analysis_result = analyze_glucose(glucose_metrics, prompt_text, member_info.get('age'), member_id, use_rag=True)
        except TimeoutError as e:
            raise TimeoutError(f"LLM 분석 시간 초과: {str(e)}")
        except Exception as e:
            raise ServiceUnavailableError(f"LLM 분석 서비스 오류: {str(e)}")
        
        # RAG 메타데이터 추출 (내부 처리용)
        if isinstance(analysis_result, dict) and 'rag_metadata' in analysis_result:
            analysis_result.pop('rag_metadata')
        
        # LLM 결과에서 요약 텍스트 추출 (안전한 처리)
        summary_text = ''
        if isinstance(analysis_result, dict):
            summary_text = analysis_result.get('summary', '')
        else:
            print(f"Unexpected analysis_result type: {type(analysis_result)}")
            print(f"analysis_result content: {analysis_result}")
        
        # LLM 결과가 없으면 기본 템플릿 사용
        if not summary_text:
            from app.utils.ai_utils import get_default_child_summary
            summary_text = get_default_child_summary(summary)
        
        return safe_json_response({
            "summary": summary_text,
            "data": {
                "period": f"{start_date} ~ {end_date}",
                "average_glucose": summary['average_glucose'],
                "tir_percentage": summary['tir_percentage'],
                "hyperglycemia_count": summary['hyperglycemia_count'],
                "hypoglycemia_count": summary['hypoglycemia_count'],
                "glucose_variability": summary['glucose_variability'],
                "total_readings": len(glucose_data)
            }
        })
        
    except ValidationError as e:
        return safe_json_response(get_user_friendly_error("VALIDATION_ERROR", str(e)), 400)
    except NotFoundError as e:
        return safe_json_response(get_user_friendly_error("NOT_FOUND", str(e)), 404)
    except DataIntegrityError as e:
        return safe_json_response(get_user_friendly_error("GLUCOSE_DATA_ERROR", str(e)), 422)
    except TimeoutError as e:
        return safe_json_response(get_user_friendly_error("TIMEOUT_ERROR", str(e)), 408)
    except ServiceUnavailableError as e:
        return safe_json_response(get_user_friendly_error("SERVICE_UNAVAILABLE", str(e)), 503)
    except DatabaseError as e:
        return safe_json_response(get_user_friendly_error("DATABASE_ERROR", str(e)), 500)
    except Exception as e:
        return safe_json_response(get_user_friendly_error("INTERNAL_SERVER_ERROR", str(e)), 500)