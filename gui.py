import sys
import threading
import math
import keyboard
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLineEdit, QPushButton, QLabel, QFrame,
                               QGraphicsDropShadowEffect, QSystemTrayIcon, QMenu)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QPoint, QRectF, QObject
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QCursor, QIcon, QPixmap, QAction

# Import backend
from router import route_intent
from executor import execute_step
import voice

# --- CONFIGURATION ---
COLOR_BG = "#1E1E1E"
COLOR_PILL = "#F5F5F7"
COLOR_ACCENT = "#89A8C9"
COLOR_TEXT = "#333333"
HOTKEY = "ctrl+space"


# --- HOTKEY BRIDGE ---
class HotkeyBridge(QObject):
    summon_signal = Signal()

    def __init__(self):
        super().__init__()
        try:
            keyboard.add_hotkey(HOTKEY, self.summon_signal.emit)
        except:
            pass


# --- WORKER THREADS ---
class VoiceWorker(QThread):
    finished = Signal(str)

    def run(self):
        text = voice.listen()
        self.finished.emit(text)


class LogicWorker(QThread):
    finished = Signal()

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        try:
            plan = route_intent(self.query)
            if not plan or "steps" not in plan:
                voice.speak("I didn't understand.")
                return

            for step in plan["steps"]:
                if step['action'] == 'OPEN_APP':
                    voice.speak(f"Opening {step.get('app', 'app')}")
                elif step['action'] == 'OPEN_URL':
                    voice.speak("Opening link")
                execute_step(step)
        except Exception as e:
            print(f"Logic Error: {e}")
        finally:
            self.finished.emit()


# --- CUSTOM WIDGET: BREATHING MIC ---
class BreathingMic(QWidget):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 300)
        self.is_listening = False
        self.is_processing = False
        self.pulse_phase = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)

    def animate(self):
        if self.is_listening or self.is_processing:
            self.pulse_phase += 0.1
            self.update()

    def mousePressEvent(self, event):
        self.clicked.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = QPoint(self.width() // 2, self.height() // 2)

        if self.is_listening:
            radius_offset = math.sin(self.pulse_phase) * 15
            color_alpha = int(100 - (math.sin(self.pulse_phase) * 50))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            pen = QPen(QColor(255, 85, 85, color_alpha))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawEllipse(center, 70 + radius_offset, 70 + radius_offset)
            painter.drawEllipse(center, 60 + (radius_offset * 0.5), 60 + (radius_offset * 0.5))

        elif self.is_processing:
            angle = -(self.pulse_phase * 20) % 360
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 170, 0))
            painter.translate(center)
            painter.rotate(angle)
            painter.drawEllipse(QPoint(70, 0), 6, 6)
            painter.resetTransform()

        painter.setPen(Qt.PenStyle.NoPen)
        if self.is_listening:
            painter.setBrush(QColor("#F5F5F7"))
        elif self.is_processing:
            painter.setBrush(QColor("#FFF5CC"))
        else:
            painter.setBrush(QColor("#F5F5F7"))
        painter.drawEllipse(center, 60, 60)

        painter.setPen(QColor("#333333"))
        font = QFont("Segoe UI Emoji", 32)
        painter.setFont(font)
        painter.drawText(QRectF(0, 0, 300, 300), Qt.AlignmentFlag.AlignCenter, "🎙️")


# --- MAIN WINDOW ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WinVoice")
        self.setFixedSize(500, 650)
        self.setStyleSheet(f"background-color: {COLOR_BG};")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(40, 60, 40, 40)

        self.mic_view = BreathingMic()
        self.mic_view.clicked.connect(self.toggle_voice)
        layout.addWidget(self.mic_view, alignment=Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel("Tap to Speak")
        self.status_label.setStyleSheet("color: #888888; font-size: 16px; font-family: 'Segoe UI';")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        layout.addStretch()

        self.pill_frame = QFrame()
        self.pill_frame.setFixedHeight(60)
        self.pill_frame.setStyleSheet(f"background-color: {COLOR_PILL}; border-radius: 30px;")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        self.pill_frame.setGraphicsEffect(shadow)

        pill_layout = QHBoxLayout(self.pill_frame)
        pill_layout.setContentsMargins(20, 5, 5, 5)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a message...")
        self.input_field.setStyleSheet(f"background: transparent; border: none; color: {COLOR_TEXT}; font-size: 16px;")
        self.input_field.returnPressed.connect(self.run_text_command)
        pill_layout.addWidget(self.input_field)

        self.send_btn = QPushButton("➜")
        self.send_btn.setFixedSize(50, 50)
        self.send_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.send_btn.clicked.connect(self.run_text_command)
        self.send_btn.setStyleSheet(
            f"background-color: {COLOR_ACCENT}; color: white; border-radius: 25px; font-size: 20px; border: none;")
        pill_layout.addWidget(self.send_btn)
        layout.addWidget(self.pill_frame)

        self.setup_tray()

        # Connect the hotkey bridge
        self.hotkey_bridge = HotkeyBridge()
        self.hotkey_bridge.summon_signal.connect(self.summon_window)

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(COLOR_ACCENT))
        painter = QPainter(pixmap)
        painter.setBrush(QColor("white"))
        painter.drawEllipse(16, 16, 32, 32)
        painter.end()
        self.tray_icon.setIcon(QIcon(pixmap))

        menu = QMenu()
        menu.addAction("Show", self.show_window)
        menu.addAction("Quit", self.quit_app)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_activated)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.summon_window()

    def summon_window(self):
        # We always want to SHOW, never hide when summoned via hotkey
        self.show_window()

    def show_window(self):
        # --- FIXED: NUCLEAR FOCUS METHOD ---
        # 1. Temporarily enable "Always On Top" to force it above other apps
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        # 2. Restore if minimized
        self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()

        # 3. Focus the input box specifically
        self.input_field.setFocus()

        # 4. Remove the "Always On Top" flag after 100ms
        # If we don't do this, it will stay on top of everything forever.
        QTimer.singleShot(100, self.remove_always_on_top)

    def remove_always_on_top(self):
        # Reset to normal behavior so it can go behind other windows again
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def quit_app(self):
        self.tray_icon.hide()
        QApplication.quit()

    # --- LOGIC ---
    def toggle_voice(self):
        if self.mic_view.is_processing: return

        if not self.mic_view.is_listening:
            self.mic_view.is_listening = True
            self.status_label.setText("Listening... (Tap to Stop)")
            self.status_label.setStyleSheet("color: #ff5555; font-size: 16px;")

            self.voice_thread = VoiceWorker()
            self.voice_thread.finished.connect(self.on_voice_finished)
            self.voice_thread.start()
        else:
            voice.force_stop_listening()
            self.status_label.setText("Finishing...")
            self.status_label.setStyleSheet("color: #ffa500; font-size: 16px;")

    def on_voice_finished(self, text):
        self.mic_view.is_listening = False
        if text:
            self.input_field.setText(text)
            self.execute_command(text)
        else:
            self.reset_ui()

    def run_text_command(self):
        text = self.input_field.text()
        if not text: return
        self.execute_command(text)

    def execute_command(self, text):
        self.mic_view.is_processing = True
        self.status_label.setText("Thinking...")
        self.status_label.setStyleSheet("color: #ffa500; font-size: 16px;")

        self.logic_thread = LogicWorker(text)
        self.logic_thread.finished.connect(self.on_execution_finished)
        self.logic_thread.start()

    def on_execution_finished(self):
        self.mic_view.is_processing = False
        self.status_label.setText("Done")
        self.status_label.setStyleSheet("color: #4caf50; font-size: 16px;")
        self.input_field.clear()

        # Reset UI text after 2 seconds
        QTimer.singleShot(2000, self.reset_ui)

    def reset_ui(self):
        self.status_label.setText("Tap to Speak")
        self.status_label.setStyleSheet("color: #888888; font-size: 16px;")
        self.mic_view.is_processing = False
        self.mic_view.update()


if __name__ == "__main__":
    # 1. WINDOWS TASKBAR ICON FIX
    # This tells Windows: "I am a unique app, not just python.exe"
    import ctypes
    import os

    myappid = 'mycompany.winvoice.agent.v1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)

    # 2. SET THE GLOBAL APP ICON
    # This applies the icon to the Taskbar and the Window Title Bar
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()

    # Optional: Set the icon for the Window specifically just in case
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    print("🚀 Agent running in background. Press Ctrl+Space to open.")
    sys.exit(app.exec())