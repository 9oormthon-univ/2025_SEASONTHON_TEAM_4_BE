"""권한 기반 접근 제어"""

from functools import wraps
from flask import g, request
from app.utils.error import AuthorizationError, get_user_friendly_error
from typing import List, Callable, Any
import logging

logger = logging.getLogger(__name__)

class Permission:
    """권한 상수"""
    READ_GLUCOSE = "read:glucose"
    WRITE_GLUCOSE = "write:glucose"
    READ_QUEST = "read:quest"
    WRITE_QUEST = "write:quest"
    READ_REPORT = "read:report"
    WRITE_REPORT = "write:report"
    MANAGE_CHILD = "manage:child"
    MANAGE_PARENT = "manage:parent"

class Role:
    """역할 상수"""
    CHILD = "child"
    PARENT = "parent"
    ADMIN = "admin"

# 역할별 권한 매핑
ROLE_PERMISSIONS = {
    Role.CHILD: [
        Permission.READ_GLUCOSE,
        Permission.READ_QUEST,
        Permission.WRITE_QUEST,
        Permission.READ_REPORT
    ],
    Role.PARENT: [
        Permission.READ_GLUCOSE,
        Permission.READ_QUEST,
        Permission.WRITE_QUEST,
        Permission.READ_REPORT,
        Permission.WRITE_REPORT,
        Permission.MANAGE_CHILD
    ],
    Role.ADMIN: [
        Permission.READ_GLUCOSE,
        Permission.WRITE_GLUCOSE,
        Permission.READ_QUEST,
        Permission.WRITE_QUEST,
        Permission.READ_REPORT,
        Permission.WRITE_REPORT,
        Permission.MANAGE_CHILD,
        Permission.MANAGE_PARENT
    ]
}

def get_user_permissions(user_info: dict) -> List[str]:
    """사용자 정보에서 권한 목록을 추출합니다."""
    auth_type = user_info.get('auth_type', '')
    
    if auth_type == 'member_id':
        return ROLE_PERMISSIONS.get(Role.CHILD, [])
    elif auth_type == 'code':
        return ROLE_PERMISSIONS.get(Role.PARENT, [])
    else:
        return []

def has_permission(user_info: dict, required_permission: str) -> bool:
    """사용자가 특정 권한을 가지고 있는지 확인합니다."""
    user_permissions = get_user_permissions(user_info)
    return required_permission in user_permissions

def require_permission(permission: str):
    """특정 권한이 필요한 데코레이터"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # 사용자 정보 확인
                if not hasattr(g, 'member_info'):
                    return get_user_friendly_error("AUTHENTICATION_ERROR", "인증이 필요합니다."), 401
                
                user_info = g.member_info
                
                # 권한 확인
                if not has_permission(user_info, permission):
                    return get_user_friendly_error("AUTHORIZATION_ERROR", f"권한이 없습니다: {permission}"), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"권한 확인 오류: {str(e)}")
                return get_user_friendly_error("INTERNAL_SERVER_ERROR", "권한 확인 중 오류가 발생했습니다."), 500
        
        return decorated_function
    return decorator

def require_any_permission(permissions: List[str]):
    """여러 권한 중 하나라도 있으면 허용하는 데코레이터"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                if not hasattr(g, 'member_info'):
                    return get_user_friendly_error("AUTHENTICATION_ERROR", "인증이 필요합니다."), 401
                
                user_info = g.member_info
                user_permissions = get_user_permissions(user_info)
                
                # 하나라도 권한이 있으면 허용
                if not any(perm in user_permissions for perm in permissions):
                    return get_user_friendly_error("AUTHORIZATION_ERROR", f"권한이 없습니다: {permissions}"), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"권한 확인 오류: {str(e)}")
                return get_user_friendly_error("INTERNAL_SERVER_ERROR", "권한 확인 중 오류가 발생했습니다."), 500
        
        return decorated_function
    return decorator

def require_all_permissions(permissions: List[str]):
    """모든 권한이 있어야 허용하는 데코레이터"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                if not hasattr(g, 'member_info'):
                    return get_user_friendly_error("AUTHENTICATION_ERROR", "인증이 필요합니다."), 401
                
                user_info = g.member_info
                user_permissions = get_user_permissions(user_info)
                
                # 모든 권한이 있어야 허용
                if not all(perm in user_permissions for perm in permissions):
                    return get_user_friendly_error("AUTHORIZATION_ERROR", f"권한이 없습니다: {permissions}"), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"권한 확인 오류: {str(e)}")
                return get_user_friendly_error("INTERNAL_SERVER_ERROR", "권한 확인 중 오류가 발생했습니다."), 500
        
        return decorated_function
    return decorator
