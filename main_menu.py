import sys
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QLabel, QMessageBox, QFrame, QHBoxLayout
)
from PyQt6.QtGui import QFont, QIcon, QMovie
from PyQt6.QtCore import Qt, QSize

# --- 스타일시트 (QSS): 앱의 전체 디자인을 담당 ---
# 첨부된 이미지 스타일을 기반으로 재구성된 스타일시트
APP_STYLESHEET = """
QWidget#MainWindow {
    /* 어두운 네이비에서 블랙으로 이어지는 그라데이션 배경 */
    background-color: qlineargradient(x1:0.5, y1:0, x2:0.5, y2:1,
                                      stop:0 #242a38, stop:1 #12151c);
}

QWidget {
    color: #e0e0e0; /* 전체 글자색 (밝은 회색) */
    font-family: "Pretendard", "Noto Sans KR", sans-serif;
}

/* 제목 라벨: 이미지의 'LiquidBounce'와 같이 그라데이션 효과를 줍니다 */
QLabel#TitleLabel {
    font-size: 48px;
    font-weight: 800; /* ExtraBold */
    color: #5DADE2; /* 기본 색상 */
    /* QSS만으로 텍스트 그라데이션은 어려워, 가장 두드러지는 파란색을 선택 */
    padding-bottom: 5px;
}

QLabel#SubtitleLabel {
    font-size: 16px;
    color: #bdc3c7; /* 부제목 글자색 (회색) */
    padding-bottom: 40px;
}

/* 메뉴 버튼을 감싸는 컨테이너 */
QWidget#MenuContainer {
    background-color: rgba(30, 33, 40, 0.8); /* 반투명한 어두운 배경 */
    border-radius: 15px;
}

/* 기본 버튼 스타일: 테두리가 있는 미니멀한 디자인 */
QPushButton {
    background-color: transparent;
    border: 2px solid #3e4147;
    border-radius: 10px;
    padding: 16px;
    font-size: 16px;
    font-weight: bold;
    color: #e0e0e0;
}

/* 버튼에 마우스를 올렸을 때 스타일 */
QPushButton:hover {
    background-color: #2c2f36;
    border: 2px solid #5a5d63;
}

/* 버튼을 클릭했을 때 스타일 */
QPushButton:pressed {
    background-color: #25282d;
}

/* 종료 버튼 스타일: 이미지의 'Quit Game' 버튼처럼 강조 */
QPushButton#DangerButton {
    background-color: #9f3a3a;
    border: none;
    color: white;
}

QPushButton#DangerButton:hover {
    background-color: #b84a4a;
}

QPushButton#DangerButton:pressed {
    background-color: #8c2a2a;
}

/* 하단 저작권/정보 라벨 */
QLabel#FooterLabel {
    font-size: 12px;
    color: #7f8c8d;
}
"""

class MainMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 홈 트레이너")
        self.setFixedSize(550, 750) # 창 크기 조정
        self.setObjectName("MainWindow")

        # --- 메인 위젯 및 레이아웃 설정 ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. 제목 섹션
        title_label = QLabel("AI Home Trainer")
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle_label = QLabel("Next Generation Fitness Client")
        subtitle_label.setObjectName("SubtitleLabel")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addStretch(1)
        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)

        # 2. 메뉴 버튼 컨테이너
        menu_container = QWidget()
        menu_container.setObjectName("MenuContainer")
        menu_container.setFixedWidth(400) # 컨테이너 너비 고정

        menu_layout = QVBoxLayout(menu_container)
        menu_layout.setContentsMargins(30, 30, 30, 30)
        menu_layout.setSpacing(15)

        # 버튼 생성
        squat_button = QPushButton("스쿼트 (Squat)")
        squat_button.clicked.connect(self.start_squat_program)
        menu_layout.addWidget(squat_button)
        
        pushup_button = QPushButton("푸쉬업 (Push-up)")
        pushup_button.clicked.connect(self.feature_coming_soon)
        menu_layout.addWidget(pushup_button)

        pullup_button = QPushButton("턱걸이 (Pull-up)")
        pullup_button.clicked.connect(self.feature_coming_soon)
        menu_layout.addWidget(pullup_button)

        chatbot_button = QPushButton("챗봇 (Chatbot)")
        chatbot_button.clicked.connect(self.feature_coming_soon)
        menu_layout.addWidget(chatbot_button)

        menu_layout.addSpacing(20) # 버튼과 종료 버튼 사이 간격

        # 종료 버튼
        exit_button = QPushButton("종료 (Quit)")
        exit_button.setObjectName("DangerButton") # 특별 스타일 적용
        exit_button.clicked.connect(self.close) # 앱 종료
        menu_layout.addWidget(exit_button)

        main_layout.addWidget(menu_container, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch(2)

        # 3. 하단 푸터
        footer_label = QLabel("Made with ❤️ for your health")
        footer_label.setObjectName("FooterLabel")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer_label)

    # --- 버튼 클릭 시 실행될 함수들 ---
    def start_squat_program(self):
        """스쿼트 AI 트레이너 프로그램을 실행합니다."""
        print("스쿼트 프로그램을 시작합니다...")
        try:
            subprocess.Popen([sys.executable, "squat_ai_trainer.py"])
        except FileNotFoundError:
            self.show_error_message(
                "squat_ai_trainer.py 파일을 찾을 수 없습니다.\n"
                "메인 프로그램과 같은 폴더에 있는지 확인해주세요."
            )
        except Exception as e:
            self.show_error_message(f"프로그램 실행 중 오류가 발생했습니다:\n{e}")

    def feature_coming_soon(self):
        """'준비 중' 메시지를 표시하는 함수"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("알림")
        msg_box.setText("🛠️ 현재 준비 중인 기능입니다. 🛠️")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.setStyleSheet("""
            QMessageBox { background-color: #1e2128; }
            QLabel { color: white; font-size: 14px; }
            QPushButton { 
                background-color: #9f3a3a; 
                color: white; 
                padding: 8px 20px; 
                border-radius: 5px; 
                border: none;
            }
        """)
        msg_box.exec()

    def show_error_message(self, message):
        """에러 메시지를 표시하는 함수"""
        QMessageBox.critical(self, "오류", message)

# --- 프로그램 실행 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    font = QFont("Pretendard", 10)
    app.setFont(font)

    app.setStyleSheet(APP_STYLESHEET)
    
    main_window = MainMenu()
    main_window.show()
    
    sys.exit(app.exec())

