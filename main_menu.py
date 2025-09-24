# main_menu.py
import sys
import subprocess
import os
import random
import json
import cv2  # <<< 웹캠 확인을 위해 추가

from datetime import datetime
from style_sheet import DARK_STYLESHEET, CARD_STYLESHEET
from database_manager import init_db, get_records_by_exercise
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel, QMessageBox, QFrame, QHBoxLayout, QStackedWidget,
    QGroupBox, QRadioButton, QCheckBox, QSlider, QLineEdit,
    QScrollArea
)
from PyQt6.QtGui import QFont, QIntValidator
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

# --- 메인 메뉴 위젯 (변경 없음) ---
class MainMenuWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout=QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label=QLabel("AI Home Trainer");title_label.setObjectName("TitleLabel");title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label=QLabel("Next Generation Fitness Client");subtitle_label.setObjectName("SubtitleLabel");subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch(1);main_layout.addWidget(title_label);main_layout.addWidget(subtitle_label)
        menu_container=QWidget();menu_container.setObjectName("MenuContainer");menu_container.setFixedWidth(400)
        menu_layout=QVBoxLayout(menu_container);menu_layout.setContentsMargins(30,30,30,30);menu_layout.setSpacing(15)
        self.squat_button=QPushButton("스쿼트 (Squat)");menu_layout.addWidget(self.squat_button)
        self.pushup_button=QPushButton("푸쉬업 (Push-up)");menu_layout.addWidget(self.pushup_button)
        self.pullup_button=QPushButton("턱걸이 (Pull-up)");menu_layout.addWidget(self.pullup_button)
        self.records_button=QPushButton("내 기록 (My Records)");menu_layout.addWidget(self.records_button)
        self.chatbot_button=QPushButton("챗봇 (Chatbot)");menu_layout.addWidget(self.chatbot_button)
        self.settings_button=QPushButton("환경설정 (Settings)");menu_layout.addWidget(self.settings_button)
        menu_layout.addSpacing(20)
        self.exit_button=QPushButton("종료 (Quit)");self.exit_button.setObjectName("DangerButton");menu_layout.addWidget(self.exit_button)
        main_layout.addWidget(menu_container,alignment=Qt.AlignmentFlag.AlignCenter);main_layout.addStretch(2)
        footer_label=QLabel("제작자: ghpark00  |  이메일: fkzpt345@gmail.com");footer_label.setObjectName("FooterLabel");footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter);main_layout.addWidget(footer_label)

# --- 운동 기록 선택 위젯 (변경 없음) ---
class ExerciseSelectionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ExerciseSelectionScreen")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container = QWidget()
        container.setObjectName("MenuContainer")
        container.setFixedWidth(400)
        container_layout = QVBoxLayout(container)

        title_label = QLabel("조회할 운동 기록을 선택하세요")
        title_label.setObjectName("SubtitleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title_label)

        self.squat_button = QPushButton("스쿼트")
        container_layout.addWidget(self.squat_button)

        self.pushup_button = QPushButton("푸쉬업") 
        container_layout.addWidget(self.pushup_button)

        self.pullup_button = QPushButton("턱걸이 (준비중)")
        self.pullup_button.setEnabled(False)
        container_layout.addWidget(self.pullup_button)

        container_layout.addSpacing(20)
        self.back_button = QPushButton("메인 메뉴로 돌아가기")
        container_layout.addWidget(self.back_button)
        layout.addWidget(container)

# --- 개별 기록 카드 위젯 (변경 없음) ---
class RecordCardWidget(QWidget):
    def __init__(self, record_data, parent=None):
        super().__init__(parent)
        self.setObjectName("RecordCard")
        timestamp, _, reps, sets, rest, details_json = record_data
        
        layout = QVBoxLayout(self)
        
        dt_object = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        date_label = QLabel(dt_object.strftime("%Y년 %m월 %d일 %H:%M"))
        date_label.setObjectName("RecordDate")
        layout.addWidget(date_label)

        try:
            details_list = json.loads(details_json)
            total_good = sum(item['good'] for item in details_list)
            details_str = ", ".join([f"S{i+1}: G{item['good']}/B{item['bad']}" for i, item in enumerate(details_list)])
        except (json.JSONDecodeError, TypeError):
            total_good = "N/A"
            details_str = "데이터 오류"

        stats_text = f"""
        🏋️‍♂️ &nbsp;<b>설정:</b> {reps}회 / {sets}세트 / {rest}초 휴식<br>
        ✅ &nbsp;<b>총 성공:</b> {total_good}회<br>
        📊 &nbsp;<b>세트별:</b> {details_str}
        """
        stats_label = QLabel(stats_text)
        stats_label.setObjectName("RecordStats")
        stats_label.setWordWrap(True)
        layout.addWidget(stats_label)

# --- 내 기록 표시 위젯 (변경 없음) ---
class RecordsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RecordsScreen")
        self.setStyleSheet(CARD_STYLESHEET)
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        container = QWidget()
        container.setObjectName("MenuContainer")
        container.setFixedWidth(500)
        container_layout = QVBoxLayout(container)

        self.title_label = QLabel("운동 기록")
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.title_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.record_list_widget = QWidget()
        self.record_list_widget.setObjectName("RecordListWidget")
        self.record_list_layout = QVBoxLayout(self.record_list_widget)
        self.record_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(self.record_list_widget)
        container_layout.addWidget(scroll_area)

        self.back_button = QPushButton("뒤로가기")
        container_layout.addWidget(self.back_button)
        main_layout.addWidget(container)

    def load_records(self, exercise_type):
        self.title_label.setText(f"'{exercise_type}' 운동 기록")
        for i in reversed(range(self.record_list_layout.count())): 
            self.record_list_layout.itemAt(i).widget().setParent(None)

        records = get_records_by_exercise(exercise_type)
        if not records:
            no_record_label = QLabel("아직 저장된 기록이 없습니다.")
            no_record_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.record_list_layout.addWidget(no_record_label)
            return
            
        for record in records:
            card = RecordCardWidget(record)
            self.record_list_layout.addWidget(card)

# --- 운동 설정 위젯 (변경 없음) ---
class SquatSettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SquatSettingsScreen")
        layout=QVBoxLayout(self);layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container=QWidget();container.setObjectName("MenuContainer");container.setFixedWidth(450);container_layout=QVBoxLayout(container)
        settings_group=QGroupBox("스쿼트 설정");settings_layout=QVBoxLayout();settings_layout.setSpacing(15)
        validator=QIntValidator(1,999)
        reps_layout=QHBoxLayout();reps_label=QLabel("한 세트당 목표 횟수:");self.reps_input=QLineEdit("5");self.reps_input.setValidator(validator)
        reps_layout.addWidget(reps_label);reps_layout.addWidget(self.reps_input);settings_layout.addLayout(reps_layout)
        sets_layout=QHBoxLayout();sets_label=QLabel("총 목표 세트 수:");self.sets_input=QLineEdit("3");self.sets_input.setValidator(validator)
        sets_layout.addWidget(sets_label);sets_layout.addWidget(self.sets_input);settings_layout.addLayout(sets_layout)
        rest_layout=QHBoxLayout();rest_label=QLabel("휴식 시간 (초):");self.rest_input=QLineEdit("30");self.rest_input.setValidator(validator)
        rest_layout.addWidget(rest_label);rest_layout.addWidget(self.rest_input);settings_layout.addLayout(rest_layout)
        settings_group.setLayout(settings_layout);container_layout.addWidget(settings_group);container_layout.addStretch(1)
        button_layout=QHBoxLayout();self.back_button=QPushButton("뒤로가기");self.start_button=QPushButton("운동 시작");self.start_button.setObjectName("SuccessButton")
        button_layout.addWidget(self.back_button);button_layout.addWidget(self.start_button);container_layout.addLayout(button_layout)
        layout.addWidget(container)

class PushupSettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PushupSettingsScreen")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container = QWidget()
        container.setObjectName("MenuContainer")
        container.setFixedWidth(450)
        container_layout = QVBoxLayout(container)
        settings_group = QGroupBox("푸쉬업 설정")
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(15)
        validator = QIntValidator(1, 999)
        reps_layout = QHBoxLayout()
        reps_label = QLabel("한 세트당 목표 횟수:")
        self.reps_input = QLineEdit("10")
        self.reps_input.setValidator(validator)
        reps_layout.addWidget(reps_label)
        reps_layout.addWidget(self.reps_input)
        settings_layout.addLayout(reps_layout)
        sets_layout = QHBoxLayout()
        sets_label = QLabel("총 목표 세트 수:")
        self.sets_input = QLineEdit("3")
        self.sets_input.setValidator(validator)
        sets_layout.addWidget(sets_label)
        sets_layout.addWidget(self.sets_input)
        settings_layout.addLayout(sets_layout)
        rest_layout = QHBoxLayout()
        rest_label = QLabel("휴식 시간 (초):")
        self.rest_input = QLineEdit("30")
        self.rest_input.setValidator(validator)
        rest_layout.addWidget(rest_label)
        rest_layout.addWidget(self.rest_input)
        settings_layout.addLayout(rest_layout)
        settings_group.setLayout(settings_layout)
        container_layout.addWidget(settings_group)
        container_layout.addStretch(1)
        button_layout = QHBoxLayout()
        self.back_button = QPushButton("뒤로가기")
        self.start_button = QPushButton("운동 시작")
        self.start_button.setObjectName("SuccessButton")
        button_layout.addWidget(self.back_button)
        button_layout.addWidget(self.start_button)
        container_layout.addLayout(button_layout)
        layout.addWidget(container)

class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsScreen")
        layout=QVBoxLayout(self);layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container=QWidget();container.setObjectName("MenuContainer");container.setFixedWidth(450);container_layout=QVBoxLayout(container)
        music_group=QGroupBox("배경음악");music_layout=QVBoxLayout();self.music_checkbox=QCheckBox("배경음악 켜기 / 끄기");self.music_checkbox.setChecked(True);music_layout.addWidget(self.music_checkbox)
        volume_layout=QHBoxLayout();self.volume_slider=QSlider(Qt.Orientation.Horizontal);self.volume_slider.setRange(0,100);self.volume_slider.setValue(50);self.volume_label=QLabel("50%");self.volume_label.setFixedWidth(40)
        volume_layout.addWidget(QLabel("볼륨:"));volume_layout.addWidget(self.volume_slider);volume_layout.addWidget(self.volume_label);music_layout.addLayout(volume_layout);music_group.setLayout(music_layout);container_layout.addWidget(music_group)
        controls_group=QGroupBox("조작법 안내");controls_layout=QVBoxLayout();controls_label=QLabel("운동 시작 후 'ESC' 키를 누르면 프로그램이 종료됩니다.");controls_label.setWordWrap(True);controls_layout.addWidget(controls_label)
        controls_group.setLayout(controls_layout);container_layout.addWidget(controls_group);container_layout.addStretch(1)
        self.back_button=QPushButton("메인 메뉴로 돌아가기");container_layout.addWidget(self.back_button);layout.addWidget(container)

class LoadingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent);self.setObjectName("LoadingScreen");layout=QVBoxLayout(self);layout.setAlignment(Qt.AlignmentFlag.AlignCenter);layout.setSpacing(20)
        self.animation_label=QLabel();self.animation_label.setAlignment(Qt.AlignmentFlag.AlignCenter);self.animation_label.setObjectName("TitleLabel");self.animation_label.setStyleSheet("font-size: 40px;");layout.addWidget(self.animation_label)
        self.loading_text=QLabel("프로그램 실행중...");self.loading_text.setObjectName("SubtitleLabel");self.loading_text.setAlignment(Qt.AlignmentFlag.AlignCenter);layout.addWidget(self.loading_text)
        self.timer=QTimer(self);self.timer.timeout.connect(self.update_animation);self.animation_chars=["◐","◓","◑","◒"];self.animation_index=0
    def set_loading_text(self, text): self.loading_text.setText(text)
    def start_animation(self):self.animation_index=0;self.timer.start(150)
    def stop_animation(self):self.timer.stop()
    def update_animation(self):self.animation_label.setText(self.animation_chars[self.animation_index]);self.animation_index=(self.animation_index + 1) % len(self.animation_chars)

# --- [새로운 함수] 웹캠 가용성 체크 ---
def is_camera_available():
    """시스템의 기본 웹캠이 사용 가능한지 확인합니다."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return False
    # 사용 가능하면 자원을 즉시 해제하여 다른 프로세스가 사용할 수 있도록 함
    cap.release()
    return True

# --- 메인 윈도우 ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 홈 트레이너")
        self.setFixedSize(550, 750)
        self.setObjectName("MainWindow")
        
        init_db()

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 위젯 인스턴스 생성
        self.main_menu = MainMenuWidget()
        self.squat_settings = SquatSettingsWidget()
        self.pushup_settings = PushupSettingsWidget()
        self.settings_menu = SettingsWidget()
        self.loading_screen = LoadingWidget()
        self.exercise_selection_menu = ExerciseSelectionWidget()
        self.records_menu = RecordsWidget()
        
        # 스택 위젯에 추가
        self.stacked_widget.addWidget(self.main_menu)
        self.stacked_widget.addWidget(self.squat_settings)
        self.stacked_widget.addWidget(self.pushup_settings)
        self.stacked_widget.addWidget(self.settings_menu)
        self.stacked_widget.addWidget(self.loading_screen)
        self.stacked_widget.addWidget(self.exercise_selection_menu)
        self.stacked_widget.addWidget(self.records_menu)
        
        self.player = QMediaPlayer();self.audio_output = QAudioOutput();self.player.setAudioOutput(self.audio_output);self.audio_output.setVolume(0.5)
        self.playlist, self.current_track_index = [], 0
        self.setup_playlist()
        self.connect_signals()

    def connect_signals(self):
        # 메인 메뉴
        self.main_menu.squat_button.clicked.connect(self.show_squat_settings_screen)
        self.main_menu.pushup_button.clicked.connect(self.show_pushup_settings_screen)
        self.main_menu.chatbot_button.clicked.connect(self.start_chatbot_program) # <<< start_chatbot_program 으로 변경
        self.main_menu.records_button.clicked.connect(self.show_exercise_selection_screen)
        self.main_menu.settings_button.clicked.connect(self.show_settings_screen)
        self.main_menu.exit_button.clicked.connect(self.close)
        
        # 준비중인 기능
        self.main_menu.pullup_button.clicked.connect(self.feature_coming_soon)

        # 스쿼트 설정
        self.squat_settings.back_button.clicked.connect(self.show_main_menu_screen)
        self.squat_settings.start_button.clicked.connect(self.start_squat_program)

        # 푸쉬업 설정
        self.pushup_settings.back_button.clicked.connect(self.show_main_menu_screen)
        self.pushup_settings.start_button.clicked.connect(self.start_pushup_program)

        # 운동 기록 선택
        self.exercise_selection_menu.back_button.clicked.connect(self.show_main_menu_screen)
        self.exercise_selection_menu.squat_button.clicked.connect(lambda: self.show_records_screen('스쿼트'))
        self.exercise_selection_menu.pushup_button.clicked.connect(lambda: self.show_records_screen('푸쉬업'))

        # 기록 화면
        self.records_menu.back_button.clicked.connect(self.show_exercise_selection_screen)

        # 환경설정 및 음악 플레이어
        self.settings_menu.back_button.clicked.connect(self.show_main_menu_screen)
        self.settings_menu.music_checkbox.stateChanged.connect(self.toggle_music)
        self.settings_menu.volume_slider.valueChanged.connect(self.set_volume)
        self.player.mediaStatusChanged.connect(self.play_next_song)
    
    # --- 화면 전환 메소드 (변경 없음) ---
    def show_main_menu_screen(self): self.stacked_widget.setCurrentWidget(self.main_menu)
    def show_squat_settings_screen(self): self.stacked_widget.setCurrentWidget(self.squat_settings)
    def show_pushup_settings_screen(self): self.stacked_widget.setCurrentWidget(self.pushup_settings)
    def show_settings_screen(self): self.stacked_widget.setCurrentWidget(self.settings_menu)
    def show_exercise_selection_screen(self): self.stacked_widget.setCurrentWidget(self.exercise_selection_menu)
    def show_records_screen(self, exercise_type):
        self.records_menu.load_records(exercise_type)
        self.stacked_widget.setCurrentWidget(self.records_menu)

    # --- [수정] 챗봇 프로그램을 별도 프로세스로 실행하는 함수 ---
    def start_chatbot_program(self):
        # 실행 전 API 키 유무를 메인 메뉴에서 먼저 확인
        API_KEY = os.getenv("OPENAI_API_KEY")
        if not API_KEY:
            self.show_error_message(
                "OpenAI API 키가 설정되지 않았습니다.\n"
                "환경 변수 'OPENAI_API_KEY'를 설정한 후\n"
                "프로그램을 다시 시작해주세요."
            )
            return
        
        try:
            # 챗봇 스크립트를 독립적인 프로세스로 실행
            # (self.process 에 할당하거나 타이머로 확인할 필요 없음)
            subprocess.Popen(["python", "chatbot.py"])
        except Exception as e:
            self.show_error_message(f"챗봇을 시작하는 중 오류 발생: {e}")

    # --- 기능 메소드 (음악 관련 변경 없음) ---
    def setup_playlist(self):
        sound_dir = 'background_music'
        if not os.path.isdir(sound_dir): return
        try:
            supported = ('.mp3', '.wav', '.ogg')
            music_files = [f for f in os.listdir(sound_dir) if f.lower().endswith(supported)]
            if not music_files: return
            self.playlist = [QUrl.fromLocalFile(os.path.join(sound_dir, f)) for f in music_files]
            random.shuffle(self.playlist); self.player.setSource(self.playlist[0])
            if self.settings_menu.music_checkbox.isChecked(): self.player.play()
        except Exception as e: print(f"배경음악 재생 목록 설정 실패: {e}")

    def play_next_song(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self.playlist:
            self.current_track_index = (self.current_track_index + 1) % len(self.playlist)
            self.player.setSource(self.playlist[self.current_track_index]); self.player.play()
            
    def toggle_music(self, state):
        if state == Qt.CheckState.Checked.value:
            if self.player.mediaStatus() != QMediaPlayer.MediaStatus.NoMedia: self.player.play()
        else: self.player.pause()

    def set_volume(self, value):
        self.audio_output.setVolume(value / 100.0); self.settings_menu.volume_label.setText(f"{value}%")
    
    # --- 운동 프로그램 시작 함수 (웹캠 체크 추가) ---
    def start_squat_program(self):
        # <<< [수정] 웹캠 연결 상태 확인
        if not is_camera_available():
            self.show_error_message("웹캠이 연결되어 있지 않습니다!\n웹캠을 연결한 후 다시 시도해주세요.")
            return

        try:
            reps, sets, rest = self.squat_settings.reps_input.text(), self.squat_settings.sets_input.text(), self.squat_settings.rest_input.text()
            if not (reps and sets and rest and int(reps) > 0 and int(sets) > 0 and int(rest) > 0):
                self.show_error_message("모든 값은 0보다 큰 숫자로 입력해주세요.")
                return
            self.loading_screen.set_loading_text("스쿼트 프로그램 실행중...\n 카메라 각도를 올바른 방향으로 설정해주세요.")
            self.stacked_widget.setCurrentWidget(self.loading_screen)
            self.loading_screen.start_animation()
            self.process = subprocess.Popen(["python", "squat_ai_trainer.py", reps, sets, rest])
            self.check_timer = QTimer(self)
            self.check_timer.timeout.connect(self.check_process_finished)
            self.check_timer.start(500)
        except Exception as e:
            self.show_error_message(f"프로그램 시작 중 오류 발생: {e}")
            self.stacked_widget.setCurrentWidget(self.squat_settings)
    
    def start_pushup_program(self):
        # <<< [수정] 웹캠 연결 상태 확인
        if not is_camera_available():
            self.show_error_message("웹캠이 연결되어 있지 않습니다!\n웹캠을 연결한 후 다시 시도해주세요.")
            return
            
        try:
            reps, sets, rest = self.pushup_settings.reps_input.text(), self.pushup_settings.sets_input.text(), self.pushup_settings.rest_input.text()
            if not (reps and sets and rest and int(reps) > 0 and int(sets) > 0 and int(rest) > 0):
                self.show_error_message("모든 값은 0보다 큰 숫자로 입력해주세요.")
                return
            self.loading_screen.set_loading_text("푸쉬업 프로그램 실행중...\n 카메라 각도를 올바른 방향으로 설정해주세요.")
            self.stacked_widget.setCurrentWidget(self.loading_screen)
            self.loading_screen.start_animation()
            self.process = subprocess.Popen(["python", "pushup_ai_trainer.py", reps, sets, rest])
            self.check_timer = QTimer(self)
            self.check_timer.timeout.connect(self.check_process_finished)
            self.check_timer.start(500)
        except Exception as e:
            self.show_error_message(f"프로그램 시작 중 오류 발생: {e}")
            self.stacked_widget.setCurrentWidget(self.pushup_settings)

    # --- 유틸리티 메소드 (변경 없음) ---
    def check_process_finished(self):
        if self.process.poll() is not None:
            self.check_timer.stop()
            self.loading_screen.stop_animation()
            self.stacked_widget.setCurrentWidget(self.main_menu)

    def feature_coming_soon(self): QMessageBox.information(self, "알림", "🛠️ 현재 준비 중인 기능입니다. 🛠️")
    def show_error_message(self, message): QMessageBox.critical(self, "오류", message)

# --- 프로그램 실행 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Pretendard", 10))
    app.setStyleSheet(DARK_STYLESHEET)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())