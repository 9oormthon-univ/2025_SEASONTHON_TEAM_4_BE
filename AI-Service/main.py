from flask import Flask, request, jsonify
from app.utils.io import load_text
from app.services.glucose import calculate_glucose_metrics, analyze_glucose
from app.services.food import calculate_food_metrics, analyze_food
from app.services.habit import calculate_habit_metrics, analyze_habits
from app.db import SessionLocal
from app.models.logs import GlucoseLog, FoodLog
from datetime import datetime

app = Flask(__name__)

@app.route("/quest/glucose", methods=["GET"])
def analyze():
    try:
        # Get today's date in YYYY-MM-DD format
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Read today's glucose readings from DB
        db = SessionLocal()
        try:
            readings = (
                db.query(GlucoseLog)
                .filter(GlucoseLog.date == today)
                .order_by(GlucoseLog.time.asc())
                .all()
            )
        finally:
            db.close()
        
        cgm_readings = []
        for r in readings:
            iso_time = f"{r.date}T{r.time}" if r.time else f"{r.date}T00:00:00"
            cgm_readings.append({
                "time": iso_time,
                "glucose_mg_dl": r.glucose_mg_dl,
            })
        blood_sugar_data = {"cgm_data": {"readings": cgm_readings}}
        
        # Calculate glucose metrics
        glucose_metrics = calculate_glucose_metrics(blood_sugar_data)
        
        # Load prompt and analyze
        prompt = load_text("prompts/daily_quest.txt")
        analysis_result = analyze_glucose(glucose_metrics, prompt)
        
        return jsonify(analysis_result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/quest/food", methods=["GET"])
def food_analyze():
    try:
        # Get today's date in YYYY-MM-DD format
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Read today's food logs from DB
        db = SessionLocal()
        try:
            foods = (
                db.query(FoodLog)
                .filter(FoodLog.date == today)
                .order_by(FoodLog.time.asc())
                .all()
            )
        finally:
            db.close()
        
        # Group by meal type for today
        food_list = []
        for f in foods:
            # Represent each DB row as a single-meal entry containing one item
            food_list.append({
                "meal": f.type,  # 아침/점심/저녁/간식/야식
                "time": f.time or "",
                "items": [
                    {
                        "name": f.name,
                        "calories": f.calories or 0,
                        "carbs": f.carbs or 0,
                    }
                ],
            })
        
        # Build expected structure for today only
        food_log_data = {"records": [{"date": today, "food": food_list}]}
        
        # Calculate food metrics
        food_metrics = calculate_food_metrics(food_log_data)
        
        # Load prompt and analyze
        prompt = load_text("prompts/food_quest.txt")
        analysis_result = analyze_food(food_metrics, prompt)
        
        return jsonify(analysis_result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/analyze", methods=["GET"])
def habit_analyze():
    """생활 습관 종합 분석 및 코칭"""
    try:
        # Query parameters
        user_id = request.args.get("user_id", "demo_user")
        days = int(request.args.get("days", 7))  # 기본 7일간 분석
        
        # 생활 습관 지표 계산
        habit_metrics = calculate_habit_metrics(user_id, days)
        
        # 생활 습관 분석 및 코칭
        analysis_result = analyze_habits(habit_metrics)
        
        return jsonify(analysis_result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Initialize database tables
    try:
        from app.db import init_db
        init_db()
    except Exception as e:
        print("DB init failed:", e)
    app.run(port=5000, debug=True)
