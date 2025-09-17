"""혈당 변화 분석 유틸리티 함수들"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import math


def calculate_glucose_change(glucose_before: float, glucose_after: float) -> float:
    """혈당 변화량 계산 (ΔBG)"""
    return glucose_after - glucose_before


def calculate_gl_index(carbs: float, fiber: float = 0) -> float:
    """혈당 지수(GL) 계산
    GL = (탄수화물 - 섬유질) * 0.8
    """
    if carbs is None:
        return 0
    return (carbs - (fiber or 0)) * 0.8


def calculate_glucose_score(glucose_change: float, gl_index: float) -> int:
    """혈당 점수 계산 (0-100)
    혈당 변화량과 GL 지수를 기반으로 점수 계산
    """
    if gl_index == 0:
        return 50  # 기본 점수
    
    # 혈당 변화량을 GL 지수로 나누어 정규화
    normalized_change = glucose_change / gl_index
    
    # 점수 계산 (0-100 범위)
    if normalized_change <= 0:
        score = 100  # 혈당이 떨어졌거나 변화 없음
    elif normalized_change <= 1:
        score = 80 - (normalized_change * 30)  # 1:1 비율까지는 양호
    elif normalized_change <= 2:
        score = 50 - ((normalized_change - 1) * 30)  # 2:1 비율까지는 보통
    else:
        score = max(0, 20 - ((normalized_change - 2) * 10))  # 2:1 초과는 나쁨
    
    return max(0, min(100, int(score)))


def classify_glucose_status(glucose_value: float) -> str:
    """혈당 상태 분류"""
    if glucose_value < 70:
        return "저혈당"
    elif glucose_value <= 140:
        return "정상"
    elif glucose_value <= 180:
        return "경계"
    else:
        return "고혈당"


def analyze_food_glucose_impact(food_data: List[Any], glucose_data: List[Any]) -> List[Dict[str, Any]]:
    """음식이 혈당에 미친 영향 분석"""
    results = []
    
    for food in food_data:
        food_time = datetime.strptime(f"{food.date} {food.time}", "%Y-%m-%d %H:%M")
        
        # 음식 섭취 전후 2시간 내의 혈당 데이터 찾기
        before_glucose = None
        after_glucose = None
        
        for glucose in glucose_data:
            glucose_time = datetime.strptime(f"{glucose.date} {glucose.time}", "%Y-%m-%d %H:%M")
            time_diff = (glucose_time - food_time).total_seconds() / 3600  # 시간 단위
            
            # 음식 섭취 전 혈당 (섭취 시점 이전의 가장 가까운 측정값)
            if time_diff <= 0:
                if before_glucose is None or time_diff > (datetime.strptime(f"{before_glucose.date} {before_glucose.time}", "%Y-%m-%d %H:%M") - food_time).total_seconds() / 3600:
                    before_glucose = glucose
            # 음식 섭취 후 혈당 (섭취 후 1-4시간 사이의 측정값)
            elif 1 <= time_diff <= 4:
                if after_glucose is None or time_diff < (datetime.strptime(f"{after_glucose.date} {after_glucose.time}", "%Y-%m-%d %H:%M") - food_time).total_seconds() / 3600:
                    after_glucose = glucose
        
        if before_glucose and after_glucose:
            # 혈당 변화량 계산
            glucose_change = calculate_glucose_change(before_glucose.glucose_mg_dl, after_glucose.glucose_mg_dl)
            
            # GL 지수 계산 (fiber가 없으므로 carbs만 사용)
            gl_index = calculate_gl_index(food.carbs, 0)
            
            # 혈당 점수 계산
            score = calculate_glucose_score(glucose_change, gl_index)
            
            # 혈당 상태 분류
            before_status = classify_glucose_status(before_glucose.glucose_mg_dl)
            after_status = classify_glucose_status(after_glucose.glucose_mg_dl)
            
            # 고혈당/저혈당 횟수 계산
            hyperglycemia_count = 1 if after_glucose.glucose_mg_dl > 180 else 0
            hypoglycemia_count = 1 if after_glucose.glucose_mg_dl < 70 else 0
            
            result = {
                "food_name": food.name,
                "meal_type": food.type,
                "carbs": food.carbs,
                "calories": food.calories,
                "gl_index": round(gl_index, 1),
                "glucose_before": before_glucose.glucose_mg_dl,
                "glucose_after": after_glucose.glucose_mg_dl,
                "glucose_change": round(glucose_change, 1),
                "glucose_score": score,
                "before_status": before_status,
                "after_status": after_status,
                "hyperglycemia_count": hyperglycemia_count,
                "hypoglycemia_count": hypoglycemia_count,
                "time_before": before_glucose.time,
                "time_after": after_glucose.time,
                "impact_summary": generate_food_impact_summary(food.name, glucose_change, gl_index, score, after_status)
            }
            
            results.append(result)
    
    return results


def analyze_exercise_glucose_impact(exercise_data: List[Any], glucose_data: List[Any]) -> List[Dict[str, Any]]:
    """운동이 혈당에 미친 영향 분석"""
    results = []
    
    for exercise in exercise_data:
        # 기존 Exercise 모델 구조에 맞게 수정
        # time 컬럼이 없으므로 created_at을 사용하되, 날짜만 사용
        exercise_time = exercise.created_at.replace(hour=12, minute=0, second=0, microsecond=0)  # 오후 12시로 가정
        
        # 운동 전후 혈당 데이터 찾기
        before_glucose = None
        after_glucose = None
        
        for glucose in glucose_data:
            glucose_time = datetime.strptime(f"{glucose.date} {glucose.time}", "%Y-%m-%d %H:%M")
            time_diff = (glucose_time - exercise_time).total_seconds() / 3600  # 시간 단위
            
            # 운동 전 혈당 (운동 시점 이전의 가장 가까운 측정값)
            if time_diff <= 0:
                if before_glucose is None or time_diff > (datetime.strptime(f"{before_glucose.date} {before_glucose.time}", "%Y-%m-%d %H:%M") - exercise_time).total_seconds() / 3600:
                    before_glucose = glucose
            # 운동 후 혈당 (운동 후 1-3시간 사이의 측정값)
            elif 1 <= time_diff <= 3:
                if after_glucose is None or time_diff < (datetime.strptime(f"{after_glucose.date} {after_glucose.time}", "%Y-%m-%d %H:%M") - exercise_time).total_seconds() / 3600:
                    after_glucose = glucose
        
        if before_glucose and after_glucose:
            # 혈당 변화량 계산
            glucose_change = calculate_glucose_change(before_glucose.glucose_mg_dl, after_glucose.glucose_mg_dl)
            
            # 운동 강도에 따른 예상 혈당 감소량 계산 (기본 강도로 설정)
            expected_decrease = calculate_expected_glucose_decrease(exercise.exercise_duration, "medium")
            
            # 운동 효과 점수 계산
            exercise_score = calculate_exercise_score(glucose_change, expected_decrease)
            
            # 혈당 상태 분류
            before_status = classify_glucose_status(before_glucose.glucose_mg_dl)
            after_status = classify_glucose_status(after_glucose.glucose_mg_dl)
            
            result = {
                "exercise_type": exercise.exercise_name,
                "duration_minutes": exercise.exercise_duration,
                "glucose_before": before_glucose.glucose_mg_dl,
                "glucose_after": after_glucose.glucose_mg_dl,
                "glucose_change": round(glucose_change, 1),
                "expected_decrease": expected_decrease,
                "exercise_score": exercise_score,
                "before_status": before_status,
                "after_status": after_status,
                "time_before": before_glucose.time,
                "time_after": after_glucose.time,
                "impact_summary": generate_exercise_impact_summary(exercise.exercise_name, glucose_change, exercise_score, after_status)
            }
            
            results.append(result)
    
    return results


def calculate_expected_glucose_decrease(duration_minutes: int, intensity: str) -> float:
    """운동 강도와 시간에 따른 예상 혈당 감소량 계산"""
    if duration_minutes is None or intensity is None:
        return 0
    
    # 강도별 분당 혈당 감소량 (mg/dL)
    intensity_multipliers = {
        "low": 0.5,
        "medium": 1.0,
        "high": 1.5
    }
    
    multiplier = intensity_multipliers.get(intensity.lower(), 0.5)
    return duration_minutes * multiplier


def calculate_exercise_score(actual_change: float, expected_decrease: float) -> int:
    """운동 효과 점수 계산 (0-100)"""
    if expected_decrease == 0:
        return 50  # 기본 점수
    
    # 실제 변화량이 예상 감소량에 얼마나 가까운지 계산
    if actual_change <= 0:  # 혈당이 감소했거나 변화 없음
        if abs(actual_change) >= expected_decrease * 0.8:  # 예상의 80% 이상 감소
            return 100
        elif abs(actual_change) >= expected_decrease * 0.5:  # 예상의 50% 이상 감소
            return 80
        else:
            return 60
    else:  # 혈당이 증가
        if actual_change <= expected_decrease * 0.3:  # 증가폭이 예상 감소량의 30% 이하
            return 70
        else:
            return 40


def generate_food_impact_summary(food_name: str, glucose_change: float, gl_index: float, score: int, after_status: str) -> str:
    """음식 영향 요약 메시지 생성"""
    if glucose_change > 0:
        if score >= 80:
            return f"{food_name} → ΔBG +{glucose_change:.0f} (GL {gl_index:.0f}, 점수 {score}) → {after_status}"
        elif score >= 60:
            return f"{food_name} → ΔBG +{glucose_change:.0f} (GL {gl_index:.0f}, 점수 {score}) → {after_status} 1회"
        else:
            return f"{food_name} → ΔBG +{glucose_change:.0f} (GL {gl_index:.0f}, 점수 {score}) → {after_status} 1회"
    else:
        return f"{food_name} → ΔBG {glucose_change:.0f} (GL {gl_index:.0f}, 점수 {score}) → 혈당 안정"


def generate_exercise_impact_summary(exercise_type: str, glucose_change: float, score: int, after_status: str) -> str:
    """운동 영향 요약 메시지 생성"""
    if glucose_change < 0:
        if score >= 80:
            return f"{exercise_type} → 혈당 {abs(glucose_change):.0f}mg/dL 감소 → {after_status} 복귀"
        else:
            return f"{exercise_type} → 혈당 {abs(glucose_change):.0f}mg/dL 감소 → {after_status}"
    else:
        return f"{exercise_type} → 혈당 변화 {glucose_change:.0f}mg/dL → {after_status}"


def generate_daily_glucose_analysis(member_id: int, date: str, food_data: List[Any], exercise_data: List[Any], glucose_data: List[Any]) -> Dict[str, Any]:
    """일일 혈당 변화 종합 분석"""
    # 음식 영향 분석
    food_impacts = analyze_food_glucose_impact(food_data, glucose_data)
    
    # 운동 영향 분석
    exercise_impacts = analyze_exercise_glucose_impact(exercise_data, glucose_data)
    
    # 전체 통계 계산
    total_hyperglycemia = sum(impact['hyperglycemia_count'] for impact in food_impacts)
    total_hypoglycemia = sum(impact['hypoglycemia_count'] for impact in food_impacts)
    
    # 평균 점수 계산
    avg_food_score = sum(impact['glucose_score'] for impact in food_impacts) / len(food_impacts) if food_impacts else 0
    avg_exercise_score = sum(impact['exercise_score'] for impact in exercise_impacts) / len(exercise_impacts) if exercise_impacts else 0
    
    return {
        "date": date,
        "member_id": member_id,
        "food_impacts": food_impacts,
        "exercise_impacts": exercise_impacts,
        "summary": {
            "total_hyperglycemia": total_hyperglycemia,
            "total_hypoglycemia": total_hypoglycemia,
            "avg_food_score": round(avg_food_score, 1),
            "avg_exercise_score": round(avg_exercise_score, 1),
            "total_food_items": len(food_impacts),
            "total_exercises": len(exercise_impacts)
        }
    }
