"""부모 관련 API 엔드포인트 - 기존 구조 유지"""

from flask import Blueprint, request, jsonify
from app.utils.error_handler import (
    log_request_info, safe_json_response, ValidationError, NotFoundError, DatabaseError,
    AuthenticationError, AuthorizationError, RateLimitError, ServiceUnavailableError,
    TimeoutError, DataIntegrityError, QuestError, handle_ai_service_error,
    handle_database_error, handle_glucose_data_error, handle_quest_error,
    validate_glucose_value, validate_quest_status, validate_approval_status,
    validate_age, validate_diabetes_type
)
from app.utils.user_messages import get_user_friendly_error, get_user_friendly_success
from app.utils.database_utils import (
    get_member_info, get_quests_by_date, get_weekly_glucose_data, get_glucose_data,
    get_food_data, get_exercise_data, get_glucose_food_correlation, get_glucose_exercise_correlation
)
from app.utils.glucose_utils import (
    format_glucose_data, calculate_weekly_glucose_summary,
    get_default_date_range
)
from app.services.glucose_service import calculate_glucose_metrics, analyze_glucose
from app.utils.io import load_text
from app.utils.glucose_analysis_utils import (
    analyze_food_glucose_impact, analyze_exercise_glucose_impact, 
    generate_daily_glucose_analysis
)
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
        
        # RAG 강화된 LLM 분석
        formatted_data = format_glucose_data(glucose_data)
        glucose_metrics = calculate_glucose_metrics(formatted_data)
        prompt_text = load_text("app/prompts/parent_report_prompt.txt")
        analysis_result = analyze_glucose(glucose_metrics, prompt_text, member_info.get('age'), member_id, use_rag=True)
        
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
        
        # RAG 강화된 LLM 분석
        formatted_data = format_glucose_data(glucose_data)
        glucose_metrics = calculate_glucose_metrics(formatted_data)
        prompt_text = load_text("app/prompts/parent_analyze_prompt.txt")
        analysis_result = analyze_glucose(glucose_metrics, prompt_text, member_info.get('age'), member_id, use_rag=True)
        
        # RAG 메타데이터 추출 (내부 처리용)
        if isinstance(analysis_result, dict) and 'rag_metadata' in analysis_result:
            analysis_result.pop('rag_metadata')
        
        # LLM 결과에서 분석 텍스트 추출 (안전한 처리)
        analysis_text = ''
        if isinstance(analysis_result, dict):
            analysis_text = analysis_result.get('result', '')
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
    """부모가 아이의 퀘스트 완료를 승인하는 API"""
    try:
        data = request.get_json()
        quest_id = data.get("quest_id")
        member_id = data.get("member_id")
        approval_status = data.get("approval_status", "승인")  # "승인" 또는 "거부"
        
        # 유효성 검증
        if not quest_id or not member_id:
            raise ValidationError("quest_id와 member_id가 필요합니다.")
        
        # 승인 상태 유효성 검증
        approval_status = validate_approval_status(approval_status)
        
        with SessionLocal() as db:
            quest = db.query(Quest).filter(Quest.id == quest_id, Quest.member_id == member_id).first()
            if not quest:
                raise NotFoundError("퀘스트를 찾을 수 없습니다.")
            
            if quest.approval_status != '요청 중':
                raise ValidationError("승인 대기 중인 퀘스트가 아닙니다.")
            
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
    except QuestError as e:
        return safe_json_response(get_user_friendly_error("QUEST_ERROR", str(e)), 422)
    except DataIntegrityError as e:
        return safe_json_response(get_user_friendly_error("DATA_INTEGRITY_ERROR", str(e)), 422)
    except Exception as e:
        return safe_json_response(get_user_friendly_error("INTERNAL_SERVER_ERROR", str(e)), 500)


@parents_bp.route("/hint", methods=["GET"])
@log_request_info
def parent_hint_api():
    """부모를 위한 오늘의 돌봄 힌트 제공 API (오늘 하루 혈당 데이터 기반)"""
    try:
        member_id = int(request.args.get("member_id", 1))
        
        # 회원 정보 확인
        member_info = get_member_info(member_id)
        if not member_info:
            raise NotFoundError("회원을 찾을 수 없습니다.")
        
        # 오늘 날짜 설정
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 오늘의 혈당 데이터 조회
        glucose_data = get_glucose_data(member_id, today)
        
        # 혈당 데이터 유효성 검증
        handle_glucose_data_error(glucose_data, member_id)
        
        # 오늘의 구체적인 돌봄 힌트 생성
        care_hints = generate_daily_care_hints(glucose_data, member_info, today)
        
        return safe_json_response({
            "care_hints": care_hints
        })
        
    except ValidationError as e:
        return safe_json_response(get_user_friendly_error("VALIDATION_ERROR", str(e)), 400)
    except NotFoundError as e:
        return safe_json_response(get_user_friendly_error("NOT_FOUND", str(e)), 404)
    except DatabaseError as e:
        return safe_json_response(get_user_friendly_error("DATABASE_ERROR", str(e)), 500)
    except DataIntegrityError as e:
        return safe_json_response(get_user_friendly_error("GLUCOSE_DATA_ERROR", str(e)), 422)
    except TimeoutError as e:
        return safe_json_response(get_user_friendly_error("TIMEOUT_ERROR", str(e)), 408)
    except ServiceUnavailableError as e:
        return safe_json_response(get_user_friendly_error("SERVICE_UNAVAILABLE", str(e)), 503)
    except Exception as e:
        return safe_json_response(get_user_friendly_error("INTERNAL_SERVER_ERROR", str(e)), 500)


@parents_bp.route("/daily-hint", methods=["GET"])
@log_request_info
def parent_daily_hint_api():
    """오늘의 돌봄 힌트 제공 API (오늘 하루 혈당 데이터 기반)"""
    try:
        member_id = int(request.args.get("member_id", 1))
        date = request.args.get("date")  # YYYY-MM-DD 형식
        
        # 회원 정보 확인
        member_info = get_member_info(member_id)
        if not member_info:
            raise NotFoundError("회원을 찾을 수 없습니다.")
        
        # 날짜 설정 (기본값: 오늘)
        if not date:
            from datetime import datetime
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 오늘의 혈당 데이터 조회
        glucose_data = get_glucose_data(member_id, date)
        
        # 오늘의 간단한 돌봄 힌트 생성
        daily_hints = generate_daily_care_hints(glucose_data, member_info, date)
        
        return safe_json_response({
            "daily_hints": daily_hints,
            "date": date,
            "member_info": {
                "age": member_info.get('age'),
                "diabetes_type": member_info.get('diabetes_type')
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


def generate_daily_care_hints(glucose_data, member_info, date):
    """오늘의 구체적인 돌봄 힌트 생성"""
    if not glucose_data:
        return [
            "오늘 혈당 데이터가 없어요. 측정을 시작해보세요!",
            "아이의 혈당 패턴을 파악하기 위해 정기적인 측정이 필요해요."
        ]
    
    # 오늘의 혈당 요약 계산
    glucose_values = [data.glucose_mg_dl for data in glucose_data]
    avg_glucose = sum(glucose_values) / len(glucose_values)
    max_glucose = max(glucose_values)
    min_glucose = min(glucose_values)
    
    # 고혈당/저혈당 횟수
    hyper_count = sum(1 for glucose in glucose_values if glucose > 180)
    hypo_count = sum(1 for glucose in glucose_values if glucose < 70)
    
    hints = []
    
    # 1. 시간대별 구체적인 패턴 분석 (우선순위 높음)
    time_pattern_hints = analyze_daily_time_patterns(glucose_data)
    hints.extend(time_pattern_hints)
    
    # 2. 혈당 스파이크 분석
    spike_hints = analyze_glucose_spikes(glucose_data)
    hints.extend(spike_hints)
    
    # 3. 고혈당/저혈당 구체적인 알림
    if hyper_count > 0:
        if hyper_count == 1:
            hints.append("오늘 고혈당이 1회 있었어요. 내일은 반찬에 단백질을 조금 더 넣어주시면 좋아요.")
        else:
            hints.append(f"오늘 고혈당이 {hyper_count}회 있었어요. 식사 후 가벼운 산책을 권장해요.")
    
    if hypo_count > 0:
        if hypo_count == 1:
            hints.append("오늘 저혈당이 1회 있었어요. 간식 시간을 조정해보세요.")
        else:
            hints.append(f"오늘 저혈당이 {hypo_count}회 있었어요. 간식 섭취를 늘려보세요.")
    
    # 4. 전체적인 혈당 상태 (간단하게)
    if avg_glucose <= 100 and hyper_count == 0 and hypo_count == 0:
        hints.append("오늘 하루 퀘스트 완료됐어요 👏 아이에게 칭찬 한마디 해주세요.")
    elif avg_glucose <= 120 and hyper_count == 0 and hypo_count == 0:
        hints.append("오늘도 잘 관리했어요! 내일도 이렇게 유지해보세요! ✨")
    elif avg_glucose <= 140 and hyper_count <= 1:
        hints.append("오늘도 괜찮게 관리했어요! 조금만 더 노력하면 완벽할 거예요! 💪")
    else:
        hints.append("오늘은 조금 힘들었을 수 있어요. 내일은 더 좋은 하루가 될 거예요! 💙")
    
    return hints


def analyze_daily_time_patterns(glucose_data):
    """오늘의 시간대별 구체적인 패턴 분석"""
    hints = []
    
    # 시간대별 혈당 분류
    morning_glucose = []
    afternoon_glucose = []
    evening_glucose = []
    
    for data in glucose_data:
        time_str = data.time
        if isinstance(time_str, str):
            hour = int(time_str.split(':')[0])
            glucose = data.glucose_mg_dl
            
            if 6 <= hour < 12:
                morning_glucose.append((hour, glucose))
            elif 12 <= hour < 18:
                afternoon_glucose.append((hour, glucose))
            else:
                evening_glucose.append((hour, glucose))
    
    # 아침 혈당 패턴 분석
    if morning_glucose:
        morning_values = [glucose for _, glucose in morning_glucose]
        avg_morning = sum(morning_values) / len(morning_values)
        max_morning = max(morning_values)
        
        if avg_morning > 140:
            hints.append("아침 혈당이 조금 높아요. 저녁 간식을 줄여보세요.")
        elif avg_morning < 80:
            hints.append("아침 혈당이 낮아요. 야간 저혈당을 방지하기 위해 간식을 드려보세요.")
    
    # 점심 후 혈당 패턴 분석 (가장 중요)
    if afternoon_glucose:
        afternoon_values = [glucose for _, glucose in afternoon_glucose]
        avg_afternoon = sum(afternoon_values) / len(afternoon_values)
        max_afternoon = max(afternoon_values)
        
        if max_afternoon > 160:
            hints.append("점심 뒤에 혈당이 조금 올랐어요. 내일은 반찬에 단백질을 조금 더 넣어주시면 좋아요.")
        elif avg_afternoon < 100:
            hints.append("점심 후 혈당이 낮아요. 점심 식사량을 조금 늘려보세요.")
        elif 140 < avg_afternoon <= 160:
            hints.append("점심 뒤에 혈당이 조금 올랐어요. 내일은 반찬에 단백질을 조금 더 넣어주시면 좋아요.")
    
    # 저녁 혈당 패턴 분석
    if evening_glucose:
        evening_values = [glucose for _, glucose in evening_glucose]
        avg_evening = sum(evening_values) / len(evening_values)
        max_evening = max(evening_values)
        
        if avg_evening > 150 or max_evening > 180:
            hints.append("저녁 혈당이 높아요. 저녁 식사 후 가벼운 산책을 해보세요.")
        elif avg_evening < 90:
            hints.append("저녁 혈당이 낮아요. 저녁 간식을 추가해보세요.")
    
    return hints


def analyze_glucose_spikes(glucose_data):
    """혈당 스파이크 분석"""
    hints = []
    
    if len(glucose_data) < 2:
        return hints
    
    # 시간순으로 정렬
    sorted_data = sorted(glucose_data, key=lambda x: x.time)
    
    spike_count = 0
    for i in range(1, len(sorted_data)):
        prev_glucose = sorted_data[i-1].glucose_mg_dl
        curr_glucose = sorted_data[i].glucose_mg_dl
        
        # 30mg/dL 이상 상승을 스파이크로 간주
        if curr_glucose - prev_glucose >= 30:
            spike_count += 1
    
    if spike_count > 0:
        if spike_count == 1:
            hints.append("오늘 혈당 급상승이 1회 있었어요. 스트레스 관리에 신경써보세요.")
        else:
            hints.append(f"오늘 혈당 급상승이 {spike_count}회 있었어요. 규칙적인 식사 시간을 지켜보세요.")
    
    return hints


def get_daily_time_hints(glucose_data):
    """오늘의 시간대별 간단한 힌트"""
    hints = []
    
    # 시간대별 혈당 분류
    morning_glucose = []
    afternoon_glucose = []
    evening_glucose = []
    
    for data in glucose_data:
        time_str = data.time
        if isinstance(time_str, str):
            hour = int(time_str.split(':')[0])
            glucose = data.glucose_mg_dl
            
            if 6 <= hour < 12:
                morning_glucose.append(glucose)
            elif 12 <= hour < 18:
                afternoon_glucose.append(glucose)
            else:
                evening_glucose.append(glucose)
    
    # 아침 혈당 힌트
    if morning_glucose:
        avg_morning = sum(morning_glucose) / len(morning_glucose)
        if avg_morning > 140:
            hints.append("아침 혈당이 높아요. 저녁 간식을 줄여보세요.")
        elif avg_morning < 80:
            hints.append("아침 혈당이 낮아요. 야간 간식을 추가해보세요.")
    
    # 점심 후 혈당 힌트
    if afternoon_glucose:
        avg_afternoon = sum(afternoon_glucose) / len(afternoon_glucose)
        if avg_afternoon > 160:
            hints.append("점심 후 혈당이 높아요. 내일은 반찬에 단백질을 더 넣어주세요.")
        elif avg_afternoon < 100:
            hints.append("점심 후 혈당이 낮아요. 점심 식사량을 늘려보세요.")
    
    # 저녁 혈당 힌트
    if evening_glucose:
        avg_evening = sum(evening_glucose) / len(evening_glucose)
        if avg_evening > 150:
            hints.append("저녁 혈당이 높아요. 저녁 식사 후 산책을 해보세요.")
        elif avg_evening < 90:
            hints.append("저녁 혈당이 낮아요. 저녁 간식을 추가해보세요.")
    
    return hints


def get_diabetes_management_hints(hint_type, member_info):
    """당뇨 관리 힌트 생성"""
    age = member_info.get('age', 10)
    diabetes_type = member_info.get('diabetes_type', '1형')
    
    hints = {
        "general": [
            "정기적인 혈당 측정을 통해 패턴을 파악하세요.",
            "아이와 함께 혈당 관리 목표를 설정하고 달성했을 때 칭찬해주세요.",
            "혈당 일지를 꾸준히 작성하여 의료진과 상담할 때 활용하세요.",
            "스트레스는 혈당에 영향을 줄 수 있으니 아이의 감정 상태를 관찰하세요.",
            "충분한 수면과 규칙적인 생활 패턴을 유지하세요."
        ],
        "nutrition": [
            "탄수화물 섭취량을 일정하게 유지하세요.",
            "식사 전후 혈당을 측정하여 음식의 영향을 파악하세요.",
            "간식은 혈당에 미치는 영향을 고려하여 선택하세요.",
            "충분한 수분 섭취를 권장하세요 (하루 8잔 이상).",
            "식사 시간을 규칙적으로 유지하세요."
        ],
        "exercise": [
            "운동 전후 혈당을 측정하여 안전한 운동 강도를 파악하세요.",
            "저강도 운동(산책, 자전거)을 권장합니다.",
            "운동 중 저혈당 증상이 나타나면 즉시 중단하세요.",
            "운동 후 혈당 회복 패턴을 관찰하세요.",
            "아이가 좋아하는 운동을 함께 찾아보세요."
        ],
        "emergency": [
            "저혈당 증상(어지러움, 땀, 떨림)이 나타나면 즉시 당분을 섭취하세요.",
            "응급 상황 시 의료진 연락처를 항상 준비해두세요.",
            "고혈당 증상(갈증, 빈번한 소변)이 지속되면 의료진과 상담하세요.",
            "응급 처치 방법을 가족 모두가 알고 있어야 합니다.",
            "응급 상황 시 침착하게 대처하는 것이 중요합니다."
        ]
    }
    
    # 나이에 따른 맞춤형 힌트 추가
    if age < 10:
        hints["general"].extend([
            "아이의 혈당 관리를 게임처럼 재미있게 만들어보세요.",
            "혈당이 좋을 때마다 작은 보상을 주세요.",
            "아이가 이해할 수 있는 언어로 설명해주세요."
        ])
    elif age < 15:
        hints["general"].extend([
            "아이가 스스로 혈당을 관리할 수 있도록 점진적으로 책임을 주세요.",
            "혈당 관리에 대한 아이의 의견을 들어보세요.",
            "친구들과의 관계에서 당뇨 관리의 어려움을 이해해주세요."
        ])
    
    # 당뇨 타입별 힌트 추가
    if diabetes_type == "1형":
        hints["general"].extend([
            "인슐린 주사 시간을 정확히 지키세요.",
            "인슐린 보관 방법을 올바르게 관리하세요.",
            "케톤체 검사를 정기적으로 실시하세요."
        ])
    elif diabetes_type == "2형":
        hints["general"].extend([
            "체중 관리를 통해 혈당 조절에 도움을 주세요.",
            "식단 조절과 운동을 통한 생활습관 개선에 집중하세요.",
            "의료진의 처방에 따라 약물을 복용하세요."
        ])
    
    return hints.get(hint_type, hints["general"])


def generate_comprehensive_care_hints(glucose_data, glucose_summary, member_info):
    """혈당 데이터와 요약을 기반으로 한 통합된 돌봄 힌트 생성"""
    if not glucose_data:
        return [
            "혈당 데이터가 없어서 구체적인 조언을 드리기 어려워요. 혈당 측정을 시작해보세요!",
            "아이의 혈당 패턴을 파악하기 위해 정기적인 측정이 필요해요.",
            "정기적인 혈당 측정을 통해 패턴을 파악하세요.",
            "아이와 함께 혈당 관리 목표를 설정하고 달성했을 때 칭찬해주세요."
        ]
    
    care_hints = []
    
    # 1. 혈당 상태 기반 메시지
    avg_glucose = glucose_summary.get('average_glucose', 0)
    tir_percentage = glucose_summary.get('tir_percentage', 0)
    
    if avg_glucose <= 100 and tir_percentage >= 90:
        care_hints.append(f"이번 주 평균 혈당이 {avg_glucose}mg/dL로 아주 좋아요! 👏 아이에게 칭찬해주세요.")
        care_hints.append("완벽한 혈당 관리입니다. 아이가 정말 잘하고 있어요! 🌟")
    elif avg_glucose <= 120 and tir_percentage >= 80:
        care_hints.append(f"이번 주 평균 혈당이 {avg_glucose}mg/dL로 양호해요. 현재 관리를 잘 유지해주세요.")
        care_hints.append("훌륭한 관리예요! 아이의 노력이 보여요. 계속 이렇게 해주세요! 💪")
    elif avg_glucose <= 140 and tir_percentage >= 70:
        care_hints.append(f"이번 주 평균 혈당이 {avg_glucose}mg/dL로 조금 높아요. 내일은 간식을 조금 줄여보세요.")
        care_hints.append("괜찮은 상태예요. 조금만 더 노력하면 더 좋아질 거예요! 화이팅! ✨")
    else:
        care_hints.append(f"이번 주 평균 혈당이 {avg_glucose}mg/dL로 높아요. 식단 조절이 필요해 보여요.")
        care_hints.append("오늘은 조금 어려웠을 수 있어요. 하지만 포기하지 말고 함께 해봐요! 💙")
    
    # 2. 고혈당/저혈당 패턴 분석
    hyper_count = glucose_summary.get('hyperglycemia_count', 0)
    hypo_count = glucose_summary.get('hypoglycemia_count', 0)
    
    if hyper_count > 0:
        if hyper_count == 1:
            care_hints.append("오늘 고혈당이 1회 있었어요. 내일은 반찬에 단백질을 조금 더 넣어주시면 좋아요.")
        elif hyper_count <= 3:
            care_hints.append(f"이번 주 고혈당이 {hyper_count}회 있었어요. 식사 후 가벼운 산책을 권장해요.")
        else:
            care_hints.append(f"이번 주 고혈당이 {hyper_count}회로 많아요. 의료진과 상담을 권장해요.")
    
    if hypo_count > 0:
        if hypo_count == 1:
            care_hints.append("오늘 저혈당이 1회 있었어요. 간식 시간을 조정해보세요.")
        else:
            care_hints.append(f"이번 주 저혈당이 {hypo_count}회 있었어요. 간식 섭취를 늘려보세요.")
    
    # 3. 혈당 변동성 분석
    variability = glucose_summary.get('glucose_variability', 0)
    if variability < 30:
        care_hints.append("혈당이 안정적으로 유지되고 있어요! 현재 관리법을 계속 유지해주세요.")
    elif variability < 50:
        care_hints.append("혈당 변동이 조금 있네요. 규칙적인 식사 시간을 지켜보세요.")
    else:
        care_hints.append("혈당 변동이 크네요. 스트레스 관리와 충분한 수면을 권장해요.")
    
    # 4. 시간대별 패턴 분석
    time_pattern_hints = analyze_time_patterns(glucose_data)
    care_hints.extend(time_pattern_hints)
    
    # 5. 퀘스트 완료 관련 메시지
    if avg_glucose <= 120 and tir_percentage >= 80:
        care_hints.append("오늘 하루 퀘스트 완료됐어요 👏 아이에게 칭찬 한마디 해주세요.")
        care_hints.append("혈당 관리가 훌륭해요! 아이와 함께 작은 보상을 나눠보세요.")
    elif avg_glucose <= 140 and tir_percentage >= 70:
        care_hints.append("오늘도 잘 관리했어요! 아이의 노력을 인정해주세요.")
        care_hints.append("혈당이 안정적이에요. 내일도 이렇게 유지해보세요.")
    else:
        care_hints.append("오늘은 조금 힘들었을 수 있어요. 아이를 격려해주세요.")
        care_hints.append("내일은 더 나은 하루가 될 거예요. 함께 노력해봐요.")
    
    # 6. 일반적인 당뇨 관리 팁 추가
    general_tips = get_general_diabetes_tips(member_info)
    care_hints.extend(general_tips)
    
    return care_hints


def get_general_diabetes_tips(member_info):
    """일반적인 당뇨 관리 팁"""
    age = member_info.get('age', 10)
    diabetes_type = member_info.get('diabetes_type', '1형')
    
    tips = [
        "혈당 일지를 꾸준히 작성하여 의료진과 상담할 때 활용하세요.",
        "충분한 수면과 규칙적인 생활 패턴을 유지하세요.",
        "충분한 수분 섭취를 권장하세요 (하루 8잔 이상)."
    ]
    
    # 나이별 맞춤 팁
    if age < 10:
        tips.append("아이의 혈당 관리를 게임처럼 재미있게 만들어보세요.")
        tips.append("혈당이 좋을 때마다 작은 보상을 주세요.")
    elif age < 15:
        tips.append("아이가 스스로 혈당을 관리할 수 있도록 점진적으로 책임을 주세요.")
        tips.append("혈당 관리에 대한 아이의 의견을 들어보세요.")
    
    # 당뇨 타입별 팁
    if diabetes_type == "1형":
        tips.append("인슐린 주사 시간을 정확히 지키세요.")
        tips.append("케톤체 검사를 정기적으로 실시하세요.")
    elif diabetes_type == "2형":
        tips.append("체중 관리를 통해 혈당 조절에 도움을 주세요.")
        tips.append("식단 조절과 운동을 통한 생활습관 개선에 집중하세요.")
    
    return tips


def generate_care_hints_from_glucose_data(glucose_data, member_info):
    """혈당 데이터를 기반으로 한 맞춤형 돌봄 힌트 생성"""
    if not glucose_data:
        return [
            "혈당 데이터가 없어서 구체적인 조언을 드리기 어려워요. 혈당 측정을 시작해보세요!",
            "아이의 혈당 패턴을 파악하기 위해 정기적인 측정이 필요해요."
        ]
    
    # 혈당 요약 계산
    summary = calculate_weekly_glucose_summary(glucose_data)
    care_hints = []
    
    # 평균 혈당 기반 돌봄 메시지
    avg_glucose = summary.get('average_glucose', 0)
    if avg_glucose <= 100:
        care_hints.append(f"이번 주 평균 혈당이 {avg_glucose}mg/dL로 아주 좋아요! 👏 아이에게 칭찬해주세요.")
    elif avg_glucose <= 120:
        care_hints.append(f"이번 주 평균 혈당이 {avg_glucose}mg/dL로 양호해요. 현재 관리를 잘 유지해주세요.")
    elif avg_glucose <= 140:
        care_hints.append(f"이번 주 평균 혈당이 {avg_glucose}mg/dL로 조금 높아요. 내일은 간식을 조금 줄여보세요.")
    else:
        care_hints.append(f"이번 주 평균 혈당이 {avg_glucose}mg/dL로 높아요. 식단 조절이 필요해 보여요.")
    
    # 고혈당/저혈당 패턴 분석
    hyper_count = summary.get('hyperglycemia_count', 0)
    hypo_count = summary.get('hypoglycemia_count', 0)
    
    if hyper_count > 0:
        if hyper_count == 1:
            care_hints.append("오늘 고혈당이 1회 있었어요. 내일은 반찬에 단백질을 조금 더 넣어주시면 좋아요.")
        elif hyper_count <= 3:
            care_hints.append(f"이번 주 고혈당이 {hyper_count}회 있었어요. 식사 후 가벼운 산책을 권장해요.")
        else:
            care_hints.append(f"이번 주 고혈당이 {hyper_count}회로 많아요. 의료진과 상담을 권장해요.")
    
    if hypo_count > 0:
        if hypo_count == 1:
            care_hints.append("오늘 저혈당이 1회 있었어요. 간식 시간을 조정해보세요.")
        else:
            care_hints.append(f"이번 주 저혈당이 {hypo_count}회 있었어요. 간식 섭취를 늘려보세요.")
    
    # 혈당 변동성 분석
    variability = summary.get('glucose_variability', 0)
    if variability < 30:
        care_hints.append("혈당이 안정적으로 유지되고 있어요! 현재 관리법을 계속 유지해주세요.")
    elif variability < 50:
        care_hints.append("혈당 변동이 조금 있네요. 규칙적인 식사 시간을 지켜보세요.")
    else:
        care_hints.append("혈당 변동이 크네요. 스트레스 관리와 충분한 수면을 권장해요.")
    
    # 시간대별 패턴 분석
    time_pattern_hints = analyze_time_patterns(glucose_data)
    care_hints.extend(time_pattern_hints)
    
    # 퀘스트 완료 관련 메시지
    quest_hints = generate_quest_related_hints(summary)
    care_hints.extend(quest_hints)
    
    # 격려 메시지
    encouragement = generate_encouragement_message(summary)
    if encouragement:
        care_hints.append(encouragement)
    
    return care_hints


def analyze_time_patterns(glucose_data):
    """시간대별 혈당 패턴 분석"""
    hints = []
    
    # 시간대별 혈당 데이터 분류
    morning_glucose = []
    afternoon_glucose = []
    evening_glucose = []
    
    for data in glucose_data:
        time_str = data.time
        if isinstance(time_str, str):
            hour = int(time_str.split(':')[0])
            glucose = data.glucose_mg_dl
            
            if 6 <= hour < 12:
                morning_glucose.append(glucose)
            elif 12 <= hour < 18:
                afternoon_glucose.append(glucose)
            else:
                evening_glucose.append(glucose)
    
    # 아침 혈당 패턴
    if morning_glucose:
        avg_morning = sum(morning_glucose) / len(morning_glucose)
        if avg_morning > 140:
            hints.append("아침 혈당이 조금 높아요. 저녁 간식을 줄여보세요.")
        elif avg_morning < 80:
            hints.append("아침 혈당이 낮아요. 야간 저혈당을 방지하기 위해 간식을 드려보세요.")
    
    # 점심 후 혈당 패턴
    if afternoon_glucose:
        avg_afternoon = sum(afternoon_glucose) / len(afternoon_glucose)
        if avg_afternoon > 160:
            hints.append("점심 뒤에 혈당이 조금 올랐어요. 내일은 반찬에 단백질을 조금 더 넣어주시면 좋아요.")
        elif avg_afternoon < 100:
            hints.append("점심 후 혈당이 낮아요. 점심 식사량을 조금 늘려보세요.")
    
    # 저녁 혈당 패턴
    if evening_glucose:
        avg_evening = sum(evening_glucose) / len(evening_glucose)
        if avg_evening > 150:
            hints.append("저녁 혈당이 높아요. 저녁 식사 후 가벼운 산책을 해보세요.")
        elif avg_evening < 90:
            hints.append("저녁 혈당이 낮아요. 저녁 간식을 추가해보세요.")
    
    return hints


def generate_quest_related_hints(summary):
    """퀘스트 관련 돌봄 힌트 생성"""
    hints = []
    
    # 혈당 상태가 좋을 때
    avg_glucose = summary.get('average_glucose', 0)
    tir_percentage = summary.get('tir_percentage', 0)
    
    if avg_glucose <= 120 and tir_percentage >= 80:
        hints.append("오늘 하루 퀘스트 완료됐어요 👏 아이에게 칭찬 한마디 해주세요.")
        hints.append("혈당 관리가 훌륭해요! 아이와 함께 작은 보상을 나눠보세요.")
    elif avg_glucose <= 140 and tir_percentage >= 70:
        hints.append("오늘도 잘 관리했어요! 아이의 노력을 인정해주세요.")
        hints.append("혈당이 안정적이에요. 내일도 이렇게 유지해보세요.")
    else:
        hints.append("오늘은 조금 힘들었을 수 있어요. 아이를 격려해주세요.")
        hints.append("내일은 더 나은 하루가 될 거예요. 함께 노력해봐요.")
    
    return hints


def generate_encouragement_message(summary):
    """격려 메시지 생성"""
    avg_glucose = summary.get('average_glucose', 0)
    tir_percentage = summary.get('tir_percentage', 0)
    
    if avg_glucose <= 100 and tir_percentage >= 90:
        return "정말 대단해요! 완벽한 혈당 관리입니다. 아이가 정말 잘하고 있어요! 🌟"
    elif avg_glucose <= 120 and tir_percentage >= 80:
        return "훌륭한 관리예요! 아이의 노력이 보여요. 계속 이렇게 해주세요! 💪"
    elif avg_glucose <= 140 and tir_percentage >= 70:
        return "괜찮은 상태예요. 조금만 더 노력하면 더 좋아질 거예요! 화이팅! ✨"
    else:
        return "오늘은 조금 어려웠을 수 있어요. 하지만 포기하지 말고 함께 해봐요! 💙"


@parents_bp.route("/glucose/correlation", methods=["GET"])
@log_request_info
def parent_glucose_analysis_api():
    """일일 혈당 변화 종합 분석 API (음식 + 운동 + 혈당 통합 분석)"""
    try:
        # 요청 파라미터 검증
        member_id = request.args.get("member_id")
        if not member_id:
            raise ValidationError("member_id는 필수 파라미터입니다.")
        
        try:
            member_id = int(member_id)
            if member_id <= 0:
                raise ValidationError("member_id는 양수여야 합니다.")
        except ValueError:
            raise ValidationError("member_id는 숫자여야 합니다.")
        
        # 날짜는 항상 오늘로 설정
        from datetime import datetime
        date = datetime.now().strftime("%Y-%m-%d")
        
        # 회원 정보 확인
        member_info = get_member_info(member_id)
        if not member_info:
            raise NotFoundError(f"회원 ID {member_id}를 찾을 수 없습니다.")
        
        # 해당 날짜의 모든 데이터 조회
        try:
            food_data = get_food_data(member_id, date)
            exercise_data = get_exercise_data(member_id, date)
            glucose_data = get_glucose_data(member_id, date)
        except Exception as e:
            raise DatabaseError(f"데이터 조회 중 오류가 발생했습니다: {str(e)}")
        
        # 혈당 데이터 유효성 검증
        handle_glucose_data_error(glucose_data, member_id)
        
        # 음식-혈당 영향 분석
        try:
            food_impacts = analyze_food_glucose_impact(food_data, glucose_data)
        except Exception as e:
            raise DataIntegrityError(f"음식-혈당 분석 중 오류가 발생했습니다: {str(e)}")
        
        # 운동-혈당 영향 분석
        try:
            exercise_impacts = analyze_exercise_glucose_impact(exercise_data, glucose_data)
        except Exception as e:
            raise DataIntegrityError(f"운동-혈당 분석 중 오류가 발생했습니다: {str(e)}")
        
        # 요약 통계 계산
        try:
            # 음식 분석 통계
            total_food_hyperglycemia = sum(impact.get('hyperglycemia_count', 0) for impact in food_impacts)
            total_food_hypoglycemia = sum(impact.get('hypoglycemia_count', 0) for impact in food_impacts)
            avg_food_score = sum(impact.get('glucose_score', 0) for impact in food_impacts) / len(food_impacts) if food_impacts else 0
            
            # 운동 분석 통계
            avg_exercise_score = sum(impact.get('exercise_score', 0) for impact in exercise_impacts) / len(exercise_impacts) if exercise_impacts else 0
            total_duration = sum(impact.get('duration_minutes', 0) for impact in exercise_impacts if impact.get('duration_minutes'))
            
            # 전체 통계
            total_hyperglycemia = total_food_hyperglycemia
            total_hypoglycemia = total_food_hypoglycemia
            
        except Exception as e:
            raise DataIntegrityError(f"통계 계산 중 오류가 발생했습니다: {str(e)}")
        
        # 응답 데이터 구성
        response_data = {
            "date": date,
            "member_id": member_id,
            "member_info": {
                "age": member_info.get('age'),
                "diabetes_type": member_info.get('diabetes_type'),
                "gender": member_info.get('gender'),
                "height": member_info.get('height'),
                "weight": member_info.get('weight')
            },
            "food_analysis": {
                "impacts": food_impacts,
                "summary": {
                    "total_food_items": len(food_impacts),
                    "total_hyperglycemia": total_food_hyperglycemia,
                    "total_hypoglycemia": total_food_hypoglycemia,
                    "average_score": round(avg_food_score, 1)
                }
            },
            "exercise_analysis": {
                "impacts": exercise_impacts,
                "summary": {
                    "total_exercises": len(exercise_impacts),
                    "total_duration_minutes": total_duration,
                    "average_score": round(avg_exercise_score, 1)
                }
            },
            "overall_summary": {
                "total_hyperglycemia": total_hyperglycemia,
                "total_hypoglycemia": total_hypoglycemia,
                "avg_food_score": round(avg_food_score, 1),
                "avg_exercise_score": round(avg_exercise_score, 1),
                "total_food_items": len(food_impacts),
                "total_exercises": len(exercise_impacts),
                "analysis_type": "종합 혈당 분석"
            }
        }
        
        return safe_json_response(response_data)
        
    except ValidationError as e:
        return safe_json_response(get_user_friendly_error("VALIDATION_ERROR", str(e)), 400)
    except NotFoundError as e:
        return safe_json_response(get_user_friendly_error("NOT_FOUND", str(e)), 404)
    except DatabaseError as e:
        return safe_json_response(get_user_friendly_error("DATABASE_ERROR", str(e)), 500)
    except DataIntegrityError as e:
        return safe_json_response(get_user_friendly_error("GLUCOSE_DATA_ERROR", str(e)), 422)
    except TimeoutError as e:
        return safe_json_response(get_user_friendly_error("TIMEOUT_ERROR", str(e)), 408)
    except ServiceUnavailableError as e:
        return safe_json_response(get_user_friendly_error("SERVICE_UNAVAILABLE", str(e)), 503)
    except Exception as e:
        return safe_json_response(get_user_friendly_error("INTERNAL_SERVER_ERROR", str(e)), 500)