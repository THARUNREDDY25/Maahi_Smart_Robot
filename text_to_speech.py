"""
Text-to-Speech Module for Maahi Robot Assistant
Uses gTTS for Indian female voice
Pipeline: gTTS -> mp3 -> wav -> aplay hw:0,0
"""
import logging
import os
from config import SPEAKER_VOLUME, TEMP_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SPEAKER = "hw:0,0"


class TextToSpeech:

    def __init__(self):
        self.engine    = None
        self.use_gtts  = False
        try:
            from gtts import gTTS
            self.use_gtts = True
            logger.info("Using gTTS Indian female voice")
        except ImportError:
            logger.warning("gTTS not found, using espeak fallback")

    def speak(self, text):
        if not text:
            return
        logger.info(f"Speaking: {text}")
        if self.use_gtts:
            self._speak_gtts(text)
        else:
            self._speak_espeak(text)

    def _speak_gtts(self, text):
        try:
            from gtts import gTTS
            mp3_file = "/tmp/maahi_tts.mp3"
            wav_file = "/tmp/maahi_tts.wav"
            tts = gTTS(text=text, lang="en", tld="co.in", slow=False)
            tts.save(mp3_file)
            os.system(f"mpg123 --wav {wav_file} {mp3_file} 2>/dev/null")
            os.system(f"aplay -D {SPEAKER} -q {wav_file} 2>/dev/null")
        except Exception as e:
            logger.error(f"gTTS failed: {e}")
            self._speak_espeak(text)

    def _speak_espeak(self, text):
        try:
            os.system(
                f'espeak -v en-in+f3 -s 120 -p 60 --stdout "{text}" '
                f'| aplay -D {SPEAKER} -q 2>/dev/null'
            )
        except Exception as e:
            logger.error(f"espeak failed: {e}")

    def set_rate(self, rate):
        pass

    def set_volume(self, volume):
        pass

    def speak_with_emotion(self, text, emotion="neutral"):
        self.speak(text)

    def speak_to_file(self, text, filename):
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang="en", tld="co.in")
            tts.save(f"{TEMP_DIR}/{filename}")
        except Exception as e:
            logger.error(f"speak_to_file failed: {e}")


if __name__ == "__main__":
    tts = TextToSpeech()
    print("Testing TTS...")
    tts.speak("Hello! I am Maahi your intelligent robot assistant.")
    print("Done!")
