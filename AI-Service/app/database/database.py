"""데이터베이스 연결 및 세션 관리"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# 데이터베이스 엔진 생성
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.FLASK_DEBUG,
    pool_pre_ping=True,  # 연결 상태 확인
    pool_recycle=3600,   # 1시간마다 연결 재생성
    pool_size=10,        # 연결 풀 크기
    max_overflow=20      # 최대 오버플로우 연결 수
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session():
    """데이터베이스 세션 컨텍스트 매니저"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"데이터베이스 세션 오류: {e}")
        raise
    finally:
        session.close()


def get_db() -> Session:
    """데이터베이스 세션 반환 (의존성 주입용)"""
    return SessionLocal()

