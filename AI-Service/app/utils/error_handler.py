"""에러 핸들링 및 사용자 친화적 메시지 관리"""

import logging
import traceback
from flask import request, jsonify
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
