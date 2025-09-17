"""로깅 설정"""

import logging
import logging.handlers
import os
from app.core.config import settings


def setup_logging():
    """로깅 설정 초기화"""
    
    # 로그 디렉토리 생성
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # 기존 핸들러 제거 (중복 방지)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 포맷터 설정
    formatter = logging.Formatter(settings.LOG_FORMAT)
    
    # 파일 핸들러 (로테이팅)
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=settings.LOG_FILE_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    if settings.FLASK_ENV == 'development':
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # SQLAlchemy 로깅 레벨 조정
    if settings.FLASK_ENV == 'production':
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    
    # 로깅 설정 완료 메시지
    root_logger.info(f"로깅 설정 완료 - 레벨: {settings.LOG_LEVEL}, 파일: {settings.LOG_FILE}")


def get_logger(name: str) -> logging.Logger:
    """지정된 이름의 로거 반환"""
    return logging.getLogger(name)

