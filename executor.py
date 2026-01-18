import pyautogui
import time
import webbrowser
import pyperclip


def execute_step(step):
    try:
        action = step.get("action")

        if action == "WAIT":
            print(f"   ⏳ Waiting {step.get('seconds', 1)}s...")
            time.sleep(step.get("seconds", 1))

        elif action == "OPEN_APP":
            app_name = step.get("app")
            if not app_name:
                print("   ❌ Error: AI forgot the app name.")
                return

            print(f"   📱 Opening {app_name}...")
            # Win key opens the menu reliably
            pyautogui.press("win")
            time.sleep(0.5)
            pyautogui.write(app_name)
            time.sleep(0.2)
            pyautogui.press("enter")

        elif action == "OPEN_URL":
            url = step.get("url")
            if url:
                print(f"   🌐 Opening: {url}")
                webbrowser.open(url)

        elif action == "TYPE":
            text = step.get("text", "")
            print(f"   📋 Pasting...")
            pyperclip.copy(text)
            time.sleep(0.2)
            pyautogui.hotkey("ctrl", "v")

        elif action == "PRESS":
            keys = step.get("keys") or [step.get("key")]
            print(f"   🎹 Pressing: {keys}")

            # --- FIXED: The Reliable Screenshot Method ---
            # If the command is strictly "win + printscreen", we handle it manually
            # to ensure Windows catches the signal.
            if "win" in keys and "printscreen" in keys:
                pyautogui.keyDown("win")
                pyautogui.press("printscreen")
                time.sleep(0.1)  # Tiny pause to let OS register
                pyautogui.keyUp("win")
            else:
                # For everything else, use standard hotkey
                pyautogui.hotkey(*keys)
            # ---------------------------------------------

    except Exception as e:
        print(f"   ⚠️ Step Failed: {e}")