"""
MAAHI Robot Assistant - Complete Main File
All modules integrated with all fixes applied:
- USB Mic index = 1
- Speaker hw:0,0
- Groq AI llama-3.3-70b-versatile
- gTTS Indian female voice
- Music player (YouTube + MPV)
- Motor control (L298N)
- Front obstacle detection (HC-SR04)
- SPI Display eyes (ILI9486 480x320)
- Wake word activation
- Auto-starts on boot via systemd
"""

# ── Must be first — suppress all ALSA/Jack noise ──
import os
import sys
import ctypes
import warnings

os.environ["JACK_NO_AUDIO_RESERVATION"] = "1"
os.environ["PYTHONWARNINGS"] = "ignore"
warnings.filterwarnings("ignore")

try:
    asound = ctypes.cdll.LoadLibrary('libasound.so.2')
    _EHF   = ctypes.CFUNCTYPE(
        None, ctypes.c_char_p, ctypes.c_int,
        ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p
    )
    def _eh(filename, line, function, err, fmt):
        pass
    asound.snd_lib_error_set_handler(_EHF(_eh))
except Exception:
    pass

# ── Hardcoded hardware constants ──
USB_MIC_INDEX   = 1        # USB PnP Sound Device (hw:1,0)
SPEAKER_DEVICE  = "hw:0,0" # bcm2835 Headphones 3.5mm jack

import threading
import time
import logging

logging.basicConfig(level=logging.INFO,
                    format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

import speech_recognition as sr

# ── Import all robot modules ──
try:
    from groq_assistant    import GroqAssistant
    from text_to_speech    import TextToSpeech
    from music_player      import MusicPlayer
    from motor_control     import (MotorControl,
                                   handle_voice_motor_command,
                                   parse_duration)
    from obstacle_detection import ObstacleDetection
    from display_eyes      import DisplayEyes
except Exception as e:
    print(f"[IMPORT ERROR] {e}")
    sys.exit(1)

# ══════════════════════════════════════
# INITIALIZE ALL MODULES
# ══════════════════════════════════════

print("=" * 50)
print("  MAAHI Robot Assistant Starting...")
print("=" * 50)

print("[1/6] Display...")
display = DisplayEyes()
display.show_startup()

print("[2/6] Motors...")
motor = MotorControl()
motor.set_speed(60)

print("[3/6] Sensors...")
sensor = ObstacleDetection()

print("[4/6] Groq AI...")
assistant = GroqAssistant()

print("[5/6] TTS...")
tts = TextToSpeech()

print("[6/6] Music...")
player = MusicPlayer()

print("All modules loaded!\n")

# ── Speech recognizer settings ──
recognizer = sr.Recognizer()
recognizer.energy_threshold        = 300
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold         = 0.8
recognizer.phrase_threshold        = 0.3
recognizer.non_speaking_duration   = 0.5

# ── Voice command keywords ──
WAKE_WORDS = [
    "hello maahi", "hey maahi", "hi maahi",
    "maahi", "hello mahi", "hey mahi", "hi mahi"
]
EXIT_WORDS = [
    "bye", "goodbye", "exit", "quit",
    "shutdown", "turn off", "shutdown mahi",
    "shutdown maahi", "band karo mahi"
]
SLEEP_WORDS = [
    "sleep", "go to sleep", "so ja", "soja"
]
MUSIC_STOP_WORDS = [
    "stop music", "stop song", "stop playing",
    "pause music", "band karo", "music stop",
    "music band"
]
MUSIC_PLAY_WORDS = [
    "play", "gana", "bajao", "sunao",
    "song", "gaana", "music"
]
MOVE_WORDS = [
    "forward", "backward", "left", "right",
    "move", "go", "turn", "aage", "peeche",
    "baaye", "daaye", "chal", "chalo"
]
STOP_MOVE = [
    "stop", "ruko", "halt", "brake", "rukja"
]


# ══════════════════════════════════════
# MICROPHONE HELPERS
# ══════════════════════════════════════

def _open_mic():
    """Safely open USB microphone — returns source or None"""
    try:
        source = sr.Microphone(device_index=USB_MIC_INDEX).__enter__()
        return source
    except Exception as e:
        logger.error(f"Mic open failed: {e}")
        return None


def listen_for_wake_word():
    """
    Silent loop — returns True only when wake word detected.
    Never raises — all exceptions caught internally.
    """
    try:
        with sr.Microphone(device_index=USB_MIC_INDEX) as source:
            try:
                recognizer.adjust_for_ambient_noise(source, duration=0.2)
            except Exception:
                pass
            try:
                audio = recognizer.listen(
                    source, timeout=8, phrase_time_limit=5
                )
                text = recognizer.recognize_google(
                    audio, language="en-IN"
                ).lower()
                print(f"[Sleep heard]: {text}")

                # Shutdown while sleeping
                if any(w in text for w in EXIT_WORDS):
                    tts.speak("Shutting down. Goodbye!")
                    shutdown_robot()

                if any(w in text for w in WAKE_WORDS):
                    return True

            except sr.WaitTimeoutError:
                return False
            except sr.UnknownValueError:
                return False
            except Exception:
                return False

    except Exception as e:
        logger.warning(f"Mic error: {e}")
        time.sleep(1)

    return False


def listen_for_command():
    """
    Listen for one command after wake word.
    Returns text string or None.
    Keeps listening in a short loop so user has time to speak.
    """
    display.show_state("listening")
    print("Listening for command...")

    # Try up to 3 times to get a clear command
    for attempt in range(3):
        try:
            with sr.Microphone(device_index=USB_MIC_INDEX) as source:
                try:
                    recognizer.adjust_for_ambient_noise(source, duration=0.3)
                except Exception:
                    pass
                try:
                    audio = recognizer.listen(
                        source, timeout=8, phrase_time_limit=12
                    )
                    text = recognizer.recognize_google(
                        audio, language="en-IN"
                    ).lower()
                    print(f"Command [{attempt+1}]: {text}")
                    if text.strip():
                        return text.strip()
                except sr.WaitTimeoutError:
                    print(f"[Attempt {attempt+1}] Timeout — no speech")
                    if attempt < 2:
                        tts.speak("I did not hear you. Please say your command.")
                    return None
                except sr.UnknownValueError:
                    print(f"[Attempt {attempt+1}] Could not understand")
                    if attempt < 2:
                        continue
                    return None
                except Exception as e:
                    logger.error(f"STT error: {e}")
                    return None

        except Exception as e:
            logger.error(f"Mic open error: {e}")
            time.sleep(0.5)

    return None


# ══════════════════════════════════════
# COMMAND PROCESSING HELPERS
# ══════════════════════════════════════

def extract_song_name(command):
    """Strip play/music keywords to get song name"""
    remove = [
        "play the song", "play song", "play the music",
        "play music", "play me", "please play", "can you play",
        "i want to hear", "i want to listen to", "put on",
        "start playing", "gana bajao", "gaana bajao",
        "bajao", "sunao", "gana sunao", "play",
        "song", "music", "gaana", "gana"
    ]
    s = command.lower()
    for phrase in sorted(remove, key=len, reverse=True):
        s = s.replace(phrase, "")
    return s.strip() or None


def play_music_command(song_name):
    """Search and play song — returns True if started"""
    display.show_state("thinking")
    tts.speak(f"Searching for {song_name}. Please wait.")
    songs = player.search_songs(song_name, limit=1)
    if songs:
        song = songs[0]
        tts.speak(f"Playing {song['title']} by {song['artist']}")
        player.play_song_by_video_id(
            song["video_id"], song["title"], song["artist"]
        )
        display.show_song_info(song["title"], song["artist"])
        return True
    else:
        display.show_state("normal")
        tts.speak(f"Sorry, I could not find {song_name}. Please try again.")
        return False


def shutdown_robot():
    """Clean shutdown of all hardware"""
    print("\nShutting down MAAHI...")
    try:
        display.show_state("sleeping")
        display.stop_blink_loop()
        player.stop_playback()
        motor.stop()
        motor.cleanup()
        sensor.cleanup()
        display.clear()
    except Exception:
        pass
    print("Goodbye!")
    os._exit(0)


# ══════════════════════════════════════
# MAIN COMMAND HANDLER
# ══════════════════════════════════════

def handle_command(command):
    """
    Process voice command and act.
    Returns: 'music' | 'sleep' | 'continue'
    """
    display.show_state("thinking")
    command = command.lower().strip()
    print(f"Processing: '{command}'")

    # ── 1. Shutdown ──
    if any(w in command for w in EXIT_WORDS):
        tts.speak("Shutting down. Goodbye! See you soon.")
        shutdown_robot()

    # ── 2. Sleep ──
    if any(w in command for w in SLEEP_WORDS):
        tts.speak("Going to sleep. Say Hey Maahi to wake me up.")
        display.show_state("sleeping")
        return "sleep"

    # ── 3. Stop music ──
    if any(w in command for w in MUSIC_STOP_WORDS):
        player.stop_playback()
        display.show_state("normal")
        tts.speak("Music stopped.")
        return "continue"

    # ── 4. Play music ──
    if any(w in command for w in MUSIC_PLAY_WORDS):
        # Make sure it's not a movement command
        if not any(w in command for w in MOVE_WORDS + STOP_MOVE):
            song_name = extract_song_name(command)
            if song_name and len(song_name) > 1:
                success = play_music_command(song_name)
                return "music" if success else "continue"
            else:
                display.show_state("listening")
                tts.speak("Which song would you like to play?")
                song_input = listen_for_command()
                if song_input:
                    success = play_music_command(song_input)
                    return "music" if success else "continue"
                return "continue"

    # ── 5. Stop motor ──
    if any(w in command for w in STOP_MOVE):
        motor.stop()
        display.show_state("normal")
        tts.speak("Stopped.")
        return "continue"

    # ── 6. Motor movement ──
    if any(w in command for w in MOVE_WORDS):
        is_motor = handle_voice_motor_command(command, motor)
        if is_motor:
            status    = motor.get_status()
            direction = status["direction"]
            if direction != "stopped":
                d        = parse_duration(command)
                dur_text = f" for {int(d)} seconds" if d else " until you say stop"

                # Obstacle check for forward
                if direction == "forward" and sensor.is_front_blocked():
                    display.show_state("obstacle")
                    tts.speak("Obstacle ahead! Cannot move forward.")
                    motor.stop()
                    time.sleep(1.5)
                    display.show_state("normal")
                    return "continue"

                display.show_state(direction)
                tts.speak(f"Moving {direction}{dur_text}.")
            else:
                display.show_state("normal")
                tts.speak("Stopped.")
            return "continue"

    # ── 7. General AI question ──
    print("Sending to Groq AI...")
    display.show_state("thinking")
    response = assistant.get_response(command)
    print(f"Maahi: {response}")
    display.show_response(response)
    display.show_state("answering")
    tts.speak(response)
    display.show_state("normal")
    return "continue"


# ══════════════════════════════════════
# MUSIC MODE
# ══════════════════════════════════════

def music_mode():
    """
    Music playing silently in background.
    Only responds to 'Hey Maahi + command'.
    Returns: 'next_task' | 'sleep'
    """
    print("\n[Music Mode] Playing... Say 'Hey Maahi stop' to stop")

    while True:
        # Song ended naturally
        if not player.is_song_playing():
            print("[Music] Song finished")
            display.show_state("normal")
            tts.speak("Song finished. What would you like next?")
            return "next_task"

        # Silent listen for wake word
        try:
            with sr.Microphone(device_index=USB_MIC_INDEX) as source:
                try:
                    recognizer.adjust_for_ambient_noise(source, duration=0.2)
                except Exception:
                    pass
                try:
                    audio = recognizer.listen(
                        source, timeout=5, phrase_time_limit=6
                    )
                    text = recognizer.recognize_google(
                        audio, language="en-IN"
                    ).lower()
                    print(f"[Music heard]: {text}")

                    has_wake  = any(w in text for w in WAKE_WORDS)
                    has_stop  = any(w in text for w in MUSIC_STOP_WORDS + ["stop"])
                    has_exit  = any(w in text for w in EXIT_WORDS)
                    has_sleep = any(w in text for w in SLEEP_WORDS)
                    has_play  = any(w in text for w in MUSIC_PLAY_WORDS)

                    if has_wake and has_exit:
                        player.stop_playback()
                        tts.speak("Goodbye! Shutting down.")
                        shutdown_robot()

                    if has_wake and has_sleep:
                        player.stop_playback()
                        tts.speak("Going to sleep.")
                        display.show_state("sleeping")
                        return "sleep"

                    if has_wake and has_stop:
                        player.stop_playback()
                        display.show_state("normal")
                        tts.speak("Music stopped. What would you like next?")
                        return "next_task"

                    if has_wake:
                        display.show_state("listening")
                        tts.speak("Yes?")
                        cmd = listen_for_command()
                        if cmd:
                            if any(w in cmd for w in MUSIC_STOP_WORDS + ["stop"]):
                                player.stop_playback()
                                display.show_state("normal")
                                tts.speak("Music stopped. What would you like next?")
                                return "next_task"
                            elif any(w in cmd for w in EXIT_WORDS):
                                player.stop_playback()
                                tts.speak("Goodbye!")
                                shutdown_robot()
                            elif any(w in cmd for w in SLEEP_WORDS):
                                player.stop_playback()
                                tts.speak("Going to sleep.")
                                display.show_state("sleeping")
                                return "sleep"
                            elif any(w in cmd for w in MUSIC_PLAY_WORDS):
                                # Play new song
                                player.stop_playback()
                                song_name = extract_song_name(cmd)
                                if song_name:
                                    success = play_music_command(song_name)
                                    if not success:
                                        return "next_task"
                                    # Continue music mode with new song
                                else:
                                    return "next_task"
                            else:
                                result = handle_command(cmd)
                                if result == "music":
                                    pass
                                # Restore music display
                                if player.is_song_playing():
                                    display.show_song_info(
                                        player.current_song  or "Unknown",
                                        player.current_artist or "Unknown"
                                    )

                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"Music mode mic error: {e}")
            time.sleep(0.5)


# ══════════════════════════════════════
# NEXT TASK MODE (after music stops)
# ══════════════════════════════════════

def next_task_mode():
    """After music stops — listen for next command then sleep"""
    display.show_state("listening")
    command = listen_for_command()
    if command:
        result = handle_command(command)
        if result == "music":
            return "music"
        if result == "sleep":
            return "sleep"
    display.show_state("sleeping")
    return "sleep"


# ══════════════════════════════════════
# BACKGROUND OBSTACLE MONITOR
# ══════════════════════════════════════

def obstacle_monitor():
    """Auto-stop robot if obstacle while moving forward"""
    while True:
        try:
            if motor.is_moving and motor.current_direction == "forward":
                if sensor.is_front_blocked():
                    print("[Obstacle Monitor] Auto-stop!")
                    motor.stop()
                    display.show_state("obstacle")
                    tts.speak("Obstacle detected! Stopping.")
                    time.sleep(2)
                    display.show_state("normal")
        except Exception:
            pass
        time.sleep(0.4)


# ══════════════════════════════════════
# STARTUP
# ══════════════════════════════════════

# Fix framebuffer permissions
os.system("sudo chmod 666 /dev/fb1 2>/dev/null")

# Start animation
display.start_blink_loop()

# Start obstacle monitor
threading.Thread(target=obstacle_monitor, daemon=True).start()

# Greet user
tts.speak("Hello! Mahi is online and ready. Say Hey Maahi to wake me up.")
display.show_state("sleeping")

print("\n" + "=" * 50)
print("  MAAHI is ready!")
print("  Say 'Hey Maahi' to wake up")
print("  Say 'Hey Maahi play [song]' for music")
print("  Say 'Hey Maahi move forward' to move")
print("  Say 'Hey Maahi stop' to stop")
print("  Say 'sleep' to sleep, 'shutdown Mahi' to quit")
print("  Ctrl+C to force quit")
print("=" * 50 + "\n")


# ══════════════════════════════════════
# MAIN LOOP
# ══════════════════════════════════════

try:
    mode = "sleep"

    while True:

        # ── SLEEP MODE — silent, waiting for wake word ──
        if mode == "sleep":
            display.show_state("sleeping")
            wake = listen_for_wake_word()

            if wake:
                print("\n[Wake word detected!]")
                display.show_state("listening")
                tts.speak("Yes, how can I help?")

                command = listen_for_command()

                if command:
                    result = handle_command(command)
                    if result == "music":
                        mode = "music"
                    elif result == "sleep":
                        mode = "sleep"
                    else:
                        # After answering go back to sleep
                        mode = "sleep"
                        display.show_state("sleeping")
                        print("Sleeping... Say 'Hey Maahi' to wake up")
                else:
                    # No command heard — go back to sleep silently
                    mode = "sleep"
                    display.show_state("sleeping")

        # ── MUSIC MODE — playing music ──
        elif mode == "music":
            result = music_mode()
            if result == "next_task":
                mode = "next_task"
            else:
                mode = "sleep"
                display.show_state("sleeping")
                print("Sleeping...")

        # ── NEXT TASK MODE — after song ends ──
        elif mode == "next_task":
            result = next_task_mode()
            if result == "music":
                mode = "music"
            else:
                mode = "sleep"
                display.show_state("sleeping")
                print("Sleeping...")

except KeyboardInterrupt:
    print("\n[Ctrl+C] Shutting down...")
    tts.speak("Shutting down. Goodbye!")
    shutdown_robot()
