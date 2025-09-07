# squat_ai_trainer.py
import cv2
import mediapipe as mp
import numpy as np
import time
import pygame
import sys
from PIL import ImageFont, ImageDraw, Image
from database_manager import add_workout_record  # 데이터베이스 매니저 import

# --- 상수 및 초기 설정 ---
FONT_PATH = 'font/NotoSansKR-VariableFont_wght.ttf'
ANGLE_THRESHOLD_UP = 170.0
ANGLE_THRESHOLD_DOWN = 100.0
FINISH_DURATION = 10

# 기본값 설정
SET_GOAL = 5
TOTAL_SETS_GOAL = 3
REST_DURATION = 30

# 커맨드 라인 인자로부터 값 가져오기
if len(sys.argv) == 4:
    try:
        SET_GOAL = int(sys.argv[1])
        TOTAL_SETS_GOAL = int(sys.argv[2])
        REST_DURATION = int(sys.argv[3])
        print(f"사용자 설정 적용: 횟수={SET_GOAL}, 세트={TOTAL_SETS_GOAL}, 휴식={REST_DURATION}초")
    except (ValueError, IndexError):
        print("잘못된 인자 값입니다. 기본값으로 실행합니다.")

# MediaPipe Pose 모델 초기화
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

# 사운드 출력을 위한 Pygame mixer 초기화
pygame.mixer.init()

# --- 유틸리티 함수 ---

def calculate_angle(a, b, c):
    """세 점 사이의 각도를 계산합니다."""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0: angle = 360 - angle
    return angle

def play_sound(sound_file):
    """pygame을 사용하여 사운드 파일을 재생합니다."""
    try:
        pygame.mixer.Sound(sound_file).play()
    except Exception as e:
        print(f"사운드 재생 오류 ({sound_file}): {e}")

def draw_text(img, text, pos, font_path, font_size, color):
    """Pillow 라이브러리를 사용해 한글 등 다양한 폰트를 이미지에 그립니다."""
    try:
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        font = ImageFont.truetype(font_path, font_size)
        draw.text(pos, text, font=font, fill=color)
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    except IOError:
        print(f"폰트 파일({font_path})을 찾을 수 없습니다. 기본 폰트로 대체합니다.")
        cv2.putText(img, text, (int(pos[0]), int(pos[1] + font_size)), cv2.FONT_HERSHEY_SIMPLEX, font_size / 25, color, 2)
        return img

# --- 핵심 로직 함수 (리팩토링) ---

def process_pose_landmarks(image, pose_model):
    """이미지를 처리하여 포즈 랜드마크를 찾고 각도를 계산합니다."""
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose_model.process(image_rgb)
    
    landmarks_data = {"results": results, "knee_angle": None, "hip_angle": None, "bar_percentage": 0.0}

    try:
        landmarks = results.pose_landmarks.landmark
        required_landmarks = [mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.LEFT_KNEE, mp_pose.PoseLandmark.LEFT_ANKLE, mp_pose.PoseLandmark.LEFT_SHOULDER]
        if all(landmarks[lm.value].visibility > 0.7 for lm in required_landmarks):
            hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            
            knee_angle = calculate_angle(hip, knee, ankle)
            hip_angle = calculate_angle(shoulder, hip, knee)
            
            landmarks_data["knee_angle"] = knee_angle
            landmarks_data["hip_angle"] = hip_angle
            landmarks_data["bar_percentage"] = np.interp(knee_angle, [ANGLE_THRESHOLD_DOWN, ANGLE_THRESHOLD_UP], [100.0, 0.0])
    except Exception:
        pass
    return landmarks_data

def update_state_and_counters(state, landmarks_data):
    """포즈 데이터를 기반으로 운동 상태, 카운터, 피드백을 업데이트합니다."""
    knee_angle, hip_angle = landmarks_data["knee_angle"], landmarks_data["hip_angle"]
    if knee_angle is None or hip_angle is None: return state

    if state["feedback"] == "":
        if knee_angle < 60:
            state.update({"feedback": "TOO DEEP", "mistake_made_this_rep": True, "feedback_start_time": time.time()})
            play_sound('sound/무릎이너무깊어요.wav')
        elif state["stage"] == 'down' and hip_angle < ANGLE_THRESHOLD_DOWN:
            state.update({"feedback": "STRAIGHTEN BACK", "mistake_made_this_rep": True, "feedback_start_time": time.time()})
            play_sound('sound/등을곧게펴세요.wav')

    if knee_angle < ANGLE_THRESHOLD_DOWN and state["stage"] == 'up':
        state.update({"stage": 'down', "mistake_made_this_rep": False, "feedback": ""})

    if knee_angle > ANGLE_THRESHOLD_UP and state["stage"] == 'down':
        state["stage"] = 'up'
        state["counter"] += 1
        
        if state["mistake_made_this_rep"]:
            state["bad_counter"] += 1
            play_sound('sound/063_삐삑 (오답 -짧은).mp3')
        else:
            state["good_counter"] += 1
            if state["good_counter"] == SET_GOAL:
                # 세트 완료 시 결과 기록
                state["set_results"].append({"good": state["good_counter"], "bad": state["bad_counter"]})
                
                if state["set_counter"] == TOTAL_SETS_GOAL:
                    state.update({"workout_state": 'finished', "finish_start_time": time.time()})
                    play_sound('sound/0290-와우~~.mp3')
                else:
                    state.update({"workout_state": 'rest', "rest_start_time": time.time()})
                    play_sound('sound/0289-예_.wav')
            else:
                state.update({"feedback": "GOOD", "feedback_start_time": time.time()})
                play_sound('sound/correct-choice-43861.mp3')
    return state

def draw_ui(image, state, landmarks_data):
    """화면에 전체 사용자 인터페이스(UI)를 그립니다."""
    if landmarks_data["results"].pose_landmarks:
        mp_drawing.draw_landmarks(image, landmarks_data["results"].pose_landmarks, mp_pose.POSE_CONNECTIONS)
    
    overlay = image.copy()
    cv2.rectangle(overlay, (0, 0), (200, 145), (0, 0, 0), -1)
    image = cv2.addWeighted(overlay, 0.6, image, 0.4, 0)

    image = draw_text(image, f'SET {state["set_counter"]}', (10, 10), FONT_PATH, 18, (255, 255, 255))
    image = draw_text(image, 'TOTAL REPS', (10, 35), FONT_PATH, 16, (200, 200, 200))
    image = draw_text(image, str(state["counter"]), (130, 35), FONT_PATH, 18, (255, 255, 255))
    image = draw_text(image, 'GOOD', (10, 65), FONT_PATH, 16, (0, 255, 0))
    image = draw_text(image, str(state["good_counter"]), (70, 65), FONT_PATH, 18, (255, 255, 255))
    image = draw_text(image, 'BAD', (120, 65), FONT_PATH, 16, (255, 0, 0))
    image = draw_text(image, str(state["bad_counter"]), (170, 65), FONT_PATH, 18, (255, 255, 255))
    image = draw_text(image, 'STAGE', (10, 95), FONT_PATH, 16, (200, 200, 200))
    image = draw_text(image, state["stage"].upper(), (90, 95), FONT_PATH, 18, (255, 255, 255))
    
    feedback_color = (0, 255, 0) if state["feedback"] == "GOOD" else (255, 0, 0)
    image = draw_text(image, state["feedback"], (10, 120), FONT_PATH, 18, feedback_color)

    bar_x, bar_y, bar_w, bar_h = 220, 10, 25, 125
    state["smoothed_bar"] = (0.8 * state["smoothed_bar"]) + (0.2 * landmarks_data["bar_percentage"])
    cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (200, 200, 200), 2)
    fill_h = int(bar_h * state["smoothed_bar"] / 100.0)
    cv2.rectangle(image, (bar_x, bar_y + bar_h - fill_h), (bar_x + bar_w, bar_y + bar_h), (255, 255, 255), -1)
    return image

def draw_overlay_screen(image, text1, text2, text1_size, text2_size, text1_color):
    """휴식 또는 종료 화면 오버레이를 그리는 범용 함수입니다."""
    h, w, _ = image.shape
    overlay = image.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    image = cv2.addWeighted(overlay, 0.7, image, 0.3, 0)
    
    try:
        font_large, font_medium = ImageFont.truetype(FONT_PATH, text1_size), ImageFont.truetype(FONT_PATH, text2_size)
        text1_bbox, text2_bbox = font_large.getbbox(text1), font_medium.getbbox(text2)
        text1_width, text1_height = text1_bbox[2] - text1_bbox[0], text1_bbox[3] - text1_bbox[1]
        text2_width = text2_bbox[2] - text2_bbox[0]
    except IOError:
        (text1_width, text1_height), _ = cv2.getTextSize(text1, cv2.FONT_HERSHEY_SIMPLEX, text1_size / 25, 2)
        (text2_width, _), _ = cv2.getTextSize(text2, cv2.FONT_HERSHEY_SIMPLEX, text2_size / 25, 2)

    x1, y1 = int((w - text1_width) / 2), int((h / 2) - text1_height)
    x2, y2 = int((w - text2_width) / 2), int((h / 2) + 40)
    
    image = draw_text(image, text1, (x1, y1), FONT_PATH, text1_size, text1_color)
    image = draw_text(image, text2, (x2, y2), FONT_PATH, text2_size, (255, 255, 255))
    return image

# --- 메인 프로그램 실행 ---
def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("카메라를 열 수 없습니다.")
        return

    # 프로그램 상태 변수
    app_state = {
        "counter": 0, "good_counter": 0, "bad_counter": 0,
        "stage": 'up', "feedback": "", "feedback_start_time": 0,
        "mistake_made_this_rep": False, "smoothed_bar": 0.0,
        "workout_state": 'workout', "rest_start_time": 0,
        "set_counter": 1, "finish_start_time": 0,
        "set_results": [],  # 세트별 결과를 저장할 리스트
        "workout_completed": False # 운동 완료 여부 플래그
    }

    while cap.isOpened():
        success, image = cap.read()
        if not success: break
        
        if app_state["workout_state"] == 'rest':
            elapsed_rest = time.time() - app_state["rest_start_time"]
            remaining_rest = int(REST_DURATION - elapsed_rest)
            if remaining_rest > 0:
                image = draw_overlay_screen(image, "SET COMPLETE!", f"REST: {remaining_rest}s", 50, 30, (0, 255, 0))
            else:
                app_state.update({"workout_state": 'workout', "counter": 0, "good_counter": 0, "bad_counter": 0, "set_counter": app_state["set_counter"] + 1, "stage": 'up', "feedback": ""})
        
        elif app_state["workout_state"] == 'finished':
            elapsed_finish = time.time() - app_state["finish_start_time"]
            remaining_finish = int(FINISH_DURATION - elapsed_finish)
            if remaining_finish > 0:
                image = draw_overlay_screen(image, "ALL SETS COMPLETE!!", f"종료까지: {remaining_finish}s", 50, 30, (0, 255, 255))
            else:
                app_state["workout_completed"] = True  # 완료 플래그 설정
                break
        
        elif app_state["workout_state"] == 'workout':
            landmarks_data = process_pose_landmarks(image, pose)
            app_state = update_state_and_counters(app_state, landmarks_data)
            if app_state["feedback"] and (time.time() - app_state["feedback_start_time"] > 2):
                app_state["feedback"] = ""
            image = draw_ui(image, app_state, landmarks_data)
        
        cv2.imshow('AI Home Trainer', cv2.resize(image, (1280, 720)))
        if cv2.waitKey(5) & 0xFF == 27: break

    # 모든 세트를 정상적으로 완료했을 때만 기록 저장
    if app_state["workout_completed"]:
        print("운동 완료! 기록을 저장합니다...")
        add_workout_record(
            exercise_type='스쿼트',
            target_reps=SET_GOAL,
            total_sets=TOTAL_SETS_GOAL,
            rest_time=REST_DURATION,
            set_details_list=app_state["set_results"]
        )

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()