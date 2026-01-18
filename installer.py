import sys
import os
import subprocess
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QPushButton, QStackedWidget,
                               QProgressBar, QLineEdit, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QPixmap

# --- CONFIGURATION ---
# Ensure you have a folder named 'assets' with these images!
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
TUTORIAL_IMAGES = [
    "step1.png", "step2.png", "step3.png",
    "step4.png", "step5.png", "step6.png", "step7.png"
]


class InstallWorker(QThread):
    progress_signal = Signal(int)
    text_signal = Signal(str)
    finished_signal = Signal()

    def run(self):
        # We install dependencies here.
        # Note: We install winshell/pywin32 now so they are available later.
        packages = [
            "google-genai", "python-dotenv", "SpeechRecognition",
            "pyttsx3", "pyaudio", "keyboard", "winshell", "pywin32"
        ]

        total = len(packages)
        for i, package in enumerate(packages):
            self.text_signal.emit(f"Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            except:
                pass

            progress = int(((i + 1) / total) * 100)
            self.progress_signal.emit(progress)

        self.finished_signal.emit()


class ApiTestWorker(QThread):
    result_signal = Signal(bool, str)

    def __init__(self, api_key):
        super().__init__()
        self.api_key = api_key

    def run(self):
        try:
            # Import inside thread to ensure library exists
            from google import genai

            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model="gemma-2-9b-it",
                contents="Say hi"
            )
            if response.text:
                self.result_signal.emit(True, "Success")
            else:
                self.result_signal.emit(False, "Empty response from API")
        except Exception as e:
            self.result_signal.emit(False, str(e))


class InstallerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WinVoice Setup")
        self.setFixedSize(700, 500)
        self.setStyleSheet("background-color: #1E1E1E; color: white; font-family: 'Segoe UI';")

        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.init_install_page()  # 0
        self.init_slideshow_page()  # 1
        self.init_apikey_page()  # 2
        self.init_success_page()  # 3

        self.start_installation()

    # --- PAGES ---
    def init_install_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("🚀 Setting up your Environment")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #89A8C9;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("color: #AAAAAA; margin-top: 10px;")
        layout.addWidget(self.status_label, alignment=Qt.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(500)
        self.progress_bar.setStyleSheet("""
            QProgressBar {border: 2px solid #555; border-radius: 5px; text-align: center;}
            QProgressBar::chunk {background-color: #89A8C9;}
        """)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)
        self.central_widget.addWidget(page)

    def start_installation(self):
        self.install_worker = InstallWorker()
        self.install_worker.progress_signal.connect(self.progress_bar.setValue)
        self.install_worker.text_signal.connect(self.status_label.setText)
        self.install_worker.finished_signal.connect(self.on_install_finished)
        self.install_worker.start()

    def on_install_finished(self):
        QTimer.singleShot(1000, lambda: self.central_widget.setCurrentIndex(1))

    def init_slideshow_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        header = QLabel("How to get your Free Gemini API Key")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header, alignment=Qt.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setFixedSize(600, 350)
        self.image_label.setStyleSheet("border: 1px solid #333; background: #000;")
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label, alignment=Qt.AlignCenter)

        btn_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Previous")
        self.next_btn = QPushButton("Next")

        for btn in [self.prev_btn, self.next_btn]:
            btn.setFixedSize(100, 40)
            btn.setStyleSheet("background-color: #444; border-radius: 5px;")

        self.prev_btn.clicked.connect(self.prev_slide)
        self.next_btn.clicked.connect(self.next_slide)

        btn_layout.addWidget(self.prev_btn)
        btn_layout.addWidget(self.next_btn)
        layout.addLayout(btn_layout)

        self.current_slide = 0
        self.update_slide()
        self.central_widget.addWidget(page)

    def update_slide(self):
        if not TUTORIAL_IMAGES:
            self.image_label.setText("No images found in assets/")
            return

        img_path = os.path.join(ASSETS_DIR, TUTORIAL_IMAGES[self.current_slide])
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            self.image_label.setPixmap(pixmap.scaled(600, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.image_label.setText(f"Missing: {TUTORIAL_IMAGES[self.current_slide]}")

        if self.current_slide == len(TUTORIAL_IMAGES) - 1:
            self.next_btn.setText("Enter Key ➜")
            self.next_btn.setStyleSheet(
                "background-color: #89A8C9; color: black; border-radius: 5px; font-weight: bold;")
        else:
            self.next_btn.setText("Next")
            self.next_btn.setStyleSheet("background-color: #444; border-radius: 5px; color: white;")

        self.prev_btn.setEnabled(self.current_slide > 0)

    def next_slide(self):
        if self.current_slide < len(TUTORIAL_IMAGES) - 1:
            self.current_slide += 1
            self.update_slide()
        else:
            self.central_widget.setCurrentIndex(2)

    def prev_slide(self):
        if self.current_slide > 0:
            self.current_slide -= 1
            self.update_slide()

    def init_apikey_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)

        lbl = QLabel("Enter your Gemini API Key")
        lbl.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(lbl, alignment=Qt.AlignCenter)

        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("Paste key here (AIzaSy...)")
        self.api_input.setFixedWidth(400)
        self.api_input.setStyleSheet(
            "padding: 10px; font-size: 14px; border-radius: 5px; border: 1px solid #555; background: #222;")
        layout.addWidget(self.api_input, alignment=Qt.AlignCenter)

        self.test_btn = QPushButton("Verify & Launch")
        self.test_btn.setFixedSize(200, 50)
        self.test_btn.setStyleSheet(
            "background-color: #89A8C9; color: black; font-weight: bold; font-size: 16px; border-radius: 8px;")
        self.test_btn.clicked.connect(self.verify_key)
        layout.addWidget(self.test_btn, alignment=Qt.AlignCenter)

        self.back_to_slides_btn = QPushButton("Back to Instructions")
        self.back_to_slides_btn.setFlat(True)
        self.back_to_slides_btn.setStyleSheet("color: #888; text-decoration: underline;")
        self.back_to_slides_btn.clicked.connect(lambda: self.central_widget.setCurrentIndex(1))
        layout.addWidget(self.back_to_slides_btn, alignment=Qt.AlignCenter)

        self.central_widget.addWidget(page)

    def verify_key(self):
        key = self.api_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Error", "Please enter a key.")
            return

        self.test_btn.setText("Testing...")
        self.test_btn.setEnabled(False)

        self.api_worker = ApiTestWorker(key)
        self.api_worker.result_signal.connect(self.on_verify_result)
        self.api_worker.start()

    def on_verify_result(self, success, message):
        self.test_btn.setEnabled(True)
        self.test_btn.setText("Verify & Launch")

        if success:
            with open(".env", "w") as f:
                f.write(f"GOOGLE_API_KEY={self.api_input.text().strip()}")

            # CALL THE INTERNAL STARTUP FUNCTION
            self.create_startup_shortcut()

            self.central_widget.setCurrentIndex(3)
        else:
            QMessageBox.critical(self, "Validation Failed", f"Invalid API Key.\nError: {message}")

    # --- INTERNAL STARTUP LOGIC (No extra file needed) ---
    def create_startup_shortcut(self):
        try:
            # We import here because they were JUST installed
            import winshell
            from win32com.client import Dispatch

            project_dir = os.path.dirname(os.path.abspath(__file__))
            python_exe = sys.executable
            script_path = os.path.join(project_dir, "gui.py")
            startup_folder = winshell.startup()
            shortcut_path = os.path.join(startup_folder, "JarvisAgent.lnk")

            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = python_exe
            shortcut.Arguments = f'"{script_path}"'
            shortcut.WorkingDirectory = project_dir
            shortcut.IconLocation = python_exe
            shortcut.Description = "AI Desktop Agent"
            shortcut.save()
            print("Shortcut created successfully.")

        except Exception as e:
            QMessageBox.warning(self, "Startup Error", f"Could not create startup shortcut: {e}")

    def init_success_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)

        lbl = QLabel("✅ Setup Complete!")
        lbl.setStyleSheet("font-size: 28px; font-weight: bold; color: #4CAF50;")
        layout.addWidget(lbl, alignment=Qt.AlignCenter)

        sub = QLabel("The Agent has been added to startup.\nClick below to run it now.")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("font-size: 16px; color: #CCC; margin: 20px;")
        layout.addWidget(sub, alignment=Qt.AlignCenter)

        run_btn = QPushButton("Run Agent")
        run_btn.setFixedSize(200, 60)
        run_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; font-size: 18px; border-radius: 30px;")
        run_btn.clicked.connect(self.launch_agent)
        layout.addWidget(run_btn, alignment=Qt.AlignCenter)

        self.central_widget.addWidget(page)

    def launch_agent(self):
        # We use pythonw to launch it silently (no console)
        subprocess.Popen([sys.executable.replace("python.exe", "pythonw.exe"), "gui.py"])
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InstallerWindow()
    window.show()
    sys.exit(app.exec())