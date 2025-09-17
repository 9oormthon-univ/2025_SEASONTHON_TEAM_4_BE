"""입력 검증 유틸리티"""

import re
import logging
from typing import Any, Dict, List, Optional, Union
from app.utils.error import ValidationError

logger = logging.getLogger(__name__)

class InputValidator:
    """입력 검증 클래스"""
    
    @staticmethod
    def validate_member_id(member_id: Any) -> int:
        """member_id 검증"""
        if member_id is None:
            raise ValidationError("member_id는 필수입니다.")
        
        try:
            member_id = int(member_id)
            if member_id <= 0:
                raise ValidationError("member_id는 양수여야 합니다.")
            if member_id > 999999999:  # 합리적인 범위 제한
                raise ValidationError("member_id가 너무 큽니다.")
            return member_id
        except (ValueError, TypeError):
            raise ValidationError("member_id는 숫자여야 합니다.")
    
    @staticmethod
    def validate_code(code: Any) -> str:
        """code 검증"""
        if not code:
            raise ValidationError("code는 필수입니다.")
        
        if not isinstance(code, str):
            raise ValidationError("code는 문자열이어야 합니다.")
        
        code = code.strip()
        if len(code) < 3 or len(code) > 50:
            raise ValidationError("code는 3-50자 사이여야 합니다.")
        
        # 특수문자 검증 (알파벳, 숫자, 하이픈, 언더스코어만 허용)
        if not re.match(r'^[A-Za-z0-9_-]+$', code):
            raise ValidationError("code는 영문, 숫자, 하이픈, 언더스코어만 사용할 수 있습니다.")
        
        return code
    
    @staticmethod
    def validate_email(email: Any) -> str:
        """이메일 검증"""
        if not email:
            raise ValidationError("이메일은 필수입니다.")
        
        if not isinstance(email, str):
            raise ValidationError("이메일은 문자열이어야 합니다.")
        
        email = email.strip().lower()
        if len(email) > 254:  # RFC 5321 제한
            raise ValidationError("이메일이 너무 깁니다.")
        
        # 이메일 형식 검증
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError("유효한 이메일 형식이 아닙니다.")
        
        return email
    
    @staticmethod
    def validate_phone(phone: Any) -> str:
        """전화번호 검증"""
        if not phone:
            raise ValidationError("전화번호는 필수입니다.")
        
        if not isinstance(phone, str):
            raise ValidationError("전화번호는 문자열이어야 합니다.")
        
        # 숫자만 추출
        phone_digits = re.sub(r'[^\d]', '', phone)
        
        if len(phone_digits) < 10 or len(phone_digits) > 15:
            raise ValidationError("전화번호는 10-15자리여야 합니다.")
        
        return phone_digits
    
    @staticmethod
    def validate_password(password: Any) -> str:
        """비밀번호 검증"""
        if not password:
            raise ValidationError("비밀번호는 필수입니다.")
        
        if not isinstance(password, str):
            raise ValidationError("비밀번호는 문자열이어야 합니다.")
        
        if len(password) < 8:
            raise ValidationError("비밀번호는 최소 8자 이상이어야 합니다.")
        
        if len(password) > 128:
            raise ValidationError("비밀번호가 너무 깁니다.")
        
        # 복잡도 검증
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        if not (has_upper and has_lower and has_digit):
            raise ValidationError("비밀번호는 대문자, 소문자, 숫자를 포함해야 합니다.")
        
        return password
    
    @staticmethod
    def validate_date(date_str: Any) -> str:
        """날짜 형식 검증 (YYYY-MM-DD)"""
        if not date_str:
            raise ValidationError("날짜는 필수입니다.")
        
        if not isinstance(date_str, str):
            raise ValidationError("날짜는 문자열이어야 합니다.")
        
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(date_pattern, date_str):
            raise ValidationError("날짜는 YYYY-MM-DD 형식이어야 합니다.")
        
        # 실제 날짜 유효성 검증
        try:
            from datetime import datetime
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            raise ValidationError("유효하지 않은 날짜입니다.")
        
        return date_str
    
    @staticmethod
    def validate_json_payload(data: Any, required_fields: List[str]) -> Dict[str, Any]:
        """JSON 페이로드 검증"""
        if not isinstance(data, dict):
            raise ValidationError("요청 데이터는 JSON 객체여야 합니다.")
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}")
        
        return data
    
    @staticmethod
    def sanitize_string(value: Any, max_length: int = 255) -> str:
        """문자열 정리 및 검증"""
        if not isinstance(value, str):
            value = str(value)
        
        # HTML 태그 제거
        value = re.sub(r'<[^>]+>', '', value)
        
        # 특수 문자 제거 (기본적인 XSS 방지)
        value = re.sub(r'[<>"\']', '', value)
        
        # 길이 제한
        if len(value) > max_length:
            value = value[:max_length]
        
        return value.strip()

def validate_request_data(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """요청 데이터 스키마 검증"""
    validator = InputValidator()
    validated_data = {}
    
    for field, rules in schema.items():
        if field not in data:
            if rules.get('required', False):
                raise ValidationError(f"필수 필드가 누락되었습니다: {field}")
            continue
        
        value = data[field]
        field_type = rules.get('type', 'string')
        
        try:
            if field_type == 'member_id':
                validated_data[field] = validator.validate_member_id(value)
            elif field_type == 'code':
                validated_data[field] = validator.validate_code(value)
            elif field_type == 'email':
                validated_data[field] = validator.validate_email(value)
            elif field_type == 'phone':
                validated_data[field] = validator.validate_phone(value)
            elif field_type == 'password':
                validated_data[field] = validator.validate_password(value)
            elif field_type == 'date':
                validated_data[field] = validator.validate_date(value)
            elif field_type == 'string':
                max_length = rules.get('max_length', 255)
                validated_data[field] = validator.sanitize_string(value, max_length)
            else:
                validated_data[field] = value
                
        except ValidationError as e:
            raise ValidationError(f"{field}: {str(e)}")
    
    return validated_data
