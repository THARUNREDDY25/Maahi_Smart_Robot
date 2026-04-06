"""
Obstacle Detection Module - Front HC-SR04 sensor only
GPIO 19 (TRIG) and GPIO 16 (ECHO)
"""
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logger.warning("RPi.GPIO not available - simulation mode")

from config import (
    SENSOR_FRONT_TRIG,
    SENSOR_FRONT_ECHO,
    OBSTACLE_DISTANCE_THRESHOLD
)


class ObstacleDetection:

    def __init__(self):
        if GPIO_AVAILABLE:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                GPIO.setup(SENSOR_FRONT_TRIG, GPIO.OUT)
                GPIO.setup(SENSOR_FRONT_ECHO, GPIO.IN)
                GPIO.output(SENSOR_FRONT_TRIG, GPIO.LOW)
                time.sleep(0.5)
                logger.info("Front ultrasonic sensor initialized")
            except Exception as e:
                logger.error(f"Sensor init failed: {e}")
        else:
            logger.info("Simulation mode - no GPIO")

    def get_front_distance(self):
        """Get distance in cm from front sensor"""
        if not GPIO_AVAILABLE:
            return 100.0

        try:
            GPIO.output(SENSOR_FRONT_TRIG, GPIO.HIGH)
            time.sleep(0.00001)
            GPIO.output(SENSOR_FRONT_TRIG, GPIO.LOW)

            timeout    = time.time() + 0.1
            pulse_start = time.time()
            while GPIO.input(SENSOR_FRONT_ECHO) == 0:
                pulse_start = time.time()
                if time.time() > timeout:
                    return 999.0

            timeout   = time.time() + 0.1
            pulse_end = time.time()
            while GPIO.input(SENSOR_FRONT_ECHO) == 1:
                pulse_end = time.time()
                if time.time() > timeout:
                    return 999.0

            duration = pulse_end - pulse_start
            distance = round(duration * 17150, 2)
            return distance

        except Exception as e:
            logger.error(f"Distance error: {e}")
            return 999.0

    def get_distance(self):
        return self.get_front_distance()

    def is_front_blocked(self):
        dist = self.get_front_distance()
        if dist < OBSTACLE_DISTANCE_THRESHOLD:
            logger.warning(f"Front obstacle at {dist}cm!")
            return True
        return False

    def cleanup(self):
        if GPIO_AVAILABLE:
            GPIO.cleanup()
        logger.info("Sensor cleanup done")


if __name__ == "__main__":
    print("Obstacle Detection Test - Front Sensor")
    print("=" * 50)
    sensor = ObstacleDetection()
    print("Reading for 10 seconds...")
    for i in range(10):
        dist    = sensor.get_front_distance()
        blocked = sensor.is_front_blocked()
        print(f"Front: {dist}cm  {'BLOCKED!' if blocked else 'clear'}")
        time.sleep(1)
    sensor.cleanup()
