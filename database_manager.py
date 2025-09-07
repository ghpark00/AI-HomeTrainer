# database_manager.py
import sqlite3
import json
from datetime import datetime

DB_NAME = 'workout_records.db'

def init_db():
    """데이터베이스를 초기화하고 'records' 테이블을 생성합니다."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            target_reps INTEGER NOT NULL,
            total_sets INTEGER NOT NULL,
            rest_time INTEGER NOT NULL,
            set_details TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_workout_record(exercise_type, target_reps, total_sets, rest_time, set_details_list):
    """새로운 운동 기록을 데이터베이스에 추가합니다."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    set_details_json = json.dumps(set_details_list)
    
    cursor.execute('''
        INSERT INTO records (exercise_type, timestamp, target_reps, total_sets, rest_time, set_details)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (exercise_type, timestamp, target_reps, total_sets, rest_time, set_details_json))
    
    conn.commit()
    conn.close()
    print(f"기록 저장 완료: {exercise_type} at {timestamp}")

def get_records_by_exercise(exercise_type):
    """특정 운동에 대한 모든 기록을 최신순으로 가져옵니다."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT timestamp, exercise_type, target_reps, total_sets, rest_time, set_details FROM records WHERE exercise_type = ? ORDER BY timestamp DESC",
        (exercise_type,)
    )
    records = cursor.fetchall()
    conn.close()
    return records