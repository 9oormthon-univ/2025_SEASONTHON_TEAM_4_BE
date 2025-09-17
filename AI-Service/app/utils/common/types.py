"""타입 정의"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

@dataclass
class UserInfo:
    """사용자 정보 데이터 클래스"""
    member_id: int
    username: str
    email: Optional[str] = None
    auth_type: str = ""
    auth_value: Union[int, str] = ""
    age: Optional[int] = None
    diabetes_type: Optional[str] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    code: Optional[str] = None

@dataclass
class TokenInfo:
    """토큰 정보 데이터 클래스"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: str = "24시간"

@dataclass
class AuthResult:
    """인증 결과 데이터 클래스"""
    success: bool
    user_info: Optional[UserInfo] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None

# 타입 별칭
AuthPayload = Dict[str, Any]
UserPermissions = List[str]
TokenCache = Dict[str, UserInfo]
