"""JWT 토큰 인증 유틸리티 - 확장 가능하고 효율적인 구조"""

import jwt
from functools import wraps
from flask import request, g, current_app
from app.utils.error import AuthenticationError, ValidationError, get_user_friendly_error
from app.database import get_member_info
from .input_validator import InputValidator
from .security_logger import log_security_event
from app.core.config import settings
from typing import Optional, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)

# 간단한 메모리 캐시 (프로덕션에서는 Redis 사용 권장)
_token_cache: Dict[str, Dict[str, Any]] = {}

def get_jwt_secret():
    """JWT 시크릿 키를 가져옵니다."""
    return settings.JWT_SECRET_KEY

def decode_jwt_token(token: str) -> Dict[str, Any]:
    """JWT 토큰을 디코딩합니다."""
    try:
        # 토큰 형식 검증
        if not token or not isinstance(token, str):
            raise AuthenticationError("유효하지 않은 토큰 형식입니다.")
        
        # 토큰 길이 검증 (너무 짧거나 긴 토큰 거부)
        if len(token) < 10 or len(token) > 2000:
            raise AuthenticationError("유효하지 않은 토큰 길이입니다.")
        
        # JWT 토큰 디코딩
        payload = jwt.decode(
            token, 
            get_jwt_secret(), 
            algorithms=[settings.JWT_ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "require": ["exp", "iat"]
            }
        )
        
        # 스프링에서 생성한 토큰이므로 타입 검증 생략
        
        # 발급 시간 검증 (미래 토큰 거부)
        iat = payload.get('iat')
        if iat and iat > jwt.get_unverified_header(token).get('iat', 0):
            raise AuthenticationError("유효하지 않은 토큰 발급 시간입니다.")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning(f"만료된 토큰 접근 시도: {token[:20]}...")
        raise AuthenticationError("토큰이 만료되었습니다. 다시 로그인해 주세요.")
    except jwt.InvalidTokenError as e:
        logger.warning(f"유효하지 않은 토큰 접근 시도: {str(e)}")
        raise AuthenticationError("유효하지 않은 토큰입니다.")
    except jwt.InvalidSignatureError:
        logger.warning(f"잘못된 서명의 토큰 접근 시도: {token[:20]}...")
        raise AuthenticationError("토큰 서명이 유효하지 않습니다.")
    except Exception as e:
        logger.error(f"JWT 토큰 디코딩 오류: {str(e)}", exc_info=True)
        raise AuthenticationError("토큰 처리 중 오류가 발생했습니다.")

def get_cached_user_info(token: str) -> Optional[Dict[str, Any]]:
    """캐시에서 사용자 정보를 조회합니다."""
    return _token_cache.get(token)

def cache_user_info(token: str, user_info: Dict[str, Any]):
    """사용자 정보를 캐시에 저장합니다."""
    # 캐시 크기 제한 (100개)
    if len(_token_cache) >= 100:
        # 가장 오래된 항목 제거
        oldest_token = min(_token_cache.keys())
        del _token_cache[oldest_token]
    
    _token_cache[token] = user_info

def clear_token_cache():
    """토큰 캐시를 초기화합니다."""
    _token_cache.clear()

def get_token_from_header():
    """Authorization 헤더에서 JWT 토큰을 추출합니다."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise AuthenticationError("Authorization 헤더가 없습니다.")
    
    try:
        scheme, token = auth_header.split(' ', 1)
        if scheme.lower() != 'bearer':
            raise AuthenticationError("Bearer 토큰이 필요합니다.")
        return token
    except ValueError:
        raise AuthenticationError("잘못된 Authorization 헤더 형식입니다.")

def authenticate_user(token: str, auth_type: str) -> Optional[Dict[str, Any]]:
    """사용자 인증을 수행합니다."""
    # 캐시에서 먼저 확인
    cached_info = get_cached_user_info(token)
    if cached_info:
        return cached_info
    
    # 토큰 디코딩
    payload = decode_jwt_token(token)
    
    # 인증 타입별 처리
    auth_handlers = {
        "member_id": authenticate_by_member_id,
        "code": authenticate_by_code
    }
    
    handler = auth_handlers.get(auth_type)
    if not handler:
        raise AuthenticationError(f"지원하지 않는 인증 타입: {auth_type}")
    
    user_info = handler(payload)
    return user_info

def authenticate_by_member_id(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """member_id로 사용자를 인증합니다."""
    member_id = payload.get('member_id')
    if not member_id:
        log_security_event("auth_attempt", 
                          user_identifier="unknown", 
                          auth_type="member_id", 
                          success=False, 
                          error_message="토큰에 member_id가 없습니다")
        raise AuthenticationError("토큰에 member_id가 없습니다.")
    
    try:
        # 입력 검증
        validator = InputValidator()
        member_id = validator.validate_member_id(member_id)
    except ValidationError as e:
        log_security_event("auth_attempt", 
                          user_identifier=str(member_id), 
                          auth_type="member_id", 
                          success=False, 
                          error_message=str(e))
        raise
    
    member_info = get_member_info(member_id)
    if not member_info:
        log_security_event("auth_attempt", 
                          user_identifier=str(member_id), 
                          auth_type="member_id", 
                          success=False, 
                          error_message=f"회원 ID {member_id}를 찾을 수 없습니다")
        raise AuthenticationError(f"회원 ID {member_id}를 찾을 수 없습니다.")
    
    member_info['auth_type'] = 'member_id'
    member_info['auth_value'] = member_id
    
    # 성공 로깅
    log_security_event("auth_attempt", 
                      user_identifier=str(member_id), 
                      auth_type="member_id", 
                      success=True)
    
    return member_info

def authenticate_by_code(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """code로 사용자를 인증합니다."""
    code = payload.get('code')
    if not code:
        raise AuthenticationError("토큰에 code가 없습니다.")
    
    if not isinstance(code, str) or len(code.strip()) == 0:
        raise ValidationError("code는 비어있지 않은 문자열이어야 합니다.")
    
    member_info = get_member_by_code(code)
    if not member_info:
        raise AuthenticationError(f"코드 {code}에 해당하는 회원을 찾을 수 없습니다.")
    
    member_info['auth_type'] = 'code'
    member_info['auth_value'] = code
    return member_info

def jwt_auth(auth_type: str):
    """확장 가능한 JWT 인증 데코레이터 팩토리"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # JWT 토큰 추출
                token = get_token_from_header()
                
                # 사용자 인증
                user_info = authenticate_user(token, auth_type)
                
                # 캐시에 저장
                cache_user_info(token, user_info)
                
                # g 객체에 정보 저장
                g.member_id = user_info['member_id']
                g.member_info = user_info
                g.auth_type = user_info['auth_type']
                g.auth_value = user_info['auth_value']
                
                return f(*args, **kwargs)
                
            except AuthenticationError as e:
                return get_user_friendly_error("AUTHENTICATION_ERROR", str(e)), 401
            except ValidationError as e:
                return get_user_friendly_error("VALIDATION_ERROR", str(e)), 400
            except Exception as e:
                logger.error(f"JWT 인증 오류: {str(e)}")
                return get_user_friendly_error("INTERNAL_SERVER_ERROR", "인증 처리 중 오류가 발생했습니다."), 500
        
        return decorated_function
    return decorator

# 기존 호환성을 위한 별칭
jwt_auth_member_id = lambda f: jwt_auth("member_id")(f)
jwt_auth_code = lambda f: jwt_auth("code")(f)

def get_member_by_code(code):
    """code로 회원 정보를 조회합니다."""
    try:
        from app.database import SessionLocal
        from app.models.database_models import Member
        from datetime import datetime
        
        db = SessionLocal()
        try:
            member = db.query(Member).filter(Member.code == code).first()
            if member:
                # 생년월일에서 나이 계산
                if member.birth:
                    if isinstance(member.birth, int):
                        birth_year = member.birth // 10000
                    else:
                        birth_year = member.birth.year
                    current_year = datetime.now().year
                    age = current_year - birth_year
                else:
                    age = None
                
                return {
                    'member_id': member.member_id,
                    'username': member.username,
                    'email': member.email,
                    'age': age,
                    'diabetes_type': member.diabetes_type,
                    'gender': member.gender,
                    'height': member.height,
                    'weight': member.weight,
                    'code': member.code
                }
            return None
        finally:
            db.close()
    except Exception as e:
        logger.error(f"회원 조회 오류: {str(e)}")
        return None

# 토큰 생성 관련 함수들은 스프링에서 처리하므로 제거
# Python에서는 JWT 토큰 검증과 사용자 정보 파싱만 담당

