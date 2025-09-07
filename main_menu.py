import sys
import subprocess
import os
import random
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QLabel, QMessageBox, QFrame, QHBoxLayout, QStackedWidget,
    QGroupBox, QRadioButton, QCheckBox, QSlider
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

# --- 스타일시트 (QSS): 다크 모드 ---
DARK_STYLESHEET = """
QWidget#MainWindow, QWidget#SettingsScreen {
    background-color: qlineargradient(x1:0.5, y1:0, x2:0.5, y2:1, stop:0 #242a38, stop:1 #12151c);
}
QWidget { color: #e0e0e0; font-family: "Pretendard", "Noto Sans KR", sans-serif; }
QLabel#TitleLabel { font-size: 48px; font-weight: 800; color: #5DADE2; padding-bottom: 5px; }
QLabel#SubtitleLabel { font-size: 16px; color: #bdc3c7; padding-bottom: 40px; }
QWidget#MenuContainer, QGroupBox { background-color: rgba(30, 33, 40, 0.8); border-radius: 15px; }
QPushButton { background-color: transparent; border: 2px solid #3e4147; border-radius: 10px; padding: 16px; font-size: 16px; font-weight: bold; color: #e0e0e0; }
QPushButton:hover { background-color: #2c2f36; border: 2px solid #5a5d63; }
QPushButton:pressed { background-color: #25282d; }
QPushButton#DangerButton { background-color: #9f3a3a; border: none; color: white; }
QPushButton#DangerButton:hover { background-color: #b84a4a; }
QPushButton#DangerButton:pressed { background-color: #8c2a2a; }
QLabel#FooterLabel { font-size: 12px; color: #7f8c8d; }
QGroupBox { padding: 20px; margin-top: 15px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; font-weight: bold; font-size: 18px; }
QRadioButton, QCheckBox { font-size: 14px; spacing: 10px; }
QRadioButton::indicator, QCheckBox::indicator { width: 20px; height: 20px; }

/* 알림창 스타일 추가 */
QMessageBox {
    background-color: #242a38;
}
QMessageBox QLabel {
    color: #e0e0e0;
    font-size: 14px;
}
QMessageBox QPushButton {
    background-color: transparent;
    border: 2px solid #5a5d63;
    border-radius: 8px;
    padding: 8px;
    min-width: 70px;
    font-size: 14px;
}
QMessageBox QPushButton:hover {
    background-color: #2c2f36;
}
QMessageBox QPushButton:pressed {
    background-color: #25282d;
}
"""

# --- 스타일시트 (QSS): 라이트 모드 ---
LIGHT_STYLESHEET = """
QWidget#MainWindow, QWidget#SettingsScreen {
    background-color: qlineargradient(x1:0.5, y1:0, x2:0.5, y2:1, stop:0 #ffffff, stop:1 #e8e8e8);
}
QWidget { color: #2c3e50; font-family: "Pretendard", "Noto Sans KR", sans-serif; }
QLabel#TitleLabel { font-size: 48px; font-weight: 800; color: #2980b9; padding-bottom: 5px; }
QLabel#SubtitleLabel { font-size: 16px; color: #34495e; padding-bottom: 40px; }
QWidget#MenuContainer, QGroupBox { background-color: rgba(255, 255, 255, 0.8); border: 1px solid #bdc3c7; border-radius: 15px; }
QPushButton { background-color: #3498db; border: none; border-radius: 10px; padding: 16px; font-size: 16px; font-weight: bold; color: white; }
QPushButton:hover { background-color: #2980b9; }
QPushButton:pressed { background-color: #1f618d; }
QPushButton#DangerButton { background-color: #e74c3c; border: none; color: white; }
QPushButton#DangerButton:hover { background-color: #c0392b; }
QPushButton#DangerButton:pressed { background-color: #a93226; }
QLabel#FooterLabel { font-size: 12px; color: #7f8c8d; }
QGroupBox { padding: 20px; margin-top: 15px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; font-weight: bold; font-size: 18px; }
QRadioButton, QCheckBox { font-size: 14px; spacing: 10px; }
QRadioButton::indicator, QCheckBox::indicator { width: 20px; height: 20px; }

/* 알림창 스타일 추가 */
QMessageBox {
    background-color: #f0f0f0;
}
QMessageBox QLabel {
    color: #2c3e50;
    font-size: 14px;
}
QMessageBox QPushButton {
    background-color: #3498db;
    border: none;
    border-radius: 8px;
    padding: 8px;
    min-width: 70px;
    font-size: 14px;
    color: white;
}
QMessageBox QPushButton:hover {
    background-color: #2980b9;
}
QMessageBox QPushButton:pressed {
    background-color: #1f618d;
}
"""

# --- 메인 메뉴 위젯 ---
class MainMenuWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("AI Home Trainer")
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle_label = QLabel("Next Generation Fitness Client")
        subtitle_label.setObjectName("SubtitleLabel")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addStretch(1)
        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)

        menu_container = QWidget()
        menu_container.setObjectName("MenuContainer")
        menu_container.setFixedWidth(400)

        menu_layout = QVBoxLayout(menu_container)
        menu_layout.setContentsMargins(30, 30, 30, 30)
        menu_layout.setSpacing(15)

        self.squat_button = QPushButton("스쿼트 (Squat)")
        menu_layout.addWidget(self.squat_button)
        
        self.pushup_button = QPushButton("푸쉬업 (Push-up)")
        menu_layout.addWidget(self.pushup_button)

        self.pullup_button = QPushButton("턱걸이 (Pull-up)")
        menu_layout.addWidget(self.pullup_button)

        self.chatbot_button = QPushButton("챗봇 (Chatbot)")
        menu_layout.addWidget(self.chatbot_button)
        
        self.settings_button = QPushButton("환경설정 (Settings)")
        menu_layout.addWidget(self.settings_button)

        menu_layout.addSpacing(20)

        self.exit_button = QPushButton("종료 (Quit)")
        self.exit_button.setObjectName("DangerButton")
        menu_layout.addWidget(self.exit_button)

        main_layout.addWidget(menu_container, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch(2)

        footer_label = QLabel("제작자: ghpark00  |  이메일: fkzpt345@gmail.com")
        footer_label.setObjectName("FooterLabel")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer_label)

# --- 환경설정 위젯 ---
class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsScreen")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        container = QWidget()
        container.setObjectName("MenuContainer")
        container.setFixedWidth(450)
        container_layout = QVBoxLayout(container)

        # 1. 배경음악 설정
        music_group = QGroupBox("배경음악")
        music_layout = QVBoxLayout()
        self.music_checkbox = QCheckBox("배경음악 켜기 / 끄기")
        self.music_checkbox.setChecked(True)
        music_layout.addWidget(self.music_checkbox)
        
        # 볼륨 조절 슬라이더 추가
        volume_layout = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50) # 초기 볼륨 50%
        
        self.volume_label = QLabel("50%") # 초기 볼륨 텍스트
        self.volume_label.setFixedWidth(40)

        volume_layout.addWidget(QLabel("볼륨:"))
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        
        music_layout.addLayout(volume_layout)
        music_group.setLayout(music_layout)
        container_layout.addWidget(music_group)
        
        # 2. 테마 선택
        theme_group = QGroupBox("테마 선택")
        theme_layout = QHBoxLayout()
        self.dark_mode_radio = QRadioButton("다크 모드")
        self.dark_mode_radio.setChecked(True)
        self.light_mode_radio = QRadioButton("라이트 모드")
        theme_layout.addWidget(self.dark_mode_radio)
        theme_layout.addWidget(self.light_mode_radio)
        theme_group.setLayout(theme_layout)
        container_layout.addWidget(theme_group)

        # 3. 조작법 안내
        controls_group = QGroupBox("조작법 안내")
        controls_layout = QVBoxLayout()
        controls_label = QLabel("운동 시작 후 'ESC' 키를 누르면 프로그램이 종료됩니다.")
        controls_label.setWordWrap(True)
        controls_layout.addWidget(controls_label)
        controls_group.setLayout(controls_layout)
        container_layout.addWidget(controls_group)
        
        container_layout.addStretch(1)

        # 4. 뒤로가기 버튼
        self.back_button = QPushButton("메인 메뉴로 돌아가기")
        container_layout.addWidget(self.back_button)

        layout.addWidget(container)

# --- 메인 윈도우 (화면 전환 관리) ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 홈 트레이너")
        self.setFixedSize(550, 750)
        self.setObjectName("MainWindow")

        # 화면 전환을 위한 QStackedWidget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 위젯 생성 및 추가
        self.main_menu = MainMenuWidget()
        self.settings_menu = SettingsWidget()
        self.stacked_widget.addWidget(self.main_menu)
        self.stacked_widget.addWidget(self.settings_menu)
        
        # 배경음악 플레이어 및 재생목록 설정
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.5) # 초기 볼륨 50%
        
        self.playlist = []
        self.current_track_index = 0
        self.setup_playlist()
        
        # 시그널 연결
        self.connect_signals()

    def connect_signals(self):
        # 메인 메뉴 버튼 연결
        self.main_menu.squat_button.clicked.connect(self.start_squat_program)
        self.main_menu.pushup_button.clicked.connect(self.feature_coming_soon)
        self.main_menu.pullup_button.clicked.connect(self.feature_coming_soon)
        self.main_menu.chatbot_button.clicked.connect(self.feature_coming_soon)
        self.main_menu.exit_button.clicked.connect(self.close)
        self.main_menu.settings_button.clicked.connect(self.show_settings_screen)

        # 설정 메뉴 버튼 연결
        self.settings_menu.back_button.clicked.connect(self.show_main_menu_screen)
        self.settings_menu.music_checkbox.stateChanged.connect(self.toggle_music)
        self.settings_menu.volume_slider.valueChanged.connect(self.set_volume)
        self.settings_menu.dark_mode_radio.toggled.connect(self.set_theme)
        
        # 노래가 끝나면 다음 곡 재생
        self.player.mediaStatusChanged.connect(self.play_next_song)

    def setup_playlist(self):
        """'sound' 폴더에서 음악 파일을 찾아 재생목록을 만들고 재생을 준비합니다."""
        sound_dir = 'background_music'
        supported_formats = ('.mp3', '.wav', '.ogg')
        
        if not os.path.isdir(sound_dir):
            print(f"'{sound_dir}' 폴더를 찾을 수 없습니다. 배경음악을 재생할 수 없습니다.")
            return

        try:
            music_files = [f for f in os.listdir(sound_dir) if f.lower().endswith(supported_formats)]
            if not music_files:
                print(f"'{sound_dir}' 폴더에 재생할 음악 파일이 없습니다.")
                return

            self.playlist = [QUrl.fromLocalFile(os.path.join(sound_dir, f)) for f in music_files]
            random.shuffle(self.playlist)

            self.current_track_index = 0
            self.player.setSource(self.playlist[self.current_track_index])
            
            if self.settings_menu.music_checkbox.isChecked():
                self.player.play()
        except Exception as e:
            print(f"배경음악 재생 목록 설정 실패: {e}")

    def play_next_song(self, status):
        """현재 곡 재생이 끝나면 재생목록의 다음 곡을 재생합니다."""
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self.playlist:
            self.current_track_index = (self.current_track_index + 1) % len(self.playlist)
            self.player.setSource(self.playlist[self.current_track_index])
            self.player.play()
            
    # --- 슬롯 함수 (화면 전환 및 기능) ---
    def show_main_menu_screen(self):
        self.stacked_widget.setCurrentIndex(0)

    def show_settings_screen(self):
        self.stacked_widget.setCurrentIndex(1)
        
    def toggle_music(self, state):
        if state == Qt.CheckState.Checked.value:
            if self.player.mediaStatus() != QMediaPlayer.MediaStatus.NoMedia:
                self.player.play()
        else:
            self.player.pause()

    def set_volume(self, value):
        """슬라이더 값에 따라 배경음악 볼륨을 조절합니다."""
        float_volume = value / 100.0
        self.audio_output.setVolume(float_volume)
        self.settings_menu.volume_label.setText(f"{value}%")
            
    def set_theme(self, checked):
        if checked:
            radio_button = self.sender()
            if radio_button.text() == "다크 모드":
                app.setStyleSheet(DARK_STYLESHEET)
            else:
                app.setStyleSheet(LIGHT_STYLESHEET)

    def start_squat_program(self):
        """스쿼트 AI 트레이너 프로그램을 실행합니다."""
        print("스쿼트 프로그램을 시작합니다...")
        try:
            # sys.executable은 앱을 번들로 만들 때 재귀적으로 خود를 실행할 수 있습니다.
            # 외부 스크립트를 실행하려면 'python'을 직접 사용하는 것이 더 안정적입니다.
            subprocess.Popen(["python", "squat_ai_trainer.py"])
        except FileNotFoundError:
            self.show_error_message(
                "'squat_ai_trainer.py' 파일을 찾을 수 없거나, "
                "시스템 환경 변수에 'python'이 등록되지 않았습니다."
            )
        except Exception as e:
            self.show_error_message(f"프로그램 실행 중 오류 발생: {e}")

    def feature_coming_soon(self):
        QMessageBox.information(self, "알림", "🛠️ 현재 준비 중인 기능입니다. 🛠️")

    def show_error_message(self, message):
        QMessageBox.critical(self, "오류", message)

# --- 프로그램 실행 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Pretendard", 10)
    app.setFont(font)
    app.setStyleSheet(DARK_STYLESHEET)
    
    main_window = MainWindow()
    main_window.show()
    
    sys.exit(app.exec())

