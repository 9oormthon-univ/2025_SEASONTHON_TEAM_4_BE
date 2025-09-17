"""부모 관련 API 엔드포인트 - 기존 구조 유지"""

from flask import Blueprint, request, jsonify
from app.utils.error_handler import log_request_info, safe_json_response, ValidationError, NotFoundError, DatabaseError
from app.utils.user_messages import get_user_friendly_error, get_user_friendly_success
from app.utils.database_utils import get_member_info, get_weekly_glucose_data, get_quests_by_date
from app.utils.glucose_utils import (
    format_glucose_data, calculate_weekly_glucose_summary,
    get_default_date_range
)
from app.services.glucose_service import calculate_glucose_metrics, analyze_glucose
from app.utils.io import load_text
from app.db.database import SessionLocal
from app.models.database_models import Quest
from datetime import datetime

parents_bp = Blueprint('parents', __name__)


@parents_bp.route("/report", methods=["GET"])
@log_request_info
def parent_report_api():
    """부모를 대상으로 한 주간 혈당 분석 보고서 API"""
    try:
        member_id = int(request.args.get("member_id", 1))
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        if not start_date or not end_date:
            start_date, end_date = get_default_date_range()
        
        # 회원 정보 확인
        member_info = get_member_info(member_id)
        if not member_info:
            raise NotFoundError("회원을 찾을 수 없습니다.")
        
        # 주간 혈당 데이터 조회
        glucose_data = get_weekly_glucose_data(member_id, start_date, end_date)
        
        # 혈당 요약 계산
        summary = calculate_weekly_glucose_summary(glucose_data)
        
        # LLM을 사용한 분석
        formatted_data = format_glucose_data(glucose_data)
        glucose_metrics = calculate_glucose_metrics(formatted_data)
        prompt_text = load_text("app/prompts/parent_report_prompt.txt")
        analysis_result = analyze_glucose(glucose_metrics, prompt_text, member_info.get('age'))
        
        # LLM 결과에서 요약 텍스트 추출 (안전한 처리)
        summary_text = ''
        if isinstance(analysis_result, dict):
            summary_text = analysis_result.get('summary', '')
        else:
            print(f"Unexpected analysis_result type: {type(analysis_result)}")
            print(f"analysis_result content: {analysis_result}")
        
        # LLM 결과가 없으면 기본 템플릿 사용
        if not summary_text:
            from app.utils.ai_utils import get_default_parent_summary
            summary_text = get_default_parent_summary(summary)
        
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
    except DatabaseError as e:
        return safe_json_response(get_user_friendly_error("DATABASE_ERROR", str(e)), 500)
    except Exception as e:
        return safe_json_response(get_user_friendly_error("INTERNAL_SERVER_ERROR", str(e)), 500)


@parents_bp.route("/analyze", methods=["GET"])
@log_request_info
def parent_analyze_api():
    """부모를 대상으로 한 혈당 분석 API"""
    try:
        member_id = int(request.args.get("member_id", 1))
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        if not start_date or not end_date:
            start_date, end_date = get_default_date_range()
        
        # 회원 정보 확인
        member_info = get_member_info(member_id)
        if not member_info:
            raise NotFoundError("회원을 찾을 수 없습니다.")
        
        # 주간 혈당 데이터 조회
        glucose_data = get_weekly_glucose_data(member_id, start_date, end_date)
        
        # 혈당 요약 계산
        summary = calculate_weekly_glucose_summary(glucose_data)
        
        # LLM을 사용한 분석
        formatted_data = format_glucose_data(glucose_data)
        glucose_metrics = calculate_glucose_metrics(formatted_data)
        prompt_text = load_text("app/prompts/parent_analyze_prompt.txt")
        analysis_result = analyze_glucose(glucose_metrics, prompt_text, member_info.get('age'))
        
        # LLM 결과에서 분석 텍스트 추출 (안전한 처리)
        analysis_text = ''
        if isinstance(analysis_result, dict):
            analysis_text = analysis_result.get('analysis', '')
        else:
            print(f"Unexpected analysis_result type: {type(analysis_result)}")
            print(f"analysis_result content: {analysis_result}")
        
        # LLM 결과가 없으면 기본 템플릿 사용
        if not analysis_text:
            from app.utils.ai_utils import get_default_parent_analysis
            analysis_text = get_default_parent_analysis(summary)
        
        return safe_json_response({
            "analysis": analysis_text,
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
    except DatabaseError as e:
        return safe_json_response(get_user_friendly_error("DATABASE_ERROR", str(e)), 500)
    except Exception as e:
        return safe_json_response(get_user_friendly_error("INTERNAL_SERVER_ERROR", str(e)), 500)


@parents_bp.route("/approve", methods=["POST"])
@log_request_info
def parent_approve_api():
    """부모 퀘스트 승인 API"""
    try:
        data = request.get_json()
        quest_id = data.get("quest_id")
        member_id = data.get("member_id")
        approval_status = data.get("approval_status", "approved")  # approved or rejected
        
        if not quest_id or not member_id:
            raise ValidationError("quest_id와 member_id가 필요합니다.")
        
        if approval_status not in ["approved", "rejected"]:
            raise ValidationError("approval_status는 'approved' 또는 'rejected'여야 합니다.")
        
        with SessionLocal() as db:
            quest = db.query(Quest).filter(Quest.id == quest_id, Quest.member_id == member_id).first()
            if not quest:
                raise NotFoundError("퀘스트를 찾을 수 없습니다.")
            
            quest.approval_status = approval_status
            quest.updated_at = datetime.now()
            db.commit()
            db.refresh(quest)
        
        success_msg = get_user_friendly_success("quest_approval_updated")
        return safe_json_response({
            "message": success_msg["message"]["message"],
            "quest_id": quest.id,
            "status": quest.approval_status
        })
        
    except ValidationError as e:
        return safe_json_response(get_user_friendly_error("VALIDATION_ERROR", str(e)), 400)
    except NotFoundError as e:
        return safe_json_response(get_user_friendly_error("NOT_FOUND", str(e)), 404)
    except DatabaseError as e:
        return safe_json_response(get_user_friendly_error("DATABASE_ERROR", str(e)), 500)
    except Exception as e:
        return safe_json_response(get_user_friendly_error("INTERNAL_SERVER_ERROR", str(e)), 500)
