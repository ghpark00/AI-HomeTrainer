import cv2
import mediapipe as mp

# MediaPipe Pose 모델 및 그리기 유틸리티 초기화
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

# 웹캠 열기
# 0은 기본 카메라를 의미합니다. 다른 카메라를 사용하려면 1, 2 등으로 변경하세요.
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("카메라를 열 수 없습니다.")
    exit()

# 비디오 스트림을 처리하기 위한 메인 루프
while cap.isOpened():
    # 웹캠에서 프레임(이미지) 읽기
    success, image = cap.read()
    if not success:
        print("카메라 프레임을 읽을 수 없습니다.")
        break

    # 성능 향상을 위해 이미지를 읽기 전용으로 표시
    image.flags.writeable = False
    # BGR 이미지를 RGB로 변환 (MediaPipe는 RGB 입력을 사용)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # MediaPipe Pose 모델로 이미지 처리
    results = pose.process(image_rgb)

    # 다시 이미지를 쓰기 가능으로 변경
    image.flags.writeable = True
    # RGB 이미지를 다시 BGR로 변환 (OpenCV는 BGR을 사용해 화면에 표시)
    # 이 과정은 생략해도 되지만, 원본 색상을 유지하기 위해 포함합니다.
    # image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

    # 감지된 포즈 랜드마크 그리기
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
            connection_drawing_spec=mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
        )

    # 결과 이미지를 화면에 보여주기
    cv2.imshow('AI Home Trainer - Pose Estimation', image)

    # 'ESC' 키를 누르면 루프 종료
    if cv2.waitKey(5) & 0xFF == 27:
        break

# 사용이 끝난 자원 해제
cap.release()
cv2.destroyAllWindows()