"""사용자 친화적 메시지 관리"""

from typing import Dict, Any

# 사용자 친화적 메시지 템플릿
USER_MESSAGES = {
    # 성공 메시지
    "success": {
        "quest_generated": {
            "title": "퀘스트 생성 완료",
            "message": "오늘의 개인화된 퀘스트가 생성되었습니다!",
            "type": "success"
        },
        "quest_completed": {
            "title": "퀘스트 완료",
            "message": "퀘스트를 성공적으로 완료했습니다!",
            "type": "success"
        },
        "report_generated": {
            "title": "보고서 생성 완료",
            "message": "혈당 분석 보고서가 생성되었습니다.",
            "type": "success"
        },
        "data_saved": {
            "title": "데이터 저장 완료",
            "message": "데이터가 성공적으로 저장되었습니다.",
            "type": "success"
        }
    },
    
    # 에러 메시지
    "error": {
        "VALIDATION_ERROR": {
            "title": "입력 오류",
            "message": "입력한 정보를 다시 확인해주세요.",
            "action": "올바른 형식으로 다시 입력해주세요",
            "category": "입력 오류",
            "type": "error",
            "status_code": 400,
            "number": 4001
        },
        "NOT_FOUND": {
            "title": "데이터 없음",
            "message": "요청하신 데이터를 찾을 수 없습니다.",
            "action": "다른 조건으로 검색해보세요",
            "category": "데이터 오류",
            "type": "error",
            "status_code": 404,
            "number": 4004
        },
        "DATABASE_ERROR": {
            "title": "데이터베이스 오류",
            "message": "데이터 처리 중 문제가 발생했습니다.",
            "action": "잠시 후 다시 시도해주세요",
            "category": "시스템 오류",
            "type": "error",
            "status_code": 500,
            "number": 5001
        },
        "EXTERNAL_SERVICE_ERROR": {
            "title": "외부 서비스 오류",
            "message": "외부 서비스와의 통신 중 문제가 발생했습니다.",
            "action": "잠시 후 다시 시도해주세요",
            "category": "서비스 오류",
            "type": "error",
            "status_code": 502,
            "number": 5002
        },
        "INTERNAL_SERVER_ERROR": {
            "title": "서버 오류",
            "message": "서버에서 예상치 못한 오류가 발생했습니다.",
            "action": "잠시 후 다시 시도해주세요",
            "category": "서버 오류",
            "type": "error",
            "status_code": 500,
            "number": 9999
        },
        "CONFLICT": {
            "title": "데이터 충돌",
            "message": "요청하신 작업을 수행할 수 없습니다.",
            "action": "다른 방법을 시도해보세요",
            "category": "데이터 오류",
            "type": "error",
            "status_code": 409,
            "number": 4009
        },
        "METHOD_NOT_ALLOWED": {
            "title": "허용되지 않은 메서드",
            "message": "요청하신 HTTP 메서드가 이 엔드포인트에서 지원되지 않습니다.",
            "action": "올바른 HTTP 메서드를 사용해주세요",
            "category": "요청 오류",
            "type": "error",
            "status_code": 405,
            "number": 4005
        },
        "BAD_REQUEST": {
            "title": "잘못된 요청",
            "message": "요청 형식이 올바르지 않습니다.",
            "action": "요청 형식을 확인해주세요",
            "category": "요청 오류",
            "type": "error",
            "status_code": 400,
            "number": 4000
        },
        "AUTHENTICATION_ERROR": {
            "title": "인증 실패",
            "message": "로그인이 필요합니다.",
            "action": "로그인 후 다시 시도해주세요",
            "category": "인증 오류",
            "type": "error",
            "status_code": 401,
            "number": 4001
        },
        "AUTHORIZATION_ERROR": {
            "title": "권한 없음",
            "message": "이 작업을 수행할 권한이 없습니다.",
            "action": "관리자에게 문의하세요",
            "category": "권한 오류",
            "type": "error",
            "status_code": 403,
            "number": 4003
        },
        "RATE_LIMIT_ERROR": {
            "title": "요청 제한",
            "message": "너무 많은 요청을 보내셨습니다.",
            "action": "잠시 후 다시 시도해주세요",
            "category": "제한 오류",
            "type": "error",
            "status_code": 429,
            "number": 4029
        },
        "SERVICE_UNAVAILABLE": {
            "title": "서비스 이용 불가",
            "message": "일시적으로 서비스를 이용할 수 없습니다.",
            "action": "잠시 후 다시 시도해주세요",
            "category": "서비스 오류",
            "type": "error",
            "status_code": 503,
            "number": 5003
        },
        "TIMEOUT_ERROR": {
            "title": "요청 시간 초과",
            "message": "요청 처리 시간이 초과되었습니다.",
            "action": "다시 시도해주세요",
            "category": "시간 오류",
            "type": "error",
            "status_code": 408,
            "number": 4008
        },
        "DATA_INTEGRITY_ERROR": {
            "title": "데이터 무결성 오류",
            "message": "데이터가 올바르지 않습니다.",
            "action": "데이터를 확인하고 다시 시도해주세요",
            "category": "데이터 오류",
            "type": "error",
            "status_code": 422,
            "number": 4022
        },
        "RESOURCE_EXHAUSTED": {
            "title": "리소스 부족",
            "message": "서버 리소스가 부족합니다.",
            "action": "잠시 후 다시 시도해주세요",
            "category": "리소스 오류",
            "type": "error",
            "status_code": 507,
            "number": 5007
        },
        "GLUCOSE_DATA_ERROR": {
            "title": "혈당 데이터 오류",
            "message": "혈당 데이터 처리 중 문제가 발생했습니다.",
            "action": "혈당 데이터를 확인하고 다시 시도해주세요",
            "category": "데이터 오류",
            "type": "error",
            "status_code": 422,
            "number": 4221
        },
        "QUEST_ERROR": {
            "title": "퀘스트 오류",
            "message": "퀘스트 처리 중 문제가 발생했습니다.",
            "action": "퀘스트 정보를 확인하고 다시 시도해주세요",
            "category": "퀘스트 오류",
            "type": "error",
            "status_code": 422,
            "number": 4222
        },
        "AI_SERVICE_ERROR": {
            "title": "AI 서비스 오류",
            "message": "AI 분석 서비스에서 문제가 발생했습니다.",
            "action": "잠시 후 다시 시도해주세요",
            "category": "AI 서비스 오류",
            "type": "error",
            "status_code": 502,
            "number": 5021
        }
    }
}


class UserMessageManager:
    """사용자 메시지 관리자"""
    
    @staticmethod
    def get_user_friendly_error(error_code: str, custom_message: str = None) -> Dict[str, Any]:
        """사용자 친화적 에러 메시지 반환"""
        error_template = USER_MESSAGES["error"].get(error_code, USER_MESSAGES["error"]["INTERNAL_SERVER_ERROR"])
        
        # 커스텀 메시지가 있으면 사용
        if custom_message:
            error_template = error_template.copy()
            error_template["message"] = custom_message
        
        return {
            "error": error_template,
            "success": False
        }
    
    @staticmethod
    def get_user_friendly_success(success_code: str, custom_message: str = None) -> Dict[str, Any]:
        """사용자 친화적 성공 메시지 반환"""
        success_template = USER_MESSAGES["success"].get(success_code, {
            "title": "성공",
            "message": "작업이 성공적으로 완료되었습니다.",
            "type": "success"
        })
        
        # 커스텀 메시지가 있으면 사용
        if custom_message:
            success_template = success_template.copy()
            success_template["message"] = custom_message
        
        return {
            "success": True,
            "message": success_template
        }
    
    @staticmethod
    def format_validation_error(missing_params: list) -> str:
        """유효성 검증 에러 메시지 포맷팅"""
        if len(missing_params) == 1:
            return f"{missing_params[0]}을(를) 입력해주세요."
        else:
            return f"다음 항목들을 입력해주세요: {', '.join(missing_params)}"
    
    @staticmethod
    def format_database_error(error_message: str) -> str:
        """데이터베이스 에러 메시지 포맷팅"""
        # 사용자에게 노출하기 부적절한 기술적 메시지 필터링
        technical_terms = [
            "mysql", "sqlalchemy", "connection", "timeout", "constraint",
            "foreign key", "primary key", "duplicate", "syntax error"
        ]
        
        for term in technical_terms:
            if term.lower() in error_message.lower():
                return "데이터 처리 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
        
        return error_message


# 편의 함수들
def get_user_friendly_error(error_code: str, custom_message: str = None) -> Dict[str, Any]:
    """사용자 친화적 에러 메시지 반환 (편의 함수)"""
    return UserMessageManager.get_user_friendly_error(error_code, custom_message)


def get_user_friendly_success(success_code: str, custom_message: str = None) -> Dict[str, Any]:
    """사용자 친화적 성공 메시지 반환 (편의 함수)"""
    return UserMessageManager.get_user_friendly_success(success_code, custom_message)
