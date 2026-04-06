"""
Configuration file for Maahi Robot Assistant
All settings and constants defined here
"""
import os

# ==================== ROBOT SETTINGS ====================
ROBOT_NAME  = "Mahi"
WAKE_WORD   = "hello mahi"
CLOSE_WORD  = "bye"

# ==================== GROQ API SETTINGS ====================
GROQ_API_KEY    = "Your_API_KEY"
GROQ_MODEL      = "llama-3.3-70b-versatile"
GROQ_TEMPERATURE = 0.7

# ==================== VOICE / MIC SETTINGS ====================
USB_MIC_INDEX  = 1        # USB PnP Sound Device
VOICE_LANGUAGE = "en-IN"
LISTEN_TIMEOUT = 8
AUDIO_RATE     = 16000
AUDIO_CHUNK    = 1024
AUDIO_CHANNELS = 1

# ==================== AUDIO OUTPUT SETTINGS ====================
AUDIO_OUTPUT_DEVICE = "hw:0,0"   # bcm2835 Headphones 3.5mm jack
SPEAKER_VOLUME      = 80

# ==================== MOTOR SETTINGS ====================
# Pins 1-26 used by SPI screen — motors use pins 27-40
MOTOR_LEFT_FORWARD   = 0    # GPIO 0  - Physical Pin 27
MOTOR_LEFT_BACKWARD  = 1    # GPIO 1  - Physical Pin 28
MOTOR_RIGHT_FORWARD  = 5    # GPIO 5  - Physical Pin 29
MOTOR_RIGHT_BACKWARD = 6    # GPIO 6  - Physical Pin 31
MOTOR_ENA_PIN        = 12   # GPIO 12 - Physical Pin 32
MOTOR_ENB_PIN        = 13   # GPIO 13 - Physical Pin 33 (FIXED: Different pin for independent control)
MOTOR_SPEED          = 60

# ==================== ULTRASONIC SENSOR SETTINGS ====================
SENSOR_FRONT_TRIG           = 19   # GPIO 19 - Physical Pin 35
SENSOR_FRONT_ECHO           = 16   # GPIO 16 - Physical Pin 36
OBSTACLE_DISTANCE_THRESHOLD = 20   # Stop if obstacle within 20cm
CHECK_OBSTACLE_INTERVAL     = 1

# ==================== DISPLAY SETTINGS ====================
DISPLAY_WIDTH  = 480
DISPLAY_HEIGHT = 320
FRAMEBUFFER    = "/dev/fb1"

# ==================== YOUTUBE / MUSIC SETTINGS ====================
SEARCH_RESULTS_LIMIT = 5

# ==================== WEB INTERFACE SETTINGS ====================
FLASK_HOST  = "0.0.0.0"
FLASK_PORT  = 5000
FLASK_DEBUG = False

# ==================== STATE CONSTANTS ====================
STATE_IDLE          = "idle"
STATE_LISTENING     = "listening"
STATE_PROCESSING    = "processing"
STATE_SPEAKING      = "speaking"
STATE_MOVING        = "moving"
STATE_PLAYING_MUSIC = "playing_music"
STATE_SLEEPING      = "sleeping"

# ==================== PATHS ====================
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR        = os.path.join(BASE_DIR, "logs")
TEMP_DIR        = os.path.join(BASE_DIR, "temp")
EYES_ASSETS_DIR = os.path.join(BASE_DIR, "assets", "eyes")

os.makedirs(LOGS_DIR,        exist_ok=True)
os.makedirs(TEMP_DIR,        exist_ok=True)
os.makedirs(EYES_ASSETS_DIR, exist_ok=True)
