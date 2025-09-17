"""보안 관련 로깅 유틸리티"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request, g
from app.utils.error import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)

class SecurityLogger:
    """보안 이벤트 로깅 클래스"""
    
    @staticmethod
    def log_auth_attempt(user_identifier: str, auth_type: str, success: bool, 
                        ip_address: str = None, user_agent: str = None, 
                        error_message: str = None):
        """인증 시도 로깅"""
        event = {
            "event_type": "auth_attempt",
            "timestamp": datetime.utcnow().isoformat(),
            "user_identifier": user_identifier,
            "auth_type": auth_type,
            "success": success,
            "ip_address": ip_address or request.remote_addr if request else None,
            "user_agent": user_agent or (request.headers.get('User-Agent') if request else None),
            "error_message": error_message
        }
        
        if success:
            logger.info(f"인증 성공: {json.dumps(event, ensure_ascii=False)}")
        else:
            logger.warning(f"인증 실패: {json.dumps(event, ensure_ascii=False)}")
    
    @staticmethod
    def log_token_validation(token: str, success: bool, error_message: str = None):
        """토큰 검증 로깅"""
        event = {
            "event_type": "token_validation",
            "timestamp": datetime.utcnow().isoformat(),
            "token_prefix": token[:20] + "..." if token else None,
            "success": success,
            "ip_address": request.remote_addr if request else None,
            "error_message": error_message
        }
        
        if success:
            logger.debug(f"토큰 검증 성공: {json.dumps(event, ensure_ascii=False)}")
        else:
            logger.warning(f"토큰 검증 실패: {json.dumps(event, ensure_ascii=False)}")
    
    @staticmethod
    def log_permission_check(user_id: int, permission: str, resource: str, 
                           success: bool, error_message: str = None):
        """권한 확인 로깅"""
        event = {
            "event_type": "permission_check",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "permission": permission,
            "resource": resource,
            "success": success,
            "ip_address": request.remote_addr if request else None,
            "error_message": error_message
        }
        
        if success:
            logger.debug(f"권한 확인 성공: {json.dumps(event, ensure_ascii=False)}")
        else:
            logger.warning(f"권한 확인 실패: {json.dumps(event, ensure_ascii=False)}")
    
    @staticmethod
    def log_suspicious_activity(activity_type: str, details: Dict[str, Any], 
                              severity: str = "medium"):
        """의심스러운 활동 로깅"""
        event = {
            "event_type": "suspicious_activity",
            "timestamp": datetime.utcnow().isoformat(),
            "activity_type": activity_type,
            "severity": severity,
            "details": details,
            "ip_address": request.remote_addr if request else None,
            "user_agent": request.headers.get('User-Agent') if request else None
        }
        
        if severity == "high":
            logger.error(f"높은 위험도 의심 활동: {json.dumps(event, ensure_ascii=False)}")
        elif severity == "medium":
            logger.warning(f"중간 위험도 의심 활동: {json.dumps(event, ensure_ascii=False)}")
        else:
            logger.info(f"낮은 위험도 의심 활동: {json.dumps(event, ensure_ascii=False)}")
    
    @staticmethod
    def log_data_access(user_id: int, resource_type: str, action: str, 
                       resource_id: str = None, success: bool = True):
        """데이터 접근 로깅"""
        event = {
            "event_type": "data_access",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "resource_type": resource_type,
            "action": action,
            "resource_id": resource_id,
            "success": success,
            "ip_address": request.remote_addr if request else None
        }
        
        logger.info(f"데이터 접근: {json.dumps(event, ensure_ascii=False)}")
    
    @staticmethod
    def log_error(error: Exception, context: Dict[str, Any] = None):
        """에러 로깅"""
        event = {
            "event_type": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "ip_address": request.remote_addr if request else None,
            "user_agent": request.headers.get('User-Agent') if request else None
        }
        
        logger.error(f"에러 발생: {json.dumps(event, ensure_ascii=False)}", exc_info=True)

def log_security_event(event_type: str, **kwargs):
    """보안 이벤트 로깅 헬퍼 함수"""
    security_logger = SecurityLogger()
    
    if event_type == "auth_attempt":
        security_logger.log_auth_attempt(**kwargs)
    elif event_type == "token_validation":
        security_logger.log_token_validation(**kwargs)
    elif event_type == "permission_check":
        security_logger.log_permission_check(**kwargs)
    elif event_type == "suspicious_activity":
        security_logger.log_suspicious_activity(**kwargs)
    elif event_type == "data_access":
        security_logger.log_data_access(**kwargs)
    elif event_type == "error":
        security_logger.log_error(**kwargs)
