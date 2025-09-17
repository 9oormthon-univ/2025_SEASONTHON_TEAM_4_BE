"""헬스체크 및 모니터링 API 엔드포인트"""

from flask import Blueprint, request, jsonify
from app.utils.error_handler import log_request_info, safe_json_response
from app.db.database import SessionLocal
from app.models.database_models import Member
from datetime import datetime
import psutil
import os

# 모니터링 모듈 import (선택적)
try:
    from app.utils.monitoring import get_error_statistics, get_performance_statistics, get_system_metrics
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

health_bp = Blueprint('health', __name__)


@health_bp.route("/", methods=["GET"])
@log_request_info
def health_check():
    """서비스 상태 확인"""
    return safe_json_response({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AI-Service",
        "version": "1.0.0"
    })


@health_bp.route("/detailed", methods=["GET"])
@log_request_info
def detailed_health_check():
    """상세 헬스체크 (DB, 시스템 리소스 포함)"""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AI-Service",
        "version": "1.0.0",
        "checks": {}
    }
    
    # 데이터베이스 연결 확인
    try:
        db = SessionLocal()
        db.query(Member).limit(1).first()
        db.close()
        health_data["checks"]["database"] = {
            "status": "healthy",
            "message": "데이터베이스 연결 정상"
        }
    except Exception as e:
        health_data["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"데이터베이스 연결 실패: {str(e)}"
        }
        health_data["status"] = "unhealthy"
    
    # 시스템 리소스 확인
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_data["checks"]["system"] = {
            "status": "healthy",
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
            "message": "시스템 리소스 정상"
        }
        
        # 리소스 사용률이 높으면 경고
        if cpu_percent > 80 or memory.percent > 80 or disk.percent > 90:
            health_data["checks"]["system"]["status"] = "warning"
            health_data["checks"]["system"]["message"] = "시스템 리소스 사용률이 높습니다"
            
    except Exception as e:
        health_data["checks"]["system"] = {
            "status": "unhealthy",
            "message": f"시스템 리소스 확인 실패: {str(e)}"
        }
        health_data["status"] = "unhealthy"
    
    # 전체 상태 결정
    if health_data["status"] == "healthy":
        status_code = 200
    else:
        status_code = 503
    
    return safe_json_response(health_data, status_code)


@health_bp.route("/readiness", methods=["GET"])
@log_request_info
def readiness_check():
    """서비스 준비 상태 확인 (Kubernetes readiness probe용)"""
    try:
        # 데이터베이스 연결 확인
        db = SessionLocal()
        db.query(Member).limit(1).first()
        db.close()
        
        return safe_json_response({
            "status": "ready",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return safe_json_response({
            "status": "not_ready",
            "message": f"서비스 준비되지 않음: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }, 503)


@health_bp.route("/liveness", methods=["GET"])
@log_request_info
def liveness_check():
    """서비스 생존 상태 확인 (Kubernetes liveness probe용)"""
    return safe_json_response({
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    })


@health_bp.route("/metrics", methods=["GET"])
@log_request_info
def metrics():
    """모니터링 메트릭 조회"""
    try:
        metrics_data = {
            "timestamp": datetime.now().isoformat(),
            "monitoring_available": MONITORING_AVAILABLE
        }
        
        if MONITORING_AVAILABLE:
            # 에러 통계
            error_stats = get_error_statistics(hours=24)
            metrics_data["error_statistics"] = error_stats
            
            # 성능 통계
            performance_stats = get_performance_statistics(hours=24)
            metrics_data["performance_statistics"] = performance_stats
            
            # 시스템 메트릭
            system_metrics = get_system_metrics()
            metrics_data["system_metrics"] = system_metrics
        else:
            metrics_data["message"] = "모니터링 모듈을 사용할 수 없습니다"
        
        return safe_json_response(metrics_data)
        
    except Exception as e:
        return safe_json_response({
            "error": "메트릭 조회 실패",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }, 500)
