import cv2
import mediapipe as mp
import numpy as np
import time
import threading
import pygame
from playsound import playsound
from PIL import ImageFont, ImageDraw, Image

# 사용할 폰트 파일 경로
# (Gmarket Sans를 다운받아 코드와 같은 폴더에 넣었다고 가정)
FONT_PATH = 'NotoSansKR-VariableFont_wght.ttf'

# 각도 계산 함수
def calculate_angle(a, b, c):
    # a, b, c는 랜드마크 좌표 (x, y). b가 각도의 꼭짓점.
    # 예: a=어깨, b=팔꿈치, c=손목 -> 팔꿈치 각도 계산
    a = np.array(a) # 첫 번째 점
    b = np.array(b) # 중간 점 (꼭짓점)
    c = np.array(c) # 세 번째 점

    # 벡터 계산 (b->a, b->c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - \
            np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle 
        
    return angle

def draw_rounded_rectangle(img, rect, radius, color, thickness):
    x, y, w, h = rect
    r = radius

    # 모서리 원 그리기
    cv2.circle(img, (x + r, y + r), r, color, thickness)
    cv2.circle(img, (x + w - r, y + r), r, color, thickness)
    cv2.circle(img, (x + r, y + h - r), r, color, thickness)
    cv2.circle(img, (x + w - r, y + h - r), r, color, thickness)

    # 사각형 채우기
    cv2.rectangle(img, (x + r, y), (x + w - r, y + h), color, thickness)
    cv2.rectangle(img, (x, y + r), (x + w, y + h - r), color, thickness)
    
def draw_text(img, text, pos, font_path, font_size, color):
    # OpenCV 이미지를 Pillow 이미지로 변환
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    # 폰트 설정
    font = ImageFont.truetype(font_path, font_size)
    
    # 텍스트 그리기
    draw.text(pos, text, font=font, fill=color)
    
    # Pillow 이미지를 다시 OpenCV 이미지로 변환
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

pygame.mixer.init()

def play_sound(sound_file):
    pygame.mixer.Sound(sound_file).play()


# MediaPipe Pose 모델 및 그리기 유틸리티 초기화
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

# 웹캠 열기
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("카메라를 열 수 없습니다.")
    exit()

# 카운터 및 피드백 변수 초기화
counter = 0 
good_counter = 0
bad_counter = 0
stage = 'up'
feedback = ""
feedback_start_time = 0
mistake_made_this_rep = False
smoothed_bar = 0.0
ANGLE_THRESHOLD_UP = 170.0 # UP 상태 기준 (사용자 맞춤)
ANGLE_THRESHOLD_DOWN = 100.0 # DOWN 상태 기준

# 세트 및 휴식 타이머 설정
SET_GOAL = 3 # 한 세트당 목표 횟수 (테스트 시 3~5회로 줄여서 하세요)
REST_DURATION = 30 # 휴식 시간 (초)
workout_state = 'workout' # 현재 상태: 'workout' 또는 'rest'
rest_start_time = 0
set_counter = 1 # 현재 세트 번호

# --- ✅ [while 루프 전체 교체] ---

# 비디오 스트림을 처리하기 위한 메인 루프
while cap.isOpened():
    success, image = cap.read()
    if not success:
        break

    # --- 1. 상태에 따른 로직 분기 ---
    if workout_state == 'rest':
        # --- 휴식 상태 로직 ---
        elapsed_rest_time = time.time() - rest_start_time
        remaining_rest_time = int(REST_DURATION - elapsed_rest_time)

        if remaining_rest_time > 0:
            # 휴식 중 UI 표시 (화면 중앙에 큰 메시지)
            image_height, image_width, _ = image.shape
            
            # 반투명 검은색 배경 추가
            overlay = image.copy()
            cv2.rectangle(overlay, (0, 0), (image_width, image_height), (0,0,0), -1)
            image = cv2.addWeighted(overlay, 0.7, image, 0.3, 0)
            
            text1 = "SET COMPLETE!"
            text2 = f"REST: {remaining_rest_time}s"
            
            # Pillow를 사용해 텍스트 크기 계산 (정확한 중앙 정렬을 위해)
            font_large = ImageFont.truetype(FONT_PATH, 50)
            font_medium = ImageFont.truetype(FONT_PATH, 30)
            
            text1_bbox = font_large.getbbox(text1)
            text2_bbox = font_medium.getbbox(text2)
            
            text1_width = text1_bbox[2] - text1_bbox[0]
            text1_height = text1_bbox[3] - text1_bbox[1]
            text2_width = text2_bbox[2] - text2_bbox[0]

            x1 = int((image_width - text1_width) / 2)
            y1 = int((image_height / 2) - text1_height)
            x2 = int((image_width - text2_width) / 2)
            y2 = int((image_height / 2) + 20)
            
            image = draw_text(image, text1, (x1, y1), FONT_PATH, 50, (0, 255, 0))
            image = draw_text(image, text2, (x2, y2), FONT_PATH, 30, (255, 255, 255))
            
        else:
            # 휴식 종료 -> 운동 상태로 전환 및 변수 초기화
            workout_state = 'workout'
            counter = 0
            good_counter = 0
            bad_counter = 0
            set_counter += 1
            feedback = ""
            stage = 'up'

    elif workout_state == 'workout':
        # --- 운동 상태 로직 ---
        # 피드백 타이머 로직
        if feedback != "" and time.time() - feedback_start_time > 2:
            feedback = ""

        # 포즈 처리 로직 (기존과 동일)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)
        
        # --- 👇 [1. 진행률 바 변수 초기화] ---
        bar_percentage = 0 # 기본값 0으로 설정
        
        try:
            landmarks = results.pose_landmarks.landmark
            # (랜드마크 신뢰도 체크 및 좌표/각도 계산 로직은 기존과 동일)
            hip_visibility = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].visibility
            knee_visibility = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].visibility
            ankle_visibility = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].visibility
            shoulder_visibility = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].visibility
        
            if hip_visibility > 0.7 and knee_visibility > 0.7 and ankle_visibility > 0.7 and shoulder_visibility > 0.7:
                hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
                shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                knee_angle = calculate_angle(hip, knee, ankle)
                hip_angle = calculate_angle(shoulder, hip, knee)
                
                # --- 👇 [2. 진행률(%) 계산] ---
                if knee_angle >= ANGLE_THRESHOLD_UP:
                    bar_percentage = 0.0
                elif knee_angle <= ANGLE_THRESHOLD_DOWN:
                    bar_percentage = 100.0
                else:
                    # xp는 오름차순이어야 함!
                    bar_percentage = float(np.interp(
                        knee_angle,
                        [ANGLE_THRESHOLD_DOWN, ANGLE_THRESHOLD_UP],  # 100 → 170 (오름차순)
                        [100.0, 0.0]                                 # 100°일 때 100%, 170°일 때 0%
                    ))
                
                alpha = 0.2
                smoothed_bar = (1 - alpha) * smoothed_bar + alpha * bar_percentage
                
                # --- 1. 자세 피드백 ---
                if feedback == "":  # 현재 stage에서 아직 피드백이 안 나갔을 때만
                    if knee_angle < 60:
                        feedback = "TOO DEEP"
                        mistake_made_this_rep = True
                        feedback_start_time = time.time()
                        play_sound(r'C:\GITHUB\AI-HomeTrainer\sound\무릎이너무깊어요.wav')

                    elif stage == 'down' and hip_angle < ANGLE_THRESHOLD_DOWN:
                        feedback = "STRAIGHTEN BACK"
                        mistake_made_this_rep = True
                        feedback_start_time = time.time()
                        play_sound(r'C:\GITHUB\AI-HomeTrainer\sound\등을곧게펴세요.wav')
                
                    
                # --- 2. 카운트 및 세트 로직 ---
                # 카운트를 위한 단계(stage) 변경 감지
                if knee_angle < ANGLE_THRESHOLD_DOWN and stage == 'up':
                    stage = 'down'
                    mistake_made_this_rep = False
                    feedback = "" # 새로운 동작 시작 시 피드백 초기화 (중요!)

                if knee_angle > ANGLE_THRESHOLD_UP and stage == 'down':
                    stage = 'up'
                    counter += 1
                    
                    if mistake_made_this_rep:
                        bad_counter += 1
                        play_sound('sound/063_삐삑 (오답 -짧은).mp3') # 👎 나쁜 자세로 카운트 시
                    else:
                        good_counter += 1
                        
                        # 🎉 세트 완료 여부를 먼저 체크 (오디오 충돌 방지)
                        if good_counter == SET_GOAL:
                            workout_state = 'rest'
                            rest_start_time = time.time()
                            feedback = "" # 휴식 모드로 전환
                            play_sound(r'C:\GITHUB\AI-HomeTrainer\sound\0289-예_.wav') # 🎉 세트 완료 효과음만 재생
                        else:
                            # 세트가 아직 끝나지 않았을 때만 '좋은 자세' 피드백 재생
                            feedback = "GOOD"
                            feedback_start_time = time.time()
                            play_sound(r'C:\GITHUB\AI-HomeTrainer\sound\correct-choice-43861.mp3') # 👍 좋은 자세로 카운트 시

        except Exception as e:
            pass

        # 운동 중 UI 그리기 (기존과 동일 + 세트 번호 추가)
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
        # 기존 정보창 UI    
        overlay = image.copy(); alpha = 0.6
        draw_rounded_rectangle(overlay, (0, 0, 200, 145), 20, (0,0,0), -1)
        image = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
        
        # --- 3. UI에 세트 번호 추가 ---
        image = draw_text(image, f'SET {set_counter}', (10, 10), FONT_PATH, 18, (255, 255, 255))
        image = draw_text(image, 'TOTAL REPS', (10, 35), FONT_PATH, 16, (200, 200, 200))
        image = draw_text(image, str(counter), (130, 35), FONT_PATH, 18, (255, 255, 255))
        image = draw_text(image, 'GOOD', (10, 65), FONT_PATH, 16, (0, 255, 0))
        image = draw_text(image, str(good_counter), (70, 65), FONT_PATH, 18, (255, 255, 255))
        image = draw_text(image, 'BAD', (120, 65), FONT_PATH, 16, (255, 0, 0))
        image = draw_text(image, str(bad_counter), (170, 65), FONT_PATH, 18, (255, 255, 255))
        image = draw_text(image, 'STAGE', (10, 95), FONT_PATH, 16, (200, 200, 200))
        image = draw_text(image, stage.upper(), (90, 95), FONT_PATH, 18, (255, 255, 255))
        feedback_color = (0, 255, 0) if feedback == "GOOD" else (255, 0, 0)
        image = draw_text(image, feedback, (10, 120), FONT_PATH, 18, feedback_color)

        # --- 👇 [3. 진행률 바 그리기] ---
        # 바(Bar)의 위치와 크기 설정
        bar_x, bar_y, bar_w, bar_h = 220, 10, 25, 125
        
        # 바의 배경 그리기
        cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (200, 200, 200), 2)
        
        # 바의 내용(fill) 그리기
        fill_h = int(bar_h * smoothed_bar / 100.0)
        cv2.rectangle(image, (bar_x, bar_y + bar_h - fill_h), (bar_x + bar_w, bar_y + bar_h), (255, 255, 255), -1)
        
        # 디버깅을 위해 현재 각도와 퍼센트 값을 바 옆에 텍스트로 표시
        try:
            # knee_angle 변수가 존재할 때만 텍스트를 그립니다.
            image = draw_text(image, f'ANGLE: {round(knee_angle, 1)}', (bar_x + 30, bar_y + 20), FONT_PATH, 14, (255,255,0))
            image = draw_text(image, f'PERCENT: {round(bar_percentage, 1)}%', (bar_x + 30, bar_y + 50), FONT_PATH, 14, (255,255,0))
        except:
            # knee_angle이 없으면(포즈 미감지) 아무것도 하지 않음
            pass

    # 최종 화면 출력 (기존과 동일)
    image = cv2.resize(image, (1280, 720), interpolation=cv2.INTER_AREA)
    cv2.imshow('AI Home Trainer', image)
    if cv2.waitKey(5) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()