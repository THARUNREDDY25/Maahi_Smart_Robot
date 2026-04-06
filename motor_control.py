"""
Motor Control Module for Maahi Robot Assistant
L298N Motor Driver with 2 motors
GPIO pins 27-40 (pins 1-26 used by SPI screen)
"""
import time
import logging
import threading
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logger.warning("RPi.GPIO not available - simulation mode")

from config import (
    MOTOR_LEFT_FORWARD, MOTOR_LEFT_BACKWARD,
    MOTOR_RIGHT_FORWARD, MOTOR_RIGHT_BACKWARD,
    MOTOR_ENA_PIN, MOTOR_ENB_PIN, MOTOR_SPEED
)


class MotorControl:

    def __init__(self):
        self.is_moving        = False
        self.current_speed    = MOTOR_SPEED
        self.current_direction = "stopped"
        self.ena_pwm          = None
        self.enb_pwm          = None
        self._stop_event      = threading.Event()
        self._move_thread     = None

        if GPIO_AVAILABLE:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                pins = [
                    MOTOR_LEFT_FORWARD, MOTOR_LEFT_BACKWARD,
                    MOTOR_RIGHT_FORWARD, MOTOR_RIGHT_BACKWARD,
                    MOTOR_ENA_PIN, MOTOR_ENB_PIN
                ]
                for pin in pins:
                    GPIO.setup(pin, GPIO.OUT)
                    GPIO.output(pin, GPIO.LOW)
                self.ena_pwm = GPIO.PWM(MOTOR_ENA_PIN, 1000)
                self.enb_pwm = GPIO.PWM(MOTOR_ENB_PIN, 1000)
                self.ena_pwm.start(0)
                self.enb_pwm.start(0)
                logger.info("Motor Control initialized")
            except Exception as e:
                logger.error(f"GPIO init failed: {e}")
        else:
            logger.info("Simulation mode - no GPIO")

    def set_speed(self, speed):
        speed = max(0, min(100, speed))
        self.current_speed = speed
        if GPIO_AVAILABLE and self.ena_pwm and self.enb_pwm:
            self.ena_pwm.ChangeDutyCycle(speed)
            self.enb_pwm.ChangeDutyCycle(speed)
        logger.info(f"Speed: {speed}%")

    def _set_pins(self, lf, lb, rf, rb):
        if GPIO_AVAILABLE:
            GPIO.output(MOTOR_LEFT_FORWARD,   GPIO.HIGH if lf else GPIO.LOW)
            GPIO.output(MOTOR_LEFT_BACKWARD,  GPIO.HIGH if lb else GPIO.LOW)
            GPIO.output(MOTOR_RIGHT_FORWARD,  GPIO.HIGH if rf else GPIO.LOW)
            GPIO.output(MOTOR_RIGHT_BACKWARD, GPIO.HIGH if rb else GPIO.LOW)

    def _run_continuous(self, direction_func):
        self._stop_event.clear()
        self.is_moving = True
        direction_func()
        self.set_speed(self.current_speed)
        self._stop_event.wait()
        self._stop_pins()

    def _run_timed(self, direction_func, duration):
        self._stop_event.clear()
        self.is_moving = True
        direction_func()
        self.set_speed(self.current_speed)
        self._stop_event.wait(timeout=duration)
        self._stop_pins()

    def _stop_pins(self):
        if GPIO_AVAILABLE:
            GPIO.output(MOTOR_LEFT_FORWARD,   GPIO.LOW)
            GPIO.output(MOTOR_LEFT_BACKWARD,  GPIO.LOW)
            GPIO.output(MOTOR_RIGHT_FORWARD,  GPIO.LOW)
            GPIO.output(MOTOR_RIGHT_BACKWARD, GPIO.LOW)
            if self.ena_pwm:
                self.ena_pwm.ChangeDutyCycle(0)
            if self.enb_pwm:
                self.enb_pwm.ChangeDutyCycle(0)
        self.is_moving         = False
        self.current_direction = "stopped"

    def _dir_forward(self):
        self.current_direction = "forward"
        self._set_pins(1, 0, 1, 0)

    def _dir_backward(self):
        self.current_direction = "backward"
        self._set_pins(0, 1, 0, 1)

    def _dir_left(self):
        self.current_direction = "left"
        self._set_pins(0, 1, 1, 0)

    def _dir_right(self):
        self.current_direction = "right"
        self._set_pins(1, 0, 0, 1)

    def _start_move(self, direction_func, duration):
        self.stop()
        if duration:
            self._move_thread = threading.Thread(
                target=self._run_timed,
                args=(direction_func, duration),
                daemon=True
            )
        else:
            self._move_thread = threading.Thread(
                target=self._run_continuous,
                args=(direction_func,),
                daemon=True
            )
        self._move_thread.start()

    def move_forward(self, duration=None):
        logger.info(f"Forward {duration or 'continuous'}")
        self._start_move(self._dir_forward, duration)

    def move_backward(self, duration=None):
        logger.info(f"Backward {duration or 'continuous'}")
        self._start_move(self._dir_backward, duration)

    def turn_left(self, duration=None):
        logger.info(f"Left {duration or 'continuous'}")
        self._start_move(self._dir_left, duration)

    def turn_right(self, duration=None):
        logger.info(f"Right {duration or 'continuous'}")
        self._start_move(self._dir_right, duration)

    def stop(self):
        self._stop_event.set()
        if self._move_thread and self._move_thread.is_alive():
            self._move_thread.join(timeout=1)
        self._stop_pins()
        logger.info("Motors stopped")

    def get_status(self):
        return {
            "direction": self.current_direction,
            "speed":     self.current_speed,
            "is_moving": self.is_moving
        }

    def cleanup(self):
        self.stop()
        if GPIO_AVAILABLE:
            if self.ena_pwm:
                self.ena_pwm.stop()
            if self.enb_pwm:
                self.enb_pwm.stop()
            GPIO.cleanup()
        logger.info("GPIO cleaned up")


def parse_duration(command):
    patterns = [
        r'(\d+\.?\d*)\s*seconds?',
        r'(\d+\.?\d*)\s*secs?',
        r'(\d+\.?\d*)\s*s\b',
        r'for\s+(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*minute',
    ]
    for pattern in patterns:
        match = re.search(pattern, command)
        if match:
            val = float(match.group(1))
            if 'minute' in pattern:
                val *= 60
            return val
    return None


def parse_speed(command):
    match = re.search(r'(\d+)\s*(?:percent|%|speed)', command)
    if match:
        return int(match.group(1))
    if any(w in command for w in ['fast', 'quickly', 'tez']):
        return 80
    if any(w in command for w in ['slow', 'slowly', 'dheere']):
        return 30
    return None


def handle_voice_motor_command(command, motor):
    command = command.lower()

    FORWARD_WORDS  = ["forward", "aage", "straight", "seedha", "front"]
    BACKWARD_WORDS = ["backward", "back", "peeche", "reverse"]
    LEFT_WORDS     = ["left", "baaye"]
    RIGHT_WORDS    = ["right", "daaye"]
    STOP_WORDS     = ["stop", "ruko", "band karo", "halt", "brake", "rukja"]

    is_motor = any(w in command for w in
                   FORWARD_WORDS + BACKWARD_WORDS +
                   LEFT_WORDS + RIGHT_WORDS + STOP_WORDS +
                   ["move", "go", "turn", "chalo", "chal"])

    if not is_motor:
        return False

    if any(w in command for w in STOP_WORDS):
        motor.stop()
        return True

    duration = parse_duration(command)
    speed    = parse_speed(command)
    if speed:
        motor.set_speed(speed)

    if any(w in command for w in FORWARD_WORDS):
        motor.move_forward(duration)
    elif any(w in command for w in BACKWARD_WORDS):
        motor.move_backward(duration)
    elif any(w in command for w in LEFT_WORDS):
        motor.turn_left(duration)
    elif any(w in command for w in RIGHT_WORDS):
        motor.turn_right(duration)

    return True


if __name__ == "__main__":
    print("Motor Control Test")
    print("=" * 50)
    motor = MotorControl()
    motor.set_speed(60)

    print("Forward 2s...")
    motor.move_forward(2)
    time.sleep(3)

    print("Backward 2s...")
    motor.move_backward(2)
    time.sleep(3)

    print("Left 1.5s...")
    motor.turn_left(1.5)
    time.sleep(2)

    print("Right 1.5s...")
    motor.turn_right(1.5)
    time.sleep(2)

    motor.cleanup()
    print("Done!")
