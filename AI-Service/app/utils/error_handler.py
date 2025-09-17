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
        return safe_json_response({
            "error": {
                "code": error.error_code,
                "message": error.message,
                "status_code": error.status_code,
                "details": error.details
            }
        }, error.status_code)
    
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
