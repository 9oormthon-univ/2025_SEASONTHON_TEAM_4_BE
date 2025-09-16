"""리팩토링된 메인 애플리케이션"""

from flask import Flask
from flask_cors import CORS
from config import config

# 공통, 아이, 부모 라우트 임포트
from common.routes import combined_quest, get_quests_api
from child.routes import child_request_api, child_report_api
from parent.routes import glucose_analyze, parent_approve_api, glucose_summary_api

app = Flask(__name__)

# CORS 설정
CORS(app, 
     origins=config.CORS_ORIGINS,
     methods=config.CORS_METHODS,
     allow_headers=config.CORS_HEADERS,
     supports_credentials=True)

# 공통 라우트
app.route("/quest", methods=["GET"])(combined_quest)
app.route("/quest/list", methods=["GET"])(get_quests_api)

# 아이 관련 라우트
app.route("/child/request", methods=["POST"])(child_request_api)
app.route("/child/report", methods=["GET"])(child_report_api)

# 부모 관련 라우트
app.route("/parent/analyze", methods=["GET"])(glucose_analyze)
app.route("/parent/approve", methods=["POST"])(parent_approve_api)
app.route("/parent/report", methods=["GET"])(glucose_summary_api)


if __name__ == "__main__":
    # 데이터베이스 초기화
    from common.db import init_db
    init_db()
    
    # 서버 시작
    app.run(port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
