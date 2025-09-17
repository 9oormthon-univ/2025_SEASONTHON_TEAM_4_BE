"""에러 핸들링 및 사용자 친화적 메시지 관리"""

import logging
import traceback
from flask import request, jsonify
from werkzeug.exceptions import MethodNotAllowed, BadRequest, NotFound as WerkzeugNotFound, UnsupportedMediaType
from datetime import datetime
from typing import Dict, Any, Optional
from app.utils.monitoring import log_error_to_monitor, log_request_to_monitor

logger = logging.getLogger(__name__)


class APIError(Exception):
    """API 에러 기본 클래스"""
    
    def __init__(self, message: str, status_code: int = 500, error_code: str = None, details: Dict = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"ERROR_{status_code}"
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIError):
    """유효성 검증 에러"""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 400, "VALIDATION_ERROR", details)


class NotFoundError(APIError):
    """리소스 없음 에러"""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 404, "NOT_FOUND", details)


class DatabaseError(APIError):
    """데이터베이스 에러"""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 500, "DATABASE_ERROR", details)


class ExternalServiceError(APIError):
    """외부 서비스 에러"""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 502, "EXTERNAL_SERVICE_ERROR", details)


class ConflictError(APIError):
    """충돌 에러"""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 409, "CONFLICT", details)


class AuthenticationError(APIError):
    """인증 에러"""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 401, "AUTHENTICATION_ERROR", details)


class AuthorizationError(APIError):
    """권한 에러"""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 403, "AUTHORIZATION_ERROR", details)


class RateLimitError(APIError):
    """요청 제한 에러"""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 429, "RATE_LIMIT_ERROR", details)


class ServiceUnavailableError(APIError):
    """서비스 이용 불가 에러"""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 503, "SERVICE_UNAVAILABLE", details)


class TimeoutError(APIError):
    """타임아웃 에러"""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 408, "TIMEOUT_ERROR", details)


class DataIntegrityError(APIError):
    """데이터 무결성 에러"""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 422, "DATA_INTEGRITY_ERROR", details)


class ResourceExhaustedError(APIError):
    """리소스 고갈 에러"""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 507, "RESOURCE_EXHAUSTED", details)


class QuestError(APIError):
    """퀘스트 에러"""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 422, "QUEST_ERROR", details)


def safe_json_response(data: Any, status_code: int = 200) -> tuple:
    """안전한 JSON 응답 생성"""
    try:
        response = {
            "success": status_code < 400,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        return jsonify(response), status_code
    except Exception as e:
        logger.error(f"JSON 응답 생성 실패: {e}")
        return jsonify({
            "success": False,
            "error": "응답 생성 중 오류가 발생했습니다",
            "timestamp": datetime.now().isoformat()
        }), 500


def handle_api_error(error: Exception) -> tuple:
    """API 에러 핸들러"""
    
    # 요청 정보 로깅
    try:
        log_request_to_monitor(
            method=request.method,
            path=request.path,
            status_code=getattr(error, 'status_code', 500),
            duration=0,
            error=str(error)
        )
    except:
        pass
    
    # 에러 로깅
    try:
        log_error_to_monitor(
            error_type=type(error).__name__,
            error_message=str(error),
            traceback=traceback.format_exc(),
            request_path=request.path,
            request_method=request.method
        )
    except:
        pass
    
    # APIError인 경우
    if isinstance(error, APIError):
        logger.warning(f"API 에러: {error.message} (코드: {error.error_code})")
        
        # 사용자 친화적 메시지 가져오기
        from app.utils.user_messages import get_user_friendly_error
        user_friendly_response = get_user_friendly_error(error.error_code, error.message)
        
        # 상세 정보 추가
        user_friendly_response["error"]["details"] = error.details
        
        return safe_json_response(user_friendly_response, error.status_code)
    
    # Werkzeug 예외 처리
    if isinstance(error, MethodNotAllowed):
        logger.warning(f"허용되지 않은 메서드: {request.method} {request.path}")
        from app.utils.user_messages import get_user_friendly_error
        error_response = get_user_friendly_error("METHOD_NOT_ALLOWED")
        error_response["error"]["details"] = {
            "allowed_methods": getattr(error, 'valid_methods', []),
            "requested_method": request.method
        }
        return safe_json_response(error_response, 405)
    
    if isinstance(error, BadRequest):
        logger.warning(f"잘못된 요청: {request.method} {request.path} - {str(error)}")
        from app.utils.user_messages import get_user_friendly_error
        error_response = get_user_friendly_error("BAD_REQUEST", str(error))
        return safe_json_response(error_response, 400)
    
    if isinstance(error, WerkzeugNotFound):
        logger.warning(f"리소스를 찾을 수 없음: {request.method} {request.path}")
        from app.utils.user_messages import get_user_friendly_error
        error_response = get_user_friendly_error("NOT_FOUND")
        error_response["error"]["details"] = {
            "path": request.path
        }
        return safe_json_response(error_response, 404)
    
    if isinstance(error, UnsupportedMediaType):
        logger.warning(f"지원되지 않는 미디어 타입: {request.method} {request.path} - {request.content_type}")
        from app.utils.user_messages import get_user_friendly_error
        error_response = get_user_friendly_error("BAD_REQUEST", "Content-Type이 application/json이어야 합니다")
        error_response["error"]["details"] = {
            "content_type": request.content_type,
            "expected": "application/json"
        }
        return safe_json_response(error_response, 415)
    
    # 일반 예외인 경우
    logger.error(f"예상치 못한 에러: {str(error)}", exc_info=True)
    return safe_json_response({
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "서버 내부 오류가 발생했습니다",
            "status_code": 500,
            "details": {
                "type": type(error).__name__,
                "message": str(error)
            }
        }
    }, 500)


def validate_required_params(params: list) -> list:
    """필수 파라미터 검증"""
    missing_params = []
    for param in params:
        # GET 요청의 경우 args에서만 확인
        if request.method == 'GET':
            if param not in request.args:
                missing_params.append(param)
        else:
            # POST/PUT 등의 경우 args와 JSON 모두 확인
            json_data = {}
            if request.is_json:
                try:
                    json_data = request.get_json() or {}
                except:
                    json_data = {}
            
            if param not in request.args and param not in json_data:
                missing_params.append(param)
    
    if missing_params:
        raise ValidationError(
            f"필수 파라미터가 누락되었습니다: {', '.join(missing_params)}",
            {"missing_params": missing_params}
        )
    
    return missing_params


def log_request_info(func):
    """요청 정보 로깅 데코레이터"""
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        
        try:
            # 요청 정보 로깅
            logger.info(f"요청 시작: {request.method} {request.path}")
            logger.info(f"파라미터: {dict(request.args)}")
            
            # JSON 데이터가 있는 경우 로깅 (민감한 정보 제외)
            if request.is_json:
                try:
                    json_data = request.get_json() or {}
                    # 민감한 정보 마스킹
                    safe_json = {}
                    for key, value in json_data.items():
                        if any(sensitive in key.lower() for sensitive in ['password', 'token', 'key', 'secret']):
                            safe_json[key] = "***"
                        else:
                            safe_json[key] = value
                    logger.info(f"JSON 데이터: {safe_json}")
                except Exception as e:
                    logger.warning(f"JSON 파싱 실패: {e}")
            
            # 함수 실행
            result = func(*args, **kwargs)
            
            # 응답 시간 계산
            duration = (datetime.now() - start_time).total_seconds()
            
            # 성공 로깅
            logger.info(f"요청 완료: {request.method} {request.path} (소요시간: {duration:.3f}초)")
            
            # 모니터링 로깅
            try:
                log_request_to_monitor(
                    method=request.method,
                    path=request.path,
                    status_code=200,
                    duration=duration
                )
            except:
                pass
            
            return result
            
        except Exception as e:
            # 에러 로깅
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"요청 실패: {request.method} {request.path} - {str(e)} (소요시간: {duration:.3f}초)")
            
            # 상세 에러 정보 로깅
            if hasattr(e, 'status_code'):
                logger.error(f"에러 상태 코드: {e.status_code}")
            if hasattr(e, 'error_code'):
                logger.error(f"에러 코드: {e.error_code}")
            
            # 모니터링 에러 로깅
            try:
                log_error_to_monitor(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    traceback=traceback.format_exc(),
                    request_path=request.path,
                    request_method=request.method
                )
            except:
                pass
            
            raise
    
    wrapper.__name__ = func.__name__
    return wrapper


def validate_json_request():
    """JSON 요청 유효성 검증"""
    if not request.is_json:
        raise ValidationError("Content-Type이 application/json이어야 합니다")
    
    try:
        data = request.get_json()
        if data is None:
            raise ValidationError("유효한 JSON 데이터가 필요합니다")
        return data
    except Exception as e:
        raise ValidationError(f"JSON 파싱 오류: {str(e)}")


def validate_member_id(member_id):
    """회원 ID 유효성 검증"""
    if not member_id:
        raise ValidationError("member_id가 필요합니다")
    
    try:
        member_id = int(member_id)
        if member_id <= 0:
            raise ValidationError("member_id는 양수여야 합니다")
        return member_id
    except ValueError:
        raise ValidationError("member_id는 숫자여야 합니다")


def validate_quest_id(quest_id):
    """퀘스트 ID 유효성 검증"""
    if not quest_id:
        raise ValidationError("quest_id가 필요합니다")
    
    try:
        quest_id = int(quest_id)
        if quest_id <= 0:
            raise ValidationError("quest_id는 양수여야 합니다")
        return quest_id
    except ValueError:
        raise ValidationError("quest_id는 숫자여야 합니다")


def validate_date_format(date_str, field_name="date"):
    """날짜 형식 유효성 검증"""
    if not date_str:
        return None
    
    try:
        from datetime import datetime
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise ValidationError(f"{field_name}는 YYYY-MM-DD 형식이어야 합니다")


def validate_glucose_value(glucose_value, field_name="glucose"):
    """혈당 값 유효성 검증"""
    if glucose_value is None:
        raise ValidationError(f"{field_name} 값이 필요합니다")
    
    try:
        glucose_value = float(glucose_value)
        if glucose_value < 0 or glucose_value > 1000:
            raise ValidationError(f"{field_name}는 0-1000 범위의 값이어야 합니다")
        return glucose_value
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name}는 숫자여야 합니다")


def validate_quest_status(status):
    """퀘스트 상태 유효성 검증"""
    valid_statuses = ["요청 중", "승인", "거부", "완료"]
    if status not in valid_statuses:
        raise ValidationError(f"퀘스트 상태는 다음 중 하나여야 합니다: {', '.join(valid_statuses)}")
    return status


def validate_approval_status(status):
    """승인 상태 유효성 검증"""
    valid_statuses = ["승인", "거부"]
    if status not in valid_statuses:
        raise ValidationError(f"승인 상태는 '승인' 또는 '거부'여야 합니다")
    return status


def validate_age(age):
    """나이 유효성 검증"""
    if not age:
        raise ValidationError("나이가 필요합니다")
    
    try:
        age = int(age)
        if age < 0 or age > 120:
            raise ValidationError("나이는 0-120 범위의 값이어야 합니다")
        return age
    except (ValueError, TypeError):
        raise ValidationError("나이는 숫자여야 합니다")


def validate_diabetes_type(diabetes_type):
    """당뇨 타입 유효성 검증"""
    valid_types = ["1형", "2형", "임신성"]
    if diabetes_type not in valid_types:
        raise ValidationError(f"당뇨 타입은 다음 중 하나여야 합니다: {', '.join(valid_types)}")
    return diabetes_type


def handle_ai_service_error(error_message: str, original_error: Exception = None):
    """AI 서비스 에러 처리"""
    logger.error(f"AI 서비스 에러: {error_message}")
    if original_error:
        logger.error(f"원본 에러: {str(original_error)}")
    
    # AI 서비스 관련 에러 메시지 분류
    if "timeout" in error_message.lower() or "timed out" in error_message.lower():
        raise TimeoutError("AI 분석 서비스 응답 시간이 초과되었습니다")
    elif "rate limit" in error_message.lower() or "too many requests" in error_message.lower():
        raise RateLimitError("AI 서비스 요청 제한에 도달했습니다")
    elif "service unavailable" in error_message.lower() or "unavailable" in error_message.lower():
        raise ServiceUnavailableError("AI 분석 서비스를 일시적으로 이용할 수 없습니다")
    else:
        raise ExternalServiceError(f"AI 분석 서비스에서 오류가 발생했습니다: {error_message}")


def handle_database_error(error_message: str, original_error: Exception = None):
    """데이터베이스 에러 처리"""
    logger.error(f"데이터베이스 에러: {error_message}")
    if original_error:
        logger.error(f"원본 에러: {str(original_error)}")
    
    # 데이터베이스 관련 에러 메시지 분류
    if "duplicate" in error_message.lower() or "unique constraint" in error_message.lower():
        raise ConflictError("이미 존재하는 데이터입니다")
    elif "foreign key" in error_message.lower() or "constraint" in error_message.lower():
        raise DataIntegrityError("데이터 무결성 제약 조건을 위반했습니다")
    elif "timeout" in error_message.lower() or "connection" in error_message.lower():
        raise TimeoutError("데이터베이스 연결 시간이 초과되었습니다")
    else:
        raise DatabaseError("데이터베이스 처리 중 오류가 발생했습니다")


def handle_glucose_data_error(glucose_data, member_id: int):
    """혈당 데이터 에러 처리"""
    if not glucose_data:
        raise NotFoundError(f"회원 ID {member_id}의 혈당 데이터를 찾을 수 없습니다")
    
    # 혈당 데이터 유효성 검증
    for data in glucose_data:
        if not hasattr(data, 'glucose_mg_dl') or data.glucose_mg_dl is None:
            raise DataIntegrityError("혈당 데이터에 유효하지 않은 값이 포함되어 있습니다")
        
        if not hasattr(data, 'time') or not data.time:
            raise DataIntegrityError("혈당 데이터에 시간 정보가 누락되었습니다")
    
    return glucose_data


def handle_quest_error(quest_id: int, member_id: int, error_message: str = None):
    """퀘스트 에러 처리"""
    if not quest_id:
        raise ValidationError("퀘스트 ID가 필요합니다")
    
    if not member_id:
        raise ValidationError("회원 ID가 필요합니다")
    
    if error_message:
        if "not found" in error_message.lower() or "does not exist" in error_message.lower():
            raise NotFoundError(f"퀘스트 ID {quest_id}를 찾을 수 없습니다")
        elif "permission" in error_message.lower() or "unauthorized" in error_message.lower():
            raise AuthorizationError("이 퀘스트에 대한 권한이 없습니다")
        else:
            raise QuestError(f"퀘스트 처리 중 오류가 발생했습니다: {error_message}")


