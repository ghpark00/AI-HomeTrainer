# chatbot.py (메시지 잘림 최종 해결 버전)
import sys
import os
import json
import re
import google.generativeai as genai
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel, QMessageBox, QHBoxLayout,
    QLineEdit, QTextEdit, QScrollArea, QInputDialog
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal

# --- UI 스타일 중앙 관리 설정 (변경 없음) ---
STYLE_CONFIG = {
    "window_width": 600, "window_height": 850, "base_font_size": 16,
    "placeholder_font_size": 15, "button_font_size": 24, "icon_size": 36,
    "send_button_size": 48, "padding": 12, "input_padding": 8,
    "spacing": 18, "bubble_radius": 16,
}

# --- 설정 파일 이름 및 API 키 변수 (변경 없음) ---
CONFIG_FILE = "config_gemini.json"
API_KEY = None

# --- [수정] 채팅 버블 위젯 (더 안정적인 크기 조절 방식으로 변경) ---
class MessageBubble(QWidget):
    def __init__(self, text, is_user):
        super().__init__()
        self.is_user = is_user

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        padding = STYLE_CONFIG['padding']
        radius = STYLE_CONFIG['bubble_radius']

        # QLabel에서는 max-width를 제거하여 부모 위젯의 크기에 따라 자연스럽게 줄바꿈되도록 함
        if is_user:
            self.label = QLabel(text)
            self.label.setWordWrap(True)
            self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.label.setStyleSheet(f"""
                QLabel {{
                    background-color: #1de9b6; color: #1e1e2f; padding: {padding}px {padding+2}px;
                    border-radius: {radius}px; border-bottom-right-radius: 4px;
                }}""")
            main_layout.addWidget(self.label)
        else:
            header_layout = QHBoxLayout()
            header_layout.setContentsMargins(0, 0, 0, 0); header_layout.setSpacing(10)
            icon_label = QLabel()
            icon_size = STYLE_CONFIG['icon_size']
            pixmap = QPixmap('images\icon\hticon03.png')
            icon_label.setPixmap(pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            icon_label.setFixedSize(icon_size, icon_size)
            name_label = QLabel("AI-HomeTrainer")
            name_label.setStyleSheet("font-weight: bold; color: #f5f5f5;")
            header_layout.addWidget(icon_label); header_layout.addWidget(name_label); header_layout.addStretch()
            self.label = QLabel(text)
            self.label.setWordWrap(True)
            self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.label.setStyleSheet(f"""
                QLabel {{
                    background-color: #2a2a40; color: #ffffff; padding: {padding}px {padding+2}px;
                    border-radius: {radius}px; border-bottom-left-radius: 4px;
                }}""")
            main_layout.addLayout(header_layout)
            main_layout.addWidget(self.label)

        self.setLayout(main_layout)

    def text(self): return self.label.text()
    def set_text(self, text): self.label.setText(text)
    def append_text(self, text): self.label.setText(self.label.text() + text)

    # 위젯 자체의 최대 너비를 업데이트하는 방식으로 변경
    def update_width(self, parent_width):
        max_w = int(parent_width * 0.75) # 버블이 차지할 최대 너비 (조금 더 넉넉하게)
        self.setMaximumWidth(max_w)


# --- 입력창 위젯 (변경 없음) ---
class ChatInputTextEdit(QTextEdit):
    send_message_signal = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("메시지를 입력하세요...")
        self.setToolTip("Shift+Enter로 줄바꿈할 수 있습니다.")
        self.setFixedHeight(STYLE_CONFIG['send_button_size'])
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.send_message_signal.emit()
        else:
            super().keyPressEvent(event)
        doc_height = self.document().size().toSize().height()
        max_height = 150; new_height = min(doc_height + 15, max_height)
        self.setFixedHeight(new_height)

# --- Gemini API Worker (변경 없음) ---
class GeminiWorker(QObject):
    chunk_received = pyqtSignal(str); stream_finished = pyqtSignal(); error_occurred = pyqtSignal(str)
    def __init__(self, message_history):
        super().__init__(); self.message_history = message_history
    def run(self):
        try:
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            history_for_gemini = [{'role': msg['role'], 'parts': [msg['content']]} for msg in self.message_history if msg['role'] != 'system']
            last_user_message = history_for_gemini.pop()['parts'][0]
            chat = model.start_chat(history=history_for_gemini)
            response_stream = chat.send_message(last_user_message, stream=True)
            for chunk in response_stream: self.chunk_received.emit(chunk.text)
            self.stream_finished.emit()
        except Exception as e: self.error_occurred.emit(f"API 오류: {e}")

# --- 챗봇 메인 위젯 (add_message_bubble 수정) ---
class ChatbotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages = [
            {"role": "system", "content": "너는 지금부터 사용자의 운동과 건강에 대해 조언해주는 AI 헬스 트레이너야. 모든 답변은 한국어로 해줘."},
            {"role": "user", "content": "안녕하세요! 어떤 운동에 대해 알려드릴까요?"},
            {"role": "assistant", "content": "저는 당신의 AI 헬스 트레이너입니다. 운동이나 건강에 대해 무엇이든 물어보세요."}
        ]
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10); main_layout.setSpacing(10)
        self.scroll_area = QScrollArea(); self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(STYLE_CONFIG['spacing'])
        self.scroll_area.setWidget(self.chat_container)
        input_layout = QHBoxLayout()
        self.input_box = ChatInputTextEdit()
        self.send_button = QPushButton("➤")
        button_size = STYLE_CONFIG['send_button_size']
        self.send_button.setFixedSize(button_size, button_size)
        input_layout.addWidget(self.input_box); input_layout.addWidget(self.send_button)
        main_layout.addWidget(self.scroll_area); main_layout.addLayout(input_layout)
        self.send_button.clicked.connect(self.send_message)
        self.input_box.send_message_signal.connect(self.send_message)
        self.load_initial_message()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_all_bubble_widths()

    def update_all_bubble_widths(self):
        # 스크롤 영역의 너비를 기준으로 자식 위젯들의 너비를 업데이트
        content_width = self.scroll_area.width() - 30
        if content_width <= 0: return
        for i in range(self.chat_layout.count()):
            widget = self.chat_layout.itemAt(i).widget()
            if isinstance(widget, MessageBubble):
                widget.update_width(content_width)

    def add_message_bubble(self, text, is_user):
        bubble = MessageBubble(text, is_user)
        # 버블을 추가한 후, 현재 창 크기에 맞게 너비를 즉시 업데이트
        content_width = self.scroll_area.width() - 30
        if content_width > 0:
            bubble.update_width(content_width)
            
        # 사용자 메시지는 오른쪽, AI 메시지는 왼쪽에 정렬되도록 컨테이너 추가
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0,0,0,0)
        if is_user:
            container_layout.addStretch()
            container_layout.addWidget(bubble)
        else:
            container_layout.addWidget(bubble)
            container_layout.addStretch()

        self.chat_layout.addWidget(container)
        
        QApplication.processEvents()
        scroll_bar = self.scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
        return bubble
    
    def load_initial_message(self): self.add_message_bubble(self.messages[2]['content'], is_user=False)

    def send_message(self):
        user_message = self.input_box.toPlainText().strip()
        if not user_message: return
        self.add_message_bubble(user_message, is_user=True)
        self.messages.append({"role": "user", "content": user_message})
        self.input_box.clear(); self.input_box.setFixedHeight(STYLE_CONFIG['send_button_size'])
        self.set_input_enabled(False)
        self.current_ai_bubble = self.add_message_bubble("...", is_user=False)
        self.thread = QThread(); self.worker = GeminiWorker(self.messages)
        self.worker.moveToThread(self.thread)
        self.worker.chunk_received.connect(self.update_ai_bubble)
        self.worker.stream_finished.connect(self.finish_stream)
        self.worker.error_occurred.connect(self.handle_error)
        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.stream_finished.connect(self.thread.quit)
        self.worker.error_occurred.connect(self.thread.quit)
        self.thread.start()

    def update_ai_bubble(self, chunk):
        if self.current_ai_bubble.text() == "...": self.current_ai_bubble.set_text(chunk)
        else: self.current_ai_bubble.append_text(chunk)
    def finish_stream(self):
        self.messages.append({"role": "assistant", "content": self.current_ai_bubble.text()})
        self.set_input_enabled(True)
    def handle_error(self, error_message):
        self.current_ai_bubble.set_text(error_message)
        self.current_ai_bubble.setStyleSheet("QLabel { color: #e74c3c; }")
        self.set_input_enabled(True)
    def set_input_enabled(self, enabled):
        self.input_box.setEnabled(enabled); self.send_button.setEnabled(enabled)
        if enabled: self.input_box.setFocus()

# --- 메인 윈도우 (변경 없음) ---
class ChatbotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 챗봇 트레이너"); self.resize(STYLE_CONFIG['window_width'], STYLE_CONFIG['window_height'])
        self.central_widget = ChatbotWidget(); self.setCentralWidget(self.central_widget)

# --- API 키 로드/저장 (변경 없음) ---
def load_api_key():
    global API_KEY; API_KEY = os.getenv("GOOGLE_API_KEY")
    if API_KEY: return True
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f: API_KEY = json.load(f).get("GOOGLE_API_KEY")
            if API_KEY: return True
        except (json.JSONDecodeError, IOError): return False
    return False
def save_api_key(key):
    try:
        with open(CONFIG_FILE, 'w') as f: json.dump({"GOOGLE_API_KEY": key}, f, indent=4)
        return True
    except IOError: return False

# --- main 실행 (변경 없음) ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    if not load_api_key():
        text, ok = QInputDialog.getText(None, "API 키 입력", "Google AI Studio에서 발급받은 API 키를 입력해주세요.")
        if ok and text: save_api_key(text); API_KEY = text
        else: QMessageBox.critical(None, "오류", "API 키가 없어 챗봇을 실행할 수 없습니다."); sys.exit(1)
    window = ChatbotWindow()
    app.setStyleSheet(f"""
    QWidget {{ background-color: #1e1e2f; color: #f5f5f5; font-family: 'Noto Sans KR', 'Pretendard', 'Malgun Gothic', sans-serif; font-size: {STYLE_CONFIG['base_font_size']}px; }}
    QToolTip {{ background-color: #f5f5f5; color: #1e1e2f; border: 1px solid #1de9b6; padding: 5px; border-radius: 4px; font-size: 13px; }}
    QScrollArea {{ border: none; background-color: #1e1e2f; }}
    QTextEdit {{ background-color: #2a2a40; border: 2px solid #00bcd4; border-radius: {STYLE_CONFIG['bubble_radius']}px; padding: {STYLE_CONFIG['input_padding']}px; color: #ffffff; }}
    QTextEdit:focus {{ border: 2px solid #1de9b6; }}
    QTextEdit::placeholder {{ color: #888899; font-size: {STYLE_CONFIG['placeholder_font_size']}px; }}
    QPushButton {{ background-color: #00bcd4; color: white; border-radius: {int(STYLE_CONFIG['send_button_size'] / 2)}px; font-size: {STYLE_CONFIG['button_font_size']}px; font-weight: bold; }}
    QPushButton:hover {{ background-color: #1de9b6; }}
    QPushButton:pressed {{ background-color: #0097a7; }}
    QLabel {{ font-size: {STYLE_CONFIG['base_font_size']}px; }}
    """)
    window.show()
    sys.exit(app.exec())