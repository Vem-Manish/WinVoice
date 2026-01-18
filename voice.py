import speech_recognition as sr
import pyttsx3
import threading
import time
import audioop  # Used for detecting silence manually

# Global flag to control the listening loop
_stop_signal = False

# --- 1. SETUP MOUTH ---
try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    if len(voices) > 1:
        engine.setProperty('voice', voices[1].id)
    engine.setProperty('rate', 170)
except:
    pass


def speak(text):
    def _run():
        try:
            engine.say(text)
            engine.runAndWait()
        except:
            pass

    threading.Thread(target=_run).start()


# --- 2. SETUP EARS (Manual Loop) ---
def force_stop_listening():
    """Call this to immediately cut off the recording."""
    global _stop_signal
    _stop_signal = True


def listen():
    """
    Records audio until silence IS detected OR force_stop_listening() is called.
    """
    global _stop_signal
    _stop_signal = False  # Reset flag

    r = sr.Recognizer()
    r.energy_threshold = 300  # Sensitivity (Lower = more sensitive)
    r.dynamic_energy_threshold = True

    # Priority list for mics
    candidate_indices = [1, 2, 0, None]

    for index in candidate_indices:
        try:
            with sr.Microphone(device_index=index) as source:
                print(f"\n   🎤 Listening (Device {index})...")

                # Calibration (Short)
                r.adjust_for_ambient_noise(source, duration=0.5)

                frames = []
                silence_start_time = None
                has_speech_started = False
                max_recording_time = 15  # Safety timeout
                start_time = time.time()

                # --- THE MANUAL RECORDING LOOP ---
                while True:
                    # 1. CHECK FOR MANUAL STOP
                    if _stop_signal:
                        print("   🛑 Manual Stop Triggered.")
                        break

                    # 2. CHECK FOR MAX TIMEOUT
                    if (time.time() - start_time) > max_recording_time:
                        break

                    # 3. READ AUDIO CHUNK
                    # Read 4096 bytes (small chunk)
                    buffer = source.stream.read(4096)
                    if len(buffer) == 0: break
                    frames.append(buffer)

                    # 4. DETECT SILENCE (RMS Amplitude)
                    # We calculate how "loud" this chunk was
                    rms = audioop.rms(buffer, 2)  # width=2 for 16-bit audio

                    if rms > r.energy_threshold:
                        has_speech_started = True
                        silence_start_time = None  # Reset silence timer
                    else:
                        if has_speech_started:
                            if silence_start_time is None:
                                silence_start_time = time.time()
                            # If silent for > 1.2 seconds, stop automatically
                            elif (time.time() - silence_start_time) > 1.2:
                                print("   🤫 Auto-Stop (Silence).")
                                break

                # --- PROCESS AUDIO ---
                print("   ⏳ Processing...")
                if not frames: return ""

                raw_data = b"".join(frames)
                audio_data = sr.AudioData(raw_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)

                try:
                    text = r.recognize_google(audio_data)
                    print(f"   🗣️  You said: '{text}'")
                    return text
                except sr.UnknownValueError:
                    return ""
                except sr.RequestError:
                    return ""

        except OSError:
            continue  # Try next mic
        except Exception as e:
            print(f"Error: {e}")
            continue

    return ""