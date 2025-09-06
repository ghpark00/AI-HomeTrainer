import cv2
import mediapipe as mp
import numpy as np
import time
import pygame
from PIL import ImageFont, ImageDraw, Image

# --- 상수 및 초기 설정 ---
FONT_PATH = 'font/NotoSansKR-VariableFont_wght.ttf'
ANGLE_THRESHOLD_UP = 170.0  # 일어선 자세의 무릎 각도 기준
ANGLE_THRESHOLD_DOWN = 100.0 # 앉은 자세의 무릎 각도 기준
SET_GOAL = 3  # 세트당 목표 횟수
REST_DURATION = 30  # 휴식 시간 (초)

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
    if angle > 180.0:
        angle = 360 - angle
    return angle

def play_sound(sound_file):
    """pygame을 사용하여 사운드 파일을 재생합니다."""
    try:
        pygame.mixer.Sound(sound_file).play()
    except Exception as e:
        print(f"사운드 재생 오류 ({sound_file}): {e}")

def draw_text(img, text, pos, font_path, font_size, color):
    """Pillow 라이브러리를 사용해 한글 등 다양한 폰트를 이미지에 그립니다."""
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    font = ImageFont.truetype(font_path, font_size)
    draw.text(pos, text, font=font, fill=color)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

# --- 핵심 로직 함수 (리팩토링) ---

def process_pose_landmarks(image, pose_model):
    """이미지를 처리하여 포즈 랜드마크를 찾고 각도를 계산합니다."""
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose_model.process(image_rgb)
    
    landmarks_data = {
        "results": results,
        "knee_angle": None,
        "hip_angle": None,
        "bar_percentage": 0.0,
    }

    try:
        landmarks = results.pose_landmarks.landmark
        
        # 필요한 랜드마크가 잘 보이는지 확인
        required_landmarks = [mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.LEFT_KNEE, 
                                mp_pose.PoseLandmark.LEFT_ANKLE, mp_pose.PoseLandmark.LEFT_SHOULDER]
        if all(landmarks[lm.value].visibility > 0.7 for lm in required_landmarks):
            hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            
            knee_angle = calculate_angle(hip, knee, ankle)
            hip_angle = calculate_angle(shoulder, hip, knee)
            
            landmarks_data["knee_angle"] = knee_angle
            landmarks_data["hip_angle"] = hip_angle
            
            # 진행률 바(bar) 퍼센티지 계산
            landmarks_data["bar_percentage"] = np.interp(knee_angle, [ANGLE_THRESHOLD_DOWN, ANGLE_THRESHOLD_UP], [100.0, 0.0])

    except Exception:
        pass # 랜드마크를 찾지 못하면 조용히 넘어감

    return landmarks_data

def update_state_and_counters(state, landmarks_data):
    """포즈 데이터를 기반으로 운동 상태, 카운터, 피드백을 업데이트합니다."""
    knee_angle = landmarks_data["knee_angle"]
    hip_angle = landmarks_data["hip_angle"]
    
    # 각도가 감지되지 않으면 아무것도 하지 않음
    if knee_angle is None or hip_angle is None:
        return state

    # --- 1. 자세 피드백 제공 ---
    if state["feedback"] == "": # 현재 동작에서 피드백이 아직 없을 때만
        if knee_angle < 60:
            state["feedback"] = "TOO DEEP"
            state["mistake_made_this_rep"] = True
            state["feedback_start_time"] = time.time()
            play_sound('sound/무릎이너무깊어요.wav')
        elif state["stage"] == 'down' and hip_angle < ANGLE_THRESHOLD_DOWN:
            state["feedback"] = "STRAIGHTEN BACK"
            state["mistake_made_this_rep"] = True
            state["feedback_start_time"] = time.time()
            play_sound('sound/등을곧게펴세요.wav')

    # --- 2. 운동 단계(stage) 변경 및 횟수 카운트 ---
    if knee_angle < ANGLE_THRESHOLD_DOWN and state["stage"] == 'up':
        state["stage"] = 'down'
        state["mistake_made_this_rep"] = False
        state["feedback"] = "" # 새로운 동작 시작 시 피드백 초기화

    if knee_angle > ANGLE_THRESHOLD_UP and state["stage"] == 'down':
        state["stage"] = 'up'
        state["counter"] += 1
        
        if state["mistake_made_this_rep"]:
            state["bad_counter"] += 1
            play_sound('sound/063_삐삑 (오답 -짧은).mp3')
        else:
            state["good_counter"] += 1
            # 세트 완료 여부를 먼저 확인
            if state["good_counter"] == SET_GOAL:
                state["workout_state"] = 'rest'
                state["rest_start_time"] = time.time()
                play_sound('sound/0289-예_.wav')
            else: # 세트가 끝나지 않았으면 긍정 피드백 제공
                state["feedback"] = "GOOD"
                state["feedback_start_time"] = time.time()
                play_sound('sound/correct-choice-43861.mp3')
    
    return state

def draw_ui(image, state, landmarks_data):
    """화면에 전체 사용자 인터페이스(UI)를 그립니다."""
    # 포즈 랜드마크 그리기
    if landmarks_data["results"].pose_landmarks:
        mp_drawing.draw_landmarks(image, landmarks_data["results"].pose_landmarks, mp_pose.POSE_CONNECTIONS)
    
    # --- 정보창 ---
    overlay = image.copy()
    cv2.rectangle(overlay, (0, 0), (200, 145), (0, 0, 0), -1)
    alpha = 0.6
    image = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)

    image = draw_text(image, f'SET {state["set_counter"]}', (10, 10), FONT_PATH, 18, (255, 255, 255))
    image = draw_text(image, 'TOTAL REPS', (10, 35), FONT_PATH, 16, (200, 200, 200))
    image = draw_text(image, str(state["counter"]), (130, 35), FONT_PATH, 18, (255, 255, 255))
    image = draw_text(image, 'GOOD', (10, 65), FONT_PATH, 16, (0, 255, 0))
    image = draw_text(image, str(state["good_counter"]), (70, 65), FONT_PATH, 18, (255, 255, 255))
    image = draw_text(image, 'BAD', (120, 65), FONT_PATH, 16, (255, 0, 0)) # 빨간색은 (0,0,255)
    image = draw_text(image, str(state["bad_counter"]), (170, 65), FONT_PATH, 18, (255, 255, 255))
    image = draw_text(image, 'STAGE', (10, 95), FONT_PATH, 16, (200, 200, 200))
    image = draw_text(image, state["stage"].upper(), (90, 95), FONT_PATH, 18, (255, 255, 255))
    
    # 피드백 텍스트 그리기
    feedback_color = (0, 255, 0) if state["feedback"] == "GOOD" else (255, 0, 0)
    image = draw_text(image, state["feedback"], (10, 120), FONT_PATH, 18, feedback_color)

    # --- 진행률 바 ---
    bar_x, bar_y, bar_w, bar_h = 220, 10, 25, 125
    # 바의 움직임을 부드럽게 처리
    state["smoothed_bar"] = (0.8 * state["smoothed_bar"]) + (0.2 * landmarks_data["bar_percentage"])
    
    cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (200, 200, 200), 2)
    fill_h = int(bar_h * state["smoothed_bar"] / 100.0)
    cv2.rectangle(image, (bar_x, bar_y + bar_h - fill_h), (bar_x + bar_w, bar_y + bar_h), (255, 255, 255), -1)

    return image

def draw_rest_screen(image, rest_time_left):
    """휴식 화면 오버레이를 그립니다."""
    h, w, _ = image.shape
    overlay = image.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    image = cv2.addWeighted(overlay, 0.7, image, 0.3, 0)

    text1 = "SET COMPLETE!"
    text2 = f"REST: {rest_time_left}s"
    
    font_large = ImageFont.truetype(FONT_PATH, 50)
    font_medium = ImageFont.truetype(FONT_PATH, 30)
    
    text1_bbox = font_large.getbbox(text1)
    text2_bbox = font_medium.getbbox(text2)
    
    text1_width = text1_bbox[2] - text1_bbox[0]
    text1_height = text1_bbox[3] - text1_bbox[1]
    text2_width = text2_bbox[2] - text2_bbox[0]

    x1 = int((w - text1_width) / 2)
    y1 = int((h / 2) - text1_height)
    x2 = int((w - text2_width) / 2)
    y2 = int((h / 2) + 20)
    
    image = draw_text(image, text1, (x1, y1), FONT_PATH, 50, (0, 255, 0))
    image = draw_text(image, text2, (x2, y2), FONT_PATH, 30, (255, 255, 255))
    return image


# --- 메인 프로그램 실행 ---
def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("카메라를 열 수 없습니다.")
        return

    # 프로그램의 모든 상태 변수를 담는 딕셔너리
    app_state = {
        "counter": 0,
        "good_counter": 0,
        "bad_counter": 0,
        "stage": 'up',
        "feedback": "",
        "feedback_start_time": 0,
        "mistake_made_this_rep": False,
        "smoothed_bar": 0.0,
        "workout_state": 'workout',
        "rest_start_time": 0,
        "set_counter": 1
    }

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break

        # 현재 상태가 '휴식'일 때의 로직
        if app_state["workout_state"] == 'rest':
            elapsed_rest = time.time() - app_state["rest_start_time"]
            remaining_rest = int(REST_DURATION - elapsed_rest)

            if remaining_rest > 0:
                image = draw_rest_screen(image, remaining_rest)
            else: # 휴식 시간이 끝나면 다음 세트를 위해 상태 초기화
                app_state["workout_state"] = 'workout'
                app_state["counter"] = 0
                app_state["good_counter"] = 0
                app_state["bad_counter"] = 0
                app_state["set_counter"] += 1
                app_state["stage"] = 'up'
                app_state["feedback"] = ""
        
        # 현재 상태가 '운동'일 때의 로직
        elif app_state["workout_state"] == 'workout':
            # 1. 이미지 처리하여 포즈 데이터 얻기
            landmarks_data = process_pose_landmarks(image, pose)

            # 2. 포즈 데이터로 상태 업데이트
            app_state = update_state_and_counters(app_state, landmarks_data)
            
            # 3. 일정 시간 후 피드백 메시지 지우기
            if app_state["feedback"] and (time.time() - app_state["feedback_start_time"] > 2):
                app_state["feedback"] = ""

            # 4. UI 그리기
            image = draw_ui(image, app_state, landmarks_data)
        
        # 최종 결과 화면에 표시
        cv2.imshow('AI Home Trainer', cv2.resize(image, (1280, 720)))

        # 'ESC' 키를 누르면 종료
        if cv2.waitKey(5) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()