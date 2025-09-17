"""혈당 관련 유틸리티 함수들"""

import random
from datetime import datetime, timedelta


def format_glucose_data(readings):
    """혈당 데이터를 CGM 형식으로 변환"""
    cgm_readings = []
    for r in readings:
        # 시간 처리를 안전하게 수정
        if hasattr(r, 'time') and r.time:
            if isinstance(r.time, str):
                iso_time = f"{r.date}T{r.time}"
            else:
                # datetime.time 객체인 경우
                iso_time = f"{r.date}T{r.time.strftime('%H:%M:%S')}"
        else:
            iso_time = f"{r.date}T00:00:00"
        
        cgm_readings.append({
            "time": iso_time,
            "glucose_mg_dl": r.glucose_mg_dl,
        })
    return {"cgm_data": {"readings": cgm_readings}}


def calculate_weekly_glucose_summary(glucose_data):
    """주간 혈당 데이터 요약 계산"""
    if not glucose_data:
        return {
            'average_glucose': 0,
            'tir_percentage': 0,
            'hyperglycemia_count': 0,
            'hypoglycemia_count': 0,
            'glucose_variability': 0,
            'exercise_recovery_pattern': "데이터 부족"
        }
    
    glucose_values = [log.glucose_mg_dl for log in glucose_data]
    average_glucose = sum(glucose_values) / len(glucose_values)
    
    # TIR 계산 (70-180mg/dL)
    tir_count = sum(1 for glucose in glucose_values if 70 <= glucose <= 180)
    tir_percentage = round((tir_count / len(glucose_values)) * 100, 1)
    
    # 고혈당/저혈당 횟수
    hyperglycemia_count = sum(1 for glucose in glucose_values if glucose > 180)
    hypoglycemia_count = sum(1 for glucose in glucose_values if glucose < 70)
    
    # 혈당 변동성 (표준편차)
    variance = sum((glucose - average_glucose) ** 2 for glucose in glucose_values) / len(glucose_values)
    glucose_variability = round(variance ** 0.5, 1)
    
    # 운동 후 회복 패턴 분석
    if glucose_variability < 30:
        exercise_recovery_pattern = "안정적으로 회복되는 경향이 확인되었습니다"
    elif glucose_variability < 50:
        exercise_recovery_pattern = "대체로 안정적인 패턴을 보입니다"
    else:
        exercise_recovery_pattern = "변동성이 크지만 점진적 개선이 필요합니다"
    
    return {
        'average_glucose': round(average_glucose, 1),
        'tir_percentage': tir_percentage,
        'hyperglycemia_count': hyperglycemia_count,
        'hypoglycemia_count': hypoglycemia_count,
        'glucose_variability': glucose_variability,
        'exercise_recovery_pattern': exercise_recovery_pattern
    }


def generate_glucose_quest_pool(glucose_metrics):
    """혈당 데이터를 기반으로 개인화된 퀘스트 풀 생성"""
    avg_glucose = glucose_metrics.get('average_glucose', 120)
    max_glucose = glucose_metrics.get('max_glucose', 180)
    min_glucose = glucose_metrics.get('min_glucose', 80)
    spike_count = glucose_metrics.get('spike_count', 3)
    
    def format_number(num):
        if isinstance(num, (int, float)):
            if num == int(num):
                return str(int(num))
            else:
                return f"{num:.2f}"
        return str(num)
    
    quest_pool = {}
    
    # 평균 혈당 기반 퀘스트
    if avg_glucose > 130:
        target_avg = max(100, avg_glucose - 15)
        quest_pool["평균 혈당 개선 퀘스트"] = f"현재 평균 {format_number(avg_glucose)}mg/dL로 조금 높아! {format_number(target_avg)}mg/dL 이하로 낮추기 위해 물을 하루 8잔 마셔보자"
    elif avg_glucose > 120:
        target_avg = max(100, avg_glucose - 15)
        quest_pool["평균 혈당 유지 퀘스트"] = f"현재 평균 {format_number(avg_glucose)}mg/dL로 양호해! {format_number(target_avg)}mg/dL 목표로 혈당을 안정적으로 유지해보자"
    else:
        quest_pool["평균 혈당 유지 퀘스트"] = f"현재 평균 {format_number(avg_glucose)}mg/dL로 아주 좋아! 이 상태를 계속 유지해보자"
    
    # 최고 혈당 기반 퀘스트
    if max_glucose > 200:
        quest_pool["최고 혈당 긴급 관리 퀘스트"] = f"최고 혈당이 {format_number(max_glucose)}mg/dL로 매우 높아! 180mg/dL 이하로 낮추기 위해 심호흡 5회 후 물 2잔 마셔보자"
    elif max_glucose > 180:
        quest_pool["최고 혈당 관리 퀘스트"] = f"최고 혈당이 {format_number(max_glucose)}mg/dL로 높아! 160mg/dL 이하로 낮추기 위해 물을 충분히 마셔보자"
    elif max_glucose > 140:
        quest_pool["최고 혈당 주의 퀘스트"] = f"최고 혈당이 {format_number(max_glucose)}mg/dL로 조금 높아! 140mg/dL 이하로 유지하기 위해 혈당을 안정적으로 관리해보자"
    else:
        quest_pool["최고 혈당 유지 퀘스트"] = f"최고 혈당이 {format_number(max_glucose)}mg/dL로 안정적이야! 이 상태를 계속 유지해보자"
    
    # 스파이크 기반 퀘스트
    target_spikes = max(1, spike_count - 1)
    if spike_count > 2:
        quest_pool["혈당 스파이크 방지 퀘스트"] = f"오늘 {spike_count}번의 혈당 급상승이 있었어! {target_spikes}회 이하로 줄이기 위해 스트레스를 줄여보자"
    elif spike_count > 0:
        quest_pool["혈당 안정 챌린지 퀘스트"] = f"오늘 {spike_count}번의 혈당 급상승이 있었어! {target_spikes}회 이하로 줄이기 위해 심호흡으로 안정을 찾아보자"
    else:
        quest_pool["혈당 안정 유지 퀘스트"] = f"오늘 급상승이 없어서 아주 좋아! 이 안정적인 패턴을 계속 유지해보자"
    
    # 혈당 변동폭 기반 퀘스트
    glucose_range = max_glucose - min_glucose
    if glucose_range > 100:
        quest_pool["혈당 안정화 퀘스트"] = f"혈당 변동폭이 {format_number(glucose_range)}mg/dL로 매우 크네! 80mg/dL 이하로 줄이기 위해 규칙적인 생활을 해보자"
    elif glucose_range > 80:
        quest_pool["혈당 안정 개선 퀘스트"] = f"혈당 변동폭이 {format_number(glucose_range)}mg/dL로 크네! 60mg/dL 이하로 줄이기 위해 안정적인 패턴을 만들어보자"
    elif glucose_range > 60:
        quest_pool["혈당 안정 관리 퀘스트"] = f"혈당 변동폭이 {format_number(glucose_range)}mg/dL야! 더 안정적으로 만들기 위해 꾸준히 관리해보자"
    else:
        quest_pool["혈당 안정 유지 퀘스트"] = f"혈당 변동폭이 {format_number(glucose_range)}mg/dL로 안정적이야! 이 상태를 계속 유지해보자"
    
    # 종합 상태 기반 퀘스트
    if avg_glucose > 140 and max_glucose > 180:
        quest_pool["종합 혈당 관리 퀘스트"] = f"평균 혈당이 {format_number(avg_glucose)}mg/dL, 최고 혈당이 {format_number(max_glucose)}mg/dL로 전반적으로 높아! 개선을 위해 꾸준히 관리해보자"
    elif avg_glucose <= 100 and max_glucose <= 140:
        quest_pool["혈당 관리 우수 퀘스트"] = f"평균 혈당이 {format_number(avg_glucose)}mg/dL, 최고 혈당이 {format_number(max_glucose)}mg/dL로 아주 좋아! 이 우수한 관리를 계속 유지해보자"
    else:
        quest_pool["혈당 관리 개선 퀘스트"] = f"현재 상태를 바탕으로 조금씩 개선해보자"
    
    # 추가 혈당 관리 퀘스트들
    quest_pool["수분 섭취 퀘스트"] = "혈당 희석을 위해 하루 8잔 이상 물 마셔보자"
    quest_pool["스트레스 관리 퀘스트"] = "스트레스성 혈당 상승을 방지하기 위해 심호흡 5회 해보자"
    quest_pool["혈당 안정 퀘스트"] = "혈당을 안정적으로 유지하기 위해 규칙적인 생활을 해보자"
    quest_pool["건강 관리 퀘스트"] = "전반적인 건강 관리를 위해 꾸준히 노력해보자"
    
    return quest_pool


def select_daily_quests(glucose_quests_dict, record_quests_dict, date_str, count=4):
    """날짜별로 고정된 퀘스트 선택"""
    glucose_items = list(glucose_quests_dict.items())
    record_items = list(record_quests_dict.items())
    
    # 날짜를 시드로 사용하여 일관된 선택
    date_seed = hash(date_str) % (2**32)
    random.seed(date_seed)
    
    # 혈당 퀘스트 2개, 기록 퀘스트 2개 선택
    glucose_count = min(2, len(glucose_items))
    record_count = min(2, len(record_items))
    
    selected_glucose = random.sample(glucose_items, glucose_count)
    selected_record = random.sample(record_items, record_count)
    
    # 시드 초기화
    random.seed()
    
    result = {}
    for key, value in selected_glucose:
        result[key] = value
    for key, value in selected_record:
        result[key] = value
    
    return result


def get_default_date_range():
    """기본 날짜 범위 반환 (최근 7일)"""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")
    return start_date, end_date
