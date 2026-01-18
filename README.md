# 🎙️ WinVoice

**WinVoice** is a professional, background-running desktop automation agent for Windows. It allows you to control your apps, browse the web, and execute complex multi-step workflows using natural voice commands.

![App Screenshot](https://via.placeholder.com/800x400?text=WinVoice+UI)

## ⚡ Features
* **Invisible & Fast:** Runs silently in the system tray.
* **Global Hotkey:** Summon instantly with `Ctrl + Space`.
* **Smart Routing:** Knows the difference between Modern Apps (Settings), Classic Apps (Notepad), and Websites.
* **Multi-Intent:** "Open YouTube AND search for trailers THEN open Notepad."
* **One-Click Setup:** Includes a graphical installer that handles dependencies and API keys.

## 🚀 Installation

1.  **Prepare Directory**
    Open Command Prompt (cmd) or PowerShell and navigate to the folder where you want to install WinVoice.
    ```bash
    cd Documents  # (Example: You can use any folder you like)
    ```

2.  **Clone the repository**
    ```bash
    git clone https://github.com/Vem-Manish/WinVoice.git
    cd WinVoice
    ```

3.  **Run the Installer**
    Double-click **`setup.bat`**.
    * This will install the engine, guide you through getting a free Gemini API Key, and set up auto-start.

4.  **That's it!**
    WinVoice is now running. Check your system tray (bottom right).

## 🎮 Usage

* **Summon:** Press `Ctrl + Space` to bring WinVoice to the front.
* **Speak:** Tap the Mic icon (or press Enter) and say a command.
* **Interrupt:** Tap the Mic again to force-stop listening and execute immediately.
* **Quit:** Right-click the Tray Icon -> Quit.

## 🛠️ Tech Stack
* **AI:** Google Gemma 2 / Gemini 1.5 Flash
* **GUI:** PySide6 (Qt)
* **Audio:** SpeechRecognition + PyAudio
* **System:** WinShell + PyWin32