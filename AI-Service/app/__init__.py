"""Flask 애플리케이션 팩토리"""

from flask import Flask
from flask_cors import CORS
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.init import init_db
from app.utils.error_handler import handle_api_error, APIError, safe_json_response

# 새로운 구조의 블루프린트 import
from app.api.v1.router import api_v1_bp


def create_app() -> Flask:
    """Flask 애플리케이션 팩토리"""
    app = Flask(__name__)
    
    # 설정 로드
    app.config.from_object(settings)
    
    # 로깅 설정
    setup_logging()
    
    # CORS 설정
    CORS(app, 
         origins=settings.CORS_ORIGINS,
         methods=settings.CORS_METHODS,
         allow_headers=settings.CORS_HEADERS,
         supports_credentials=True)
    
    # Content-Type 검증 미들웨어
    @app.before_request
    def validate_content_type():
        from flask import request
        if request.method in ['POST', 'PUT', 'PATCH']:
            if request.path.startswith('/api/') or request.path.startswith('/child/') or request.path.startswith('/parent/'):
                if not request.is_json and request.content_type != 'application/json':
                    from app.utils.error_handler import safe_json_response
                    from app.utils.user_messages import get_user_friendly_error
                    error_response = get_user_friendly_error("BAD_REQUEST", "Content-Type이 application/json이어야 합니다")
                    error_response["error"]["details"] = {
                        "content_type": request.content_type,
                        "expected": "application/json"
                    }
                    return safe_json_response(error_response, 415)
    
    # 에러 핸들러 등록
    from werkzeug.exceptions import MethodNotAllowed, BadRequest, NotFound as WerkzeugNotFound, UnsupportedMediaType
    app.register_error_handler(APIError, handle_api_error)
    app.register_error_handler(MethodNotAllowed, handle_api_error)
    app.register_error_handler(BadRequest, handle_api_error)
    app.register_error_handler(WerkzeugNotFound, handle_api_error)
    app.register_error_handler(UnsupportedMediaType, handle_api_error)
    app.register_error_handler(Exception, handle_api_error)
    
    # API 블루프린트 등록 (통합된 구조)
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    
    # 기존 엔드포인트도 유지 (하위 호환성)
    from app.api.v1.endpoints.health import health_bp
    from app.api.v1.endpoints.quests import quests_bp
    from app.api.v1.endpoints.parents import parents_bp
    from app.api.v1.endpoints.children import children_bp
    
    app.register_blueprint(health_bp, url_prefix='/health')
    app.register_blueprint(quests_bp, url_prefix='/quest')
    app.register_blueprint(parents_bp, url_prefix='/parent')
    app.register_blueprint(children_bp, url_prefix='/child')
    
    # 루트 엔드포인트
    @app.route('/')
    def index():
        return safe_json_response({
            "message": "AI-Service RESTful API",
            "version": "1.0.0",
            "documentation": {
                "endpoints": {
                    "health": "/health",
                    "quest": "/quest",
                    "quest_list": "/quest/list",
                    "parent_analyze": "/parent/analyze",
                    "parent_approve": "/parent/approve",
                    "parent_report": "/parent/report",
                    "child_request": "/child/request",
                    "child_report": "/child/report"
                },
                "api_v1": {
                    "health": "/api/v1/health",
                    "quests": "/api/v1/quest",
                    "parents": "/api/v1/parent",
                    "children": "/api/v1/child"
                }
            }
        })
    
    # 데이터베이스 초기화
    init_db()
    
    return app
