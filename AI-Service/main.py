"""RESTful API 메인 애플리케이션 - 통합된 구조"""

from app import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(port=5000, debug=True)