# --- 스타일시트 (QSS): 다크 모드 ---
DARK_STYLESHEET = """
QWidget#MainWindow, QWidget#SettingsScreen, QWidget#SquatSettingsScreen, QWidget#LoadingScreen {
    background-color: qlineargradient(x1:0.5, y1:0, x2:0.5, y2:1, stop:0 #242a38, stop:1 #12151c);
}
QWidget { color: #e0e0e0; font-family: "Pretendard", "Noto Sans KR", sans-serif; }
QLabel#TitleLabel { font-size: 48px; font-weight: 800; color: #5DADE2; padding-bottom: 5px; }
QLabel#SubtitleLabel { font-size: 16px; color: #bdc3c7; padding-bottom: 40px; }
QWidget#MenuContainer, QGroupBox { background-color: rgba(30, 33, 40, 0.8); border-radius: 15px; }
QPushButton { background-color: transparent; border: 2px solid #3e4147; border-radius: 10px; padding: 16px; font-size: 16px; font-weight: bold; color: #e0e0e0; }
QPushButton:hover { background-color: #2c2f36; border: 2px solid #5a5d63; }
QPushButton:pressed { background-color: #25282d; }
QPushButton#SuccessButton { background-color: #27ae60; border: none; color: white; }
QPushButton#SuccessButton:hover { background-color: #2ecc71; }
QPushButton#SuccessButton:pressed { background-color: #229954; }
QPushButton#DangerButton { background-color: #9f3a3a; border: none; color: white; }
QPushButton#DangerButton:hover { background-color: #b84a4a; }
QPushButton#DangerButton:pressed { background-color: #8c2a2a; }
QLabel#FooterLabel { font-size: 12px; color: #7f8c8d; }
QGroupBox { padding: 20px; margin-top: 15px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; font-weight: bold; font-size: 18px; }
QRadioButton, QCheckBox { font-size: 14px; spacing: 10px; }
QRadioButton::indicator, QCheckBox::indicator { width: 20px; height: 20px; }
QLineEdit { border: 2px solid #3e4147; border-radius: 8px; padding: 10px; font-size: 16px; background-color: #2c2f36; }
QLineEdit:focus { border: 2px solid #5DADE2; }

/* 알림창 스타일 추가 */
QMessageBox { background-color: #242a38; }
QMessageBox QLabel { color: #e0e0e0; font-size: 14px; }
QMessageBox QPushButton { background-color: transparent; border: 2px solid #5a5d63; border-radius: 8px; padding: 8px; min-width: 70px; font-size: 14px; }
QMessageBox QPushButton:hover { background-color: #2c2f36; }
QMessageBox QPushButton:pressed { background-color: #25282d; }
"""

# --- 스타일시트 (QSS): 라이트 모드 ---
LIGHT_STYLESHEET = """
QWidget#MainWindow, QWidget#SettingsScreen, QWidget#SquatSettingsScreen, QWidget#LoadingScreen {
    background-color: qlineargradient(x1:0.5, y1:0, x2:0.5, y2:1, stop:0 #ffffff, stop:1 #e8e8e8);
}
QWidget { color: #2c3e50; font-family: "Pretendard", "Noto Sans KR", sans-serif; }
QLabel#TitleLabel { font-size: 48px; font-weight: 800; color: #2980b9; padding-bottom: 5px; }
QLabel#SubtitleLabel { font-size: 16px; color: #34495e; padding-bottom: 40px; }
QWidget#MenuContainer, QGroupBox { background-color: rgba(255, 255, 255, 0.8); border: 1px solid #bdc3c7; border-radius: 15px; }
QPushButton { background-color: #3498db; border: none; border-radius: 10px; padding: 16px; font-size: 16px; font-weight: bold; color: white; }
QPushButton:hover { background-color: #2980b9; }
QPushButton:pressed { background-color: #1f618d; }
QPushButton#SuccessButton { background-color: #27ae60; border: none; color: white; }
QPushButton#SuccessButton:hover { background-color: #2ecc71; }
QPushButton#SuccessButton:pressed { background-color: #229954; }
QPushButton#DangerButton { background-color: #e74c3c; border: none; color: white; }
QPushButton#DangerButton:hover { background-color: #c0392b; }
QPushButton#DangerButton:pressed { background-color: #a93226; }
QLabel#FooterLabel { font-size: 12px; color: #7f8c8d; }
QGroupBox { padding: 20px; margin-top: 15px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; font-weight: bold; font-size: 18px; }
QRadioButton, QCheckBox { font-size: 14px; spacing: 10px; }
QRadioButton::indicator, QCheckBox::indicator { width: 20px; height: 20px; }
QLineEdit { border: 1px solid #bdc3c7; border-radius: 8px; padding: 10px; font-size: 16px; background-color: #ffffff; }
QLineEdit:focus { border: 2px solid #3498db; }

/* 알림창 스타일 추가 */
QMessageBox { background-color: #f0f0f0; }
QMessageBox QLabel { color: #2c3e50; font-size: 14px; }
QMessageBox QPushButton { background-color: #3498db; border: none; border-radius: 8px; padding: 8px; min-width: 70px; font-size: 14px; color: white; }
QMessageBox QPushButton:hover { background-color: #2980b9; }
QMessageBox QPushButton:pressed { background-color: #1f618d; }
"""

# 카드 UI 스타일이 포함된 스타일시트
CARD_STYLESHEET = """
/* ... 기존 스타일 ... */
QWidget#MainWindow, QWidget#LoadingScreen, QWidget#SettingsScreen, QWidget#SquatSettingsScreen, QWidget#RecordsScreen, QWidget#ExerciseSelectionScreen {
    background-color: #282c34;
}
/* ... 기존 스타일 ... */
QPushButton {
    background-color: #4CAF50; /* Green */
    border: none;
    color: white;
    padding: 15px 32px;
    text-align: center;
    text-decoration: none;
    font-size: 16px;
    margin: 4px 2px;
    border-radius: 8px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #45a049;
}
QPushButton#DangerButton {
    background-color: #f44336; /* Red */
}
QPushButton#DangerButton:hover {
    background-color: #da190b;
}
QPushButton#SuccessButton {
    background-color: #008CBA; /* Blue */
}
QPushButton#SuccessButton:hover {
    background-color: #007ba7;
}
/* ... 기존 스타일 ... */

/* ▼▼▼ 기록 카드 UI 스타일 추가 ▼▼▼ */
QScrollArea {
    border: none;
}
QWidget#RecordListWidget {
    background-color: #2c313a;
    border-radius: 10px;
}
QWidget#RecordCard {
    background-color: #3a404c;
    border-radius: 8px;
    padding: 15px;
    margin: 0 10px 10px 10px;
}
QLabel#RecordDate {
    font-size: 18px;
    font-weight: bold;
    color: #61afef; /* 파란색 계열 */
    padding-bottom: 10px;
}
QLabel#RecordStats {
    font-size: 15px;
    color: #e6e6e6;
    line-height: 1.5;
}
"""