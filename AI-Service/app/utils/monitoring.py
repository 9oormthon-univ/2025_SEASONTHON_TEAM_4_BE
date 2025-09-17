"""모니터링 및 성능 추적 유틸리티"""

import logging
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, deque
from threading import Lock

logger = logging.getLogger(__name__)

# 전역 모니터링 데이터 (메모리 기반)
_error_stats = defaultdict(int)
_performance_stats = deque(maxlen=1000)  # 최근 1000개 요청만 유지
_lock = Lock()


class ErrorMonitor:
    """에러 모니터링 클래스"""
    
    def __init__(self):
        self.errors = defaultdict(int)
        self.error_details = []
        self.lock = Lock()
    
    def log_error(self, error_type: str, error_message: str, traceback: str = None, 
                  request_path: str = None, request_method: str = None):
        """에러 로깅"""
        with self.lock:
            self.errors[error_type] += 1
            self.error_details.append({
                'timestamp': datetime.now(),
                'error_type': error_type,
                'error_message': error_message,
                'traceback': traceback,
                'request_path': request_path,
                'request_method': request_method
            })
            
            # 최근 100개 에러만 유지
            if len(self.error_details) > 100:
                self.error_details = self.error_details[-100:]
    
    def get_stats(self, hours: int = 24) -> Dict:
        """에러 통계 조회"""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_errors = [e for e in self.error_details if e['timestamp'] >= cutoff_time]
            
            return {
                'total_errors': sum(self.errors.values()),
                'recent_errors': len(recent_errors),
                'error_types': dict(self.errors),
                'recent_error_details': recent_errors[-10:]  # 최근 10개
            }


class PerformanceMonitor:
    """성능 모니터링 클래스"""
    
    def __init__(self):
        self.requests = deque(maxlen=1000)
        self.lock = Lock()
    
    def log_request(self, method: str, path: str, status_code: int, duration: float, 
                   error: str = None):
        """요청 로깅"""
        with self.lock:
            self.requests.append({
                'timestamp': datetime.now(),
                'method': method,
                'path': path,
                'status_code': status_code,
                'duration': duration,
                'error': error
            })
    
    def get_stats(self, hours: int = 24) -> Dict:
        """성능 통계 조회"""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_requests = [r for r in self.requests if r['timestamp'] >= cutoff_time]
            
            if not recent_requests:
                return {
                    'total_requests': 0,
                    'avg_response_time': 0,
                    'success_rate': 0,
                    'error_rate': 0,
                    'status_codes': {},
                    'slow_requests': []
                }
            
            # 기본 통계
            total_requests = len(recent_requests)
            successful_requests = len([r for r in recent_requests if r['status_code'] < 400])
            avg_response_time = sum(r['duration'] for r in recent_requests) / total_requests
            
            # 상태 코드별 통계
            status_codes = defaultdict(int)
            for r in recent_requests:
                status_codes[r['status_code']] += 1
            
            # 느린 요청 (상위 5개)
            slow_requests = sorted(recent_requests, key=lambda x: x['duration'], reverse=True)[:5]
            
            return {
                'total_requests': total_requests,
                'avg_response_time': round(avg_response_time, 3),
                'success_rate': round((successful_requests / total_requests) * 100, 2),
                'error_rate': round(((total_requests - successful_requests) / total_requests) * 100, 2),
                'status_codes': dict(status_codes),
                'slow_requests': slow_requests
            }


# 전역 모니터 인스턴스
error_monitor = ErrorMonitor()
performance_monitor = PerformanceMonitor()


def log_error_to_monitor(error_type: str, error_message: str, traceback: str = None,
                        request_path: str = None, request_method: str = None):
    """에러 모니터링 로깅"""
    try:
        error_monitor.log_error(error_type, error_message, traceback, request_path, request_method)
    except Exception as e:
        logger.error(f"에러 모니터링 로깅 실패: {e}")


def log_request_to_monitor(method: str, path: str, status_code: int, duration: float,
                          error: str = None):
    """요청 모니터링 로깅"""
    try:
        performance_monitor.log_request(method, path, status_code, duration, error)
    except Exception as e:
        logger.error(f"요청 모니터링 로깅 실패: {e}")


def get_error_statistics(hours: int = 24) -> Dict:
    """에러 통계 조회"""
    try:
        return error_monitor.get_stats(hours)
    except Exception as e:
        logger.error(f"에러 통계 조회 실패: {e}")
        return {}


def get_performance_statistics(hours: int = 24) -> Dict:
    """성능 통계 조회"""
    try:
        return performance_monitor.get_stats(hours)
    except Exception as e:
        logger.error(f"성능 통계 조회 실패: {e}")
        return {}


def get_system_metrics() -> Dict:
    """시스템 메트릭 조회"""
    try:
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"시스템 메트릭 조회 실패: {e}")
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

