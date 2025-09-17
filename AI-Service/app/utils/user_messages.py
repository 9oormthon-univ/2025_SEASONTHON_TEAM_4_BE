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
