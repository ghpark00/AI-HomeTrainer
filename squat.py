import cv2
import mediapipe as mp
import numpy as np
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

# MediaPipe Pose 모델 및 그리기 유틸리티 초기화
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

# 스쿼트 카운터를 위한 변수 초기화
counter = 0 
stage = 'up' # 'up' 또는 'down' 상태

# 웹캠 열기
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("카메라를 열 수 없습니다.")
    exit()

import time

# 카운터 및 피드백 변수 초기화
counter = 0 
good_counter = 0
bad_counter = 0
stage = 'up'
feedback = ""
feedback_start_time = 0
mistake_made_this_rep = False

# 비디오 스트림을 처리하기 위한 메인 루프
while cap.isOpened():
    success, image = cap.read()
    if not success:
        break

    # 1. 피드백 타이머 로직
    # 피드백 메시지가 뜬 후 2초가 지났으면 메시지를 지웁니다.
    if feedback != "" and time.time() - feedback_start_time > 2:
        feedback = ""

    # BGR 이미지를 RGB로 변환
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # MediaPipe Pose 모델로 이미지 처리
    results = pose.process(image_rgb)

    try:
        landmarks = results.pose_landmarks.landmark
        
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
            
            # 2. 실시간 피드백 로직
            if knee_angle < 60:
                feedback = "TOO DEEP"
                mistake_made_this_rep = True
                feedback_start_time = time.time() # 나쁜 피드백 시간 기록
            
            elif stage == 'down' and hip_angle < 100:
                feedback = "STRAIGHTEN BACK"
                mistake_made_this_rep = True
                feedback_start_time = time.time() # 나쁜 피드백 시간 기록
            
            # 3. 스쿼트 카운팅 로직
            if knee_angle < 100 and stage == 'up':
                stage = 'down'
                mistake_made_this_rep = False

            if knee_angle > 140 and stage == 'down':
                stage = 'up'
                counter += 1 # 총 횟수 증가
                
                # 4. GOOD/BAD 카운터 로직
                if mistake_made_this_rep:
                    bad_counter += 1
                    # 나쁜 자세로 REP을 마쳤으므로 별도 피드백 없음
                else:
                    good_counter += 1
                    feedback = "GOOD"
                    feedback_start_time = time.time() # 좋은 피드백 시간 기록

            # 각도 시각화
            cv2.putText(image, str(round(knee_angle, 2)), tuple(np.multiply(knee, [1280, 720]).astype(int)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

    except Exception as e:
        pass

    # --- ✅ [반투명 UI 수정 코드] ---

    # (이전 랜드마크 그리기 코드)
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    # --- 👇 [UI 표시 부분 전체 교체] ---

    # 1. 반투명 레이어를 위한 복사본 이미지 생성
    overlay = image.copy()
    alpha = 0.6  # 투명도 (0.0: 완전 투명, 1.0: 완전 불투명)

    # 2. 반투명 박스 그리기 (overlay 위에)
    draw_rounded_rectangle(overlay, (0, 0, 200, 120), 20, (0,0,0), -1)

    # 3. 원본 이미지와 반투명 레이어 합성
    # cv2.addWeighted(src1, alpha, src2, beta, gamma)
    # 결과 = overlay*alpha + image*(1-alpha) + 0
    image = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)

    # 4. 합성된 이미지 위에 텍스트 그리기 (더 선명하게 보임)
    # 총 횟수(REPS)
    image = draw_text(image, 'TOTAL REPS', (10, 10), FONT_PATH, 16, (200, 200, 200)) # (B,G,R) -> (R,G,B)
    image = draw_text(image, str(counter), (130, 10), FONT_PATH, 18, (255, 255, 255))

    # GOOD 카운트
    image = draw_text(image, 'GOOD', (10, 40), FONT_PATH, 16, (0, 255, 0))
    image = draw_text(image, str(good_counter), (70, 40), FONT_PATH, 18, (255, 255, 255))

    # BAD 카운트
    image = draw_text(image, 'BAD', (120, 40), FONT_PATH, 16, (255, 0, 0)) # 빨간색
    image = draw_text(image, str(bad_counter), (170, 40), FONT_PATH, 18, (255, 255, 255))

    # 현재 상태 (STAGE)
    image = draw_text(image, 'STAGE', (10, 70), FONT_PATH, 16, (200, 200, 200))
    image = draw_text(image, stage.upper(), (90, 70), FONT_PATH, 18, (255, 255, 255))

    # 피드백 메시지
    feedback_color = (0, 255, 0) if feedback == "GOOD" else (255, 0, 0)
    image = draw_text(image, feedback, (10, 95), FONT_PATH, 18, feedback_color)

    
    image = cv2.resize(image, (1920, 1080), interpolation=cv2.INTER_AREA)
    cv2.imshow('AI Home Trainer - Squat Counter', image)

    if cv2.waitKey(5) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()