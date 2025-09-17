"""API v1 라우터 등록 - 기존 엔드포인트 구조 유지"""

from flask import Blueprint
from app.api.v1.endpoints import health, quests, parents, children

# API v1 블루프린트 생성 (url_prefix 제거)
api_v1 = Blueprint('api_v1', __name__)

# 각 엔드포인트 블루프린트 등록 (기존 구조 유지)
api_v1.register_blueprint(health.health_bp, url_prefix='/health')
api_v1.register_blueprint(quests.quests_bp, url_prefix='/quest')
api_v1.register_blueprint(parents.parents_bp, url_prefix='/parent')
api_v1.register_blueprint(children.children_bp, url_prefix='/child')

# api_v1_bp로 export
api_v1_bp = api_v1