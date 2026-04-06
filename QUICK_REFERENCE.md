# MAAHI ROBOT - QUICK REFERENCE GUIDE

## ⚡ QUICK START (5 Minutes)

```bash
# 1. Navigate to project
cd ~/Desktop/Robot/Maahi

# 2. Activate virtual environment
source maahi_env/bin/activate

# 3. Edit config.py with your API key
nano config.py
# Change: GROQ_API_KEY = "your_actual_key_here"

# 4. Run robot
python3 maahi_main.py

# 5. Say "Hello Maahi" to wake up
# Say "Play Kesariya" to play music
# Say "Move forward" to move
# Say "Shutdown Maahi" to turn off
```

---

## 📦 ALL PACKAGES TO INSTALL

### System Level (Raspberry Pi OS)
```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y \
    python3 python3-pip python3-dev \
    libasound2-dev portaudio19-dev \
    mpv espeak alsa-utils pulseaudio mpg123 \
    libatlas-base-dev libjasper-dev libtiff5 \
    libjasper1 libharfbuzz0b libwebp6
```

### Python Packages (From requirements.txt)
```bash
pip install -r requirements.txt
```

**Core Packages**:
- `groq==0.9.0` - Groq AI API
- `SpeechRecognition==3.10.0` - Google STT
- `PyAudio==0.2.13` - Microphone input
- `gtts==2.3.2` - Google Text-to-Speech
- `ytmusicapi==4.2.10` - YouTube Music API
- `mpv==1.0.5` - Music player
- `RPi.GPIO==0.7.0` - GPIO control
- `Pillow==10.1.0` - Image processing
- `numpy==1.24.3` - Numerical computing
- `Flask==3.0.0` - Web server (optional)

---

## 🎤 VOICE COMMANDS REFERENCE

### Wake Words
```
hello maahi | hey maahi | hi maahi | maahi
hello mahi | hey mahi | hi mahi | mahi
```

### Music Commands
```
play [song_name/artist] - Play specific song
play bollywood hits - Play genre/mood
play sad songs - Play by mood
play workout music - Play by activity
stop music - Stop playback
pause music - Pause playback
```

### Movement Commands
```
move forward - Drive forward continuously
move forward 5 seconds - Drive forward for 5 seconds
move backward - Drive backward
turn left - Turn left
turn right - Turn right
stop - Stop all motors
```

### Control Commands
```
sleep | go to sleep | so ja - Enter sleep mode
shutdown maahi | bye | goodbye - Shutdown robot
band karo mahi - Stop (Hindi)
```

### AI Questions
```
what time is it?
tell me a joke
what's the weather?
calculate 2+2
play music - AI asks which song
```

---

## 🔧 HARDWARE PIN CONFIGURATION

**Motor Driver (L298N)**:
- GPIO 0 (Pin 27): Left Forward
- GPIO 1 (Pin 28): Left Backward  
- GPIO 5 (Pin 29): Right Forward
- GPIO 6 (Pin 31): Right Backward
- GPIO 12 (Pin 32): Left Speed (PWM)
- GPIO 13 (Pin 33): Right Speed (PWM) ⭐ FIXED!

**Ultrasonic Sensor (HC-SR04)**:
- GPIO 19 (Pin 35): Trigger
- GPIO 16 (Pin 36): Echo

**Display (ILI9486)**:
- SPI: CE0, MOSI, MISO, CLK
- Framebuffer: /dev/fb1

**Audio**:
- Microphone: Device index 1 (USB)
- Speaker: hw:0,0 (3.5mm jack)

---

## 📝 FILE STRUCTURE

```
Maahi/
├── maahi_main.py              # Main program ⭐ START HERE
├── config.py                  # Configuration (⚠️ Update API key)
├── groq_assistant.py          # AI integration
├── motor_control.py           # Motor control
├── music_player.py            # YouTube Music
├── text_to_speech.py          # TTS (gTTS + espeak)
├── obstacle_detection.py      # HC-SR04 sensor
├── display_eyes.py            # ILI9486 display
├── requirements.txt           # ✅ Python packages
├── SETUP_GUIDE.md             # ✅ 11-step installation
├── ISSUES_AND_FIXES.md        # ✅ Detailed bug report
└── QUICK_REFERENCE.md         # This file
```

---

## 🧪 TESTING EACH MODULE

### Test TTS (Text-to-Speech)
```bash
python3 << 'EOF'
from text_to_speech import TextToSpeech
tts = TextToSpeech()
tts.speak("Hello! I am Maahi. Testing text to speech.")
EOF
# Expected: Robot speaks the text
```

### Test Music Player
```bash
python3 music_player.py
# Expected: Searches and plays "Kesariya Arijit Singh"
```

### Test Motor Control
```bash
python3 motor_control.py
# Expected: Motors move sequentially
```

### Test Obstacle Detection
```bash
python3 obstacle_detection.py
# Expected: Prints distance readings for 10 seconds
```

### Test Groq AI
```bash
python3 << 'EOF'
from groq_assistant import GroqAssistant
ai = GroqAssistant()
response = ai.get_simple_response("What is 2+2?")
print(f"Groq AI: {response}")
EOF
# Expected: Gets response from Groq
```

### Test Display Eyes
```bash
python3 display_eyes.py
# Expected: Shows animated eyes on screen
```

### Test Microphone Detection
```bash
python3 << 'EOF'
import speech_recognition as sr
print("Available microphones:")
for i, name in enumerate(sr.Microphone.list_working_microphones()):
    print(f"  Device {i}: {name}")
EOF
```

### Full Robot Test
```bash
python3 maahi_main.py
# Expected: All 6 modules load, robot goes to sleep mode
# Say: "Hello Maahi"
```

---

## 🔧 COMMON TROUBLESHOOTING COMMANDS

### Check System Audio
```bash
aplay -l                    # List playback devices
arecord -l                  # List recording devices (mics)
alsamixer                   # Audio mixer GUI
amixer set Master 80%       # Set volume to 80%
```

### Check Microphone
```bash
arecord -d 5 test.wav       # Record 5 seconds
aplay test.wav              # Play back
```

### Check Speaker
```bash
speaker-test -t sine -f 1000 -l 1
```

### Check GPIO
```bash
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); print('OK')"
```

### Check Groq API
```bash
export GROQ_API_KEY="your_key_here"
python3 << 'EOF'
from groq import Groq
c = Groq()
m = c.chat.completions.create(
    messages=[{"role": "user", "content": "hi"}],
    model="llama-3.3-70b-versatile"
)
print(m.choices[0].message.content)
EOF
```

### Reset USB Audio
```bash
sudo systemctl restart alsa-utils
sudo systemctl restart pulseaudio
```

### Check Serial/Device Permissions
```bash
ls -la /dev/ttyUSB*         # Check USB serial
ls -la /dev/fb1             # Check framebuffer
ls -la /dev/gpio*           # Check GPIO
```

### View System Logs
```bash
sudo journalctl -u maahi -f # If using systemd service
tail -f /var/log/syslog     # System log
```

---

## 📊 PERFORMANCE SETTINGS

### In config.py

**Faster Responses** (Lower latency):
```python
GROQ_TEMPERATURE = 0.5        # (was 0.7) More focused
LISTEN_TIMEOUT = 6            # (was 8) Faster timeout
```

**Smoother Movement**:
```python
MOTOR_SPEED = 80              # (was 60) Faster motors
```

**Better Voice Recognition**:
```python
AUDIO_RATE = 48000            # (was 16000) Better quality
```

**Faster Display** (More CPU usage):
```python
# In display_eyes.py line 578:
time.sleep(0.03)              # (was 0.045) ~33 fps instead of 22 fps
```

---

## 🚀 DEPLOYMENT OPTIONS

### Option 1: Manual Run
```bash
source maahi_env/bin/activate
python3 maahi_main.py
```

### Option 2: Systemd Service (Auto-start on boot)
```bash
sudo nano /etc/systemd/system/maahi.service
# Copy service file from SETUP_GUIDE.md
sudo systemctl enable maahi
sudo systemctl start maahi
```

### Option 3: Using Screen (Keep running in background)
```bash
source maahi_env/bin/activate
screen -S maahi
python3 maahi_main.py
# Press Ctrl+A then D to detach
# screen -r maahi to reattach
```

### Option 4: Using Nohup (Immune to logout)
```bash
nohup python3 maahi_main.py > maahi.log 2>&1 &
# Check status: ps aux | grep maahi
# Kill: pkill -f maahi_main.py
```

---

## 🔐 SECURITY CONSIDERATIONS

### Groq API Key
- ✅ Store in config.py (local file)
- ❌ Don't push to GitHub
- ❌ Don't hardcode in code

### Better Practice (Using .env):
```bash
# 1. Create .env file
echo "GROQ_API_KEY=your_key_here" > .env

# 2. Update config.py to load it:
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 3. Add .env to .gitignore
echo ".env" >> .gitignore
```

### YouTube Music Auth
- Auth token stored at: `~/.config/ytmusicapi/headers_auth.json`
- Keep this directory private
- Don't share this file

### GPIO Access
- Requires `sudo` or gpio group membership
- Add user to gpio group:
```bash
sudo usermod -a -G gpio pi
newgrp gpio
```

---

## 📞 GETTING HELP

### Official Resources
- Groq API: https://console.groq.com/docs
- ytmusicapi: https://github.com/sigma67/ytmusicapi
- Speech Recognition: https://github.com/Uberi/speech_recognition
- Raspberry Pi GPIO: https://github.com/RPi-Distro/python-rpi.gpio
- Pillow (Image): https://python-pillow.org

### Common Issues

**"ModuleNotFoundError: No module named 'groq'"**
```bash
pip install groq
```

**"No module named 'RPi.GPIO'"**
```bash
pip install RPi.GPIO
```

**"Microphone not found"**
```bash
python3 -m speech_recognition  # Check installed
arecord -l                      # Check hardware
```

**"API key invalid"**
```bash
curl -H "Authorization: Bearer YOUR_KEY" \
  https://api.groq.com/openai/v1/models
```

**"YouTube Music search fails"**
```bash
python3 -c "from ytmusicapi import YTMusic; YTMusic.setup()"
```

---

## 📈 NEXT STEPS FOR IMPROVEMENT

1. **Add Web Interface**: Flask API to control robot remotely
2. **Add Logging**: Store voice commands and responses
3. **Add Offline Mode**: Work without internet (local LLM)
4. **Add Multiple Sensors**: Rear obstacle detection, IR sensors
5. **Add Navigation**: Map building and pathfinding
6. **Add Computer Vision**: Camera for lane detection
7. **Add Scheduled Tasks**: Automatic watering, cleaning
8. **Add MQTT**: Integration with smart home systems

---

**Quick Reference Version**: 1.0  
**Last Updated**: April 6, 2026  
**Status**: Ready to Deploy ✅
