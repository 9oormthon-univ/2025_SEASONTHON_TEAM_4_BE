"""부모 관련 API 라우트"""

from flask import request, jsonify
from common.utils.database_utils import get_member_info, get_glucose_data, get_weekly_glucose_data
from common.utils.glucose_utils import (
    format_glucose_data, calculate_weekly_glucose_summary,
    get_default_date_range
)
from common.services.glucose_service import calculate_glucose_metrics, analyze_glucose
from common.utils.ai_utils import (
    format_analyze_prompt, extract_json_from_ai_response,
    get_default_analysis_result
)
from common.utils.io import load_text
from common.db import SessionLocal
from common.models.database_models import Quest
from datetime import datetime


def glucose_analyze():
    """혈당 종합 분석 및 비서 코칭"""
    try:
        member_id = int(request.args.get("member_id", 1))
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 회원 정보 조회
        member_info = get_member_info(member_id)
        if not member_info:
            return jsonify({"error": "회원을 찾을 수 없습니다."}), 404
        
        # 혈당 데이터 조회 및 지표 계산
        readings = get_glucose_data(member_id, today)
        blood_sugar_data = format_glucose_data(readings)
        glucose_metrics = calculate_glucose_metrics(blood_sugar_data)
        avg_glucose = glucose_metrics.get('average_glucose', 0)
        max_glucose = glucose_metrics.get('max_glucose', 0)
        min_glucose = glucose_metrics.get('min_glucose', 0)
        spike_count = glucose_metrics.get('spike_count', 0)
        glucose_values = [r.glucose_mg_dl for r in readings if r.glucose_mg_dl is not None]
        
        # AI 분석 시도
        prompt = load_text("common/prompts/parent_analyze_prompt.txt")
        formatted_prompt = format_analyze_prompt(prompt, avg_glucose, max_glucose, min_glucose, spike_count, len(glucose_values))
        
        from common.ai import call_openai_api
        ai_response = call_openai_api(formatted_prompt, "당신은 혈당 관리를 도와주는 친근한 비서입니다. 반드시 JSON 형식으로만 응답해주세요.")
        
        analysis_result = extract_json_from_ai_response(ai_response)
        
        # AI 분석 실패 시 기본 응답 반환
        if not analysis_result:
            analysis_result = get_default_analysis_result(glucose_values, avg_glucose, max_glucose, spike_count)
        
        return jsonify(analysis_result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def parent_approve_api():
    """부모 퀘스트 승인 API"""
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
            
            if quest.approval_status != '요청 중':
                return jsonify({"error": "승인 요청 중인 퀘스트가 아닙니다."}), 400
            
            quest.approval_status = '달성 완료'
            quest.updated_at = datetime.now()
            
            db.commit()
            
            return jsonify({"message": "퀘스트가 승인 완료되었습니다.", "quest_id": quest_id})
            
        except Exception as e:
            db.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def glucose_summary_api():
    """주간 혈당 분석 요약 API"""
    try:
        member_id = int(request.args.get("member_id", 1))
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        # 날짜가 제공되지 않으면 최근 7일로 설정
        if not start_date or not end_date:
            start_date, end_date = get_default_date_range()
        
        # 회원 정보 확인
        member_info = get_member_info(member_id)
        if not member_info:
            return jsonify({"error": "회원을 찾을 수 없습니다."}), 404
        
        # 주간 혈당 데이터 조회
        glucose_data = get_weekly_glucose_data(member_id, start_date, end_date)
        
        # 혈당 요약 계산
        summary = calculate_weekly_glucose_summary(glucose_data)
        
        # LLM을 사용한 분석
        formatted_data = format_glucose_data(glucose_data)
        glucose_metrics = calculate_glucose_metrics(formatted_data)
        prompt_text = load_text("common/prompts/parent_report_prompt.txt")
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
            summary_text = f"이번 주 평균 혈당은 {summary['average_glucose']}mg/dL, 안정 구간(TIR)은 {summary['tir_percentage']}%였습니다.\n"
            summary_text += f"고혈당이 {summary['hyperglycemia_count']}회 발생했으며 저혈당은 {summary['hypoglycemia_count']}회 발생하지 않았습니다.\n"
            summary_text += f"규칙적인 저강도 운동 후 혈당이 {summary['exercise_recovery_pattern']}."
        
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
