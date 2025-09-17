"""애플리케이션 설정"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 디버그: 환경 변수 로딩 확인
print(f".env 파일 로딩 확인:")
print(f"   OPENAI_API_KEY: {'설정됨' if os.getenv('OPENAI_API_KEY') else '설정되지 않음'}")
print(f"   DATABASE_URL: {'설정됨' if os.getenv('DATABASE_URL') else '설정되지 않음'}")

class Settings:
    """애플리케이션 설정"""
    
    # Flask 설정
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
    
    # 데이터베이스 설정
    DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://root:password@localhost:3306/danjjang')
    
    # OpenAI 설정
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your_openai_api_key_here')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    # CORS 설정
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_HEADERS = ['Content-Type', 'Authorization']
    
    # 로깅 설정
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    LOG_FILE_MAX_SIZE = int(os.getenv('LOG_FILE_MAX_SIZE', '10485760'))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 전역 설정 인스턴스
settings = Settings()

