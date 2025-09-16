"""아이 관련 API 라우트"""

from flask import request, jsonify
from common.utils.database_utils import get_member_info, get_quests_by_date
from common.db import SessionLocal
from common.models.database_models import Quest
from datetime import datetime


def child_request_api():
    """아이 퀘스트 완료 요청 API"""
    try:
        data = request.get_json()
        quest_id = data.get("quest_id")
        member_id = data.get("member_id")
        
        if not quest_id or not member_id:
            return jsonify({"error": "quest_id와 member_id가 필요합니다."}), 400
        
        db = SessionLocal()
        try:
            quest = db.query(Quest).filter(
                Quest.id == quest_id,
                Quest.member_id == member_id
            ).first()
            
            if not quest:
                return jsonify({"error": "퀘스트를 찾을 수 없습니다."}), 404
            
            if quest.is_completed:
                return jsonify({"error": "이미 완료된 퀘스트입니다."}), 400
            
            quest.is_completed = True
            quest.approval_status = '요청 중'
            quest.updated_at = datetime.now()
            
            db.commit()
            
            return jsonify({"message": "퀘스트가 완료되었습니다. 승인 요청이 전송되었습니다.", "quest_id": quest_id})
            
        except Exception as e:
            db.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def child_report_api():
    """아이를 대상으로 한 주간 혈당 분석 보고서 API"""
    try:
        member_id = int(request.args.get("member_id", 1))
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        # 날짜가 제공되지 않으면 최근 7일로 설정
        from common.utils.glucose_utils import get_default_date_range
        if not start_date or not end_date:
            start_date, end_date = get_default_date_range()
        
        # 회원 정보 확인
        member_info = get_member_info(member_id)
        if not member_info:
            return jsonify({"error": "회원을 찾을 수 없습니다."}), 404
        
        # 주간 혈당 데이터 조회
        from common.utils.database_utils import get_weekly_glucose_data
        glucose_data = get_weekly_glucose_data(member_id, start_date, end_date)
        
        # 혈당 요약 계산
        from common.utils.glucose_utils import calculate_weekly_glucose_summary
        summary = calculate_weekly_glucose_summary(glucose_data)
        
        # LLM을 사용한 분석
        from common.utils.glucose_utils import format_glucose_data
        from common.services.glucose_service import calculate_glucose_metrics, analyze_glucose
        from common.utils.io import load_text
        
        formatted_data = format_glucose_data(glucose_data)
        glucose_metrics = calculate_glucose_metrics(formatted_data)
        prompt_text = load_text("common/prompts/child_report_prompt.txt")
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
            from common.utils.ai_utils import get_default_child_summary
            summary_text = get_default_child_summary(summary)
        
        return jsonify({
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
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
