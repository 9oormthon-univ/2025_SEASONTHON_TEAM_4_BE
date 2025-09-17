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
    
    # 에러 핸들러 등록
    app.register_error_handler(APIError, handle_api_error)
    app.register_error_handler(Exception, handle_api_error)
    
    # API 블루프린트 등록 (url_prefix 없이)
    app.register_blueprint(api_v1_bp)
    
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
                    "parent_hint": "/parent/hint",
                    "parent_daily_hint": "/parent/daily-hint",
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
