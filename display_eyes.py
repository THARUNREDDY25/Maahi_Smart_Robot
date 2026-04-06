"""
Display Eyes Module for Maahi Robot Assistant
Cute animated eyes — cartoon style with eyelashes, blush, smile
ILI9486 SPI Display 480x320 via /dev/fb1 framebuffer
"""

import numpy as np
from PIL import Image, ImageDraw
import threading
import time
import math
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WIDTH  = 480
HEIGHT = 320
FB     = "/dev/fb1"

# ── Color Palette ──
SKY       = (135, 206, 235)   # Light sky blue background
NAVY      = (15,  20,  50)    # Dark navy for lines/lashes
WHITE     = (255, 255, 255)
BLACK     = (5,   5,   20)    # Near black for pupil
IRIS_BLUE = (30,  90,  200)   # Blue iris
IRIS_GRN  = (20,  160, 80)    # Green iris (listening)
IRIS_YLW  = (200, 160, 0)     # Yellow iris (answering)
IRIS_PRP  = (130, 40,  200)   # Purple iris (music)
IRIS_RED  = (200, 20,  20)    # Red iris (obstacle)
IRIS_ORG  = (210, 100, 0)     # Orange iris (moving)
BLUSH     = (240, 130, 150)   # Pink blush
HIGHLIGHT = (255, 255, 255)   # Eye highlight dot
SMILE_COL = (30,  40,  80)    # Smile line color


class DisplayEyes:

    def __init__(self):
        self.current_state  = "normal"
        self._anim_running  = False
        self._anim_thread   = None
        self._move_dir      = "forward"

        os.system("sudo chmod 666 /dev/fb1 2>/dev/null")

        try:
            with open(FB, 'wb') as f:
                pass
            self.fb_available = True
            logger.info("Framebuffer /dev/fb1 ready")
        except Exception as e:
            self.fb_available = False
            logger.warning(f"Framebuffer error: {e}")

    # ══════════════════════════════════════
    # CORE DRAWING
    # ══════════════════════════════════════

    def _write(self, img):
        try:
            r, g, b = img.split()
            r = np.array(r, dtype=np.uint16)
            g = np.array(g, dtype=np.uint16)
            b = np.array(b, dtype=np.uint16)
            rgb565 = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
            with open(FB, 'wb') as f:
                f.write(rgb565.astype(np.uint16).tobytes())
        except Exception as e:
            logger.error(f"Write error: {e}")

    def _canvas(self, bg=SKY):
        img = Image.new('RGB', (WIDTH, HEIGHT), bg)
        return img, ImageDraw.Draw(img)

    def _eye(self, draw, cx, cy,
             open_pct=1.0,
             iris_col=IRIS_BLUE,
             pupil_dx=0, pupil_dy=0,
             bg=SKY,
             lash_col=NAVY):
        """
        Draw one complete eye.
        cx, cy   = center
        open_pct = 0.0 (closed) to 1.0 (fully open)
        iris_col = color of iris ring
        pupil_dx/dy = offset for pupil position
        """
        EW  = 72   # half-width of eye
        EH  = 46   # half-height when fully open
        eh  = max(2, int(EH * open_pct))

        # ── 1. White sclera ──
        draw.ellipse(
            [cx - EW, cy - eh, cx + EW, cy + eh],
            fill=WHITE, outline=NAVY, width=2
        )
        # Clip lower half to create open-eye shape
        draw.rectangle(
            [cx - EW - 2, cy + 1, cx + EW + 2, cy + eh + 4],
            fill=bg
        )

        # ── 2. Iris (colored ring) ──
        if open_pct > 0.15:
            IR = 26
            px = cx + pupil_dx
            py = cy + pupil_dy
            # Clamp pupil inside white area
            px = max(cx - EW + IR + 4, min(cx + EW - IR - 4, px))
            py = max(cy - eh + IR + 2, min(cy - 4, py))
            draw.ellipse(
                [px - IR, py - IR, px + IR, py + IR],
                fill=iris_col
            )

            # ── 3. Pupil (black center) ──
            PR = 13
            draw.ellipse(
                [px - PR, py - PR, px + PR, py + PR],
                fill=BLACK
            )

            # ── 4. Highlight dot ──
            draw.ellipse(
                [px - 6, py - 16, px + 1, py - 9],
                fill=HIGHLIGHT
            )

        # ── 5. Upper eyelid arc ──
        draw.arc(
            [cx - EW, cy - eh, cx + EW, cy + eh],
            start=195, end=345,
            fill=lash_col, width=3
        )

        # ── 6. Eyelashes ──
        if open_pct > 0.2:
            lash_data = [
                (-62, -8,  -72, -26),
                (-40, -38, -46, -56),
                (-12, -44, -12, -64),
                ( 18, -42,  22, -62),
                ( 46, -32,  54, -50),
                ( 64, -10,  76, -24),
            ]
            scale = open_pct
            for x1, y1, x2, y2 in lash_data:
                draw.line(
                    [cx + x1, cy + int(y1 * scale),
                     cx + x2, cy + int(y2 * scale)],
                    fill=lash_col, width=2
                )

    def _blush(self, draw, bg=SKY):
        """Pink cheek blush circles"""
        # Left cheek
        draw.ellipse([55,  185, 135, 225], fill=BLUSH)
        # Right cheek
        draw.ellipse([345, 185, 425, 225], fill=BLUSH)

    def _smile(self, draw, width=4, color=SMILE_COL, size=1.0):
        """Curved smile at bottom center"""
        s = int(75 * size)
        draw.arc(
            [240 - s, 228, 240 + s, 288],
            start=12, end=168,
            fill=color, width=width
        )

    # ══════════════════════════════════════
    # ANIMATION FRAMES
    # ══════════════════════════════════════

    def _f_normal(self, f):
        """Idle — slow blink every ~4 s, gentle pupil drift"""
        img, draw = self._canvas(SKY)

        # Blink cycle: open 85 frames, close 5, open 5
        cyc = f % 95
        if   cyc < 85: op = 1.0
        elif cyc < 90: op = 1.0 - (cyc - 85) / 5.0
        elif cyc < 93: op = 0.05
        else:          op = (cyc - 93) / 2.0

        dx = int(5 * math.sin(f * 0.03))  # gentle drift

        self._eye(draw, 145, 135, op, IRIS_BLUE, dx, 0, SKY)
        self._eye(draw, 335, 135, op, IRIS_BLUE, dx, 0, SKY)
        self._blush(draw, SKY)
        self._smile(draw)
        self._write(img)

    def _f_sleeping(self, f):
        """Sleeping — fully closed with ZZZ floating up"""
        img, draw = self._canvas((110, 185, 215))

        # Closed eyelid arc
        for cx in [145, 335]:
            draw.arc(
                [cx - 72, 130, cx + 72, 145],
                start=195, end=345,
                fill=NAVY, width=3
            )
            # Lashes pointing down (sleepy)
            for x1, y1, x2, y2 in [
                (-55, 0, -62, 14), (-25, 7, -27, 22),
                (  5, 8,   5, 24), ( 35, 6,  38, 22),
                ( 58, 0,  66, 14)
            ]:
                draw.line(
                    [cx + x1, 137 + y1, cx + x2, 137 + y2],
                    fill=NAVY, width=2
                )

        self._blush(draw, (110, 185, 215))
        # Gentle sleep smile
        draw.arc([175, 232, 305, 272], start=15, end=165,
                 fill=NAVY, width=2)

        # Floating ZZZs
        for i, (zx, zy, sz, txt) in enumerate([
            (330, 70, 18, "z"),
            (355, 45, 22, "Z"),
            (382, 18, 26, "Z"),
        ]):
            drift = int(30 * ((f * 0.015 + i * 0.3) % 1.0))
            alpha = int(200 * abs(math.sin(f * 0.04 + i * 1.0)))
            col   = (20, 50, 120, alpha)
            draw.text((zx, zy - drift), txt,
                      fill=(20, 50, 120))

        self._write(img)

    def _f_listening(self, f):
        """Listening — wide green eyes, sound-wave rings on sides"""
        img, draw = self._canvas((90, 185, 220))

        # Eyes look slightly up + slight pulse
        pulse = int(3 * math.sin(f * 0.18))
        self._eye(draw, 145, 132, 1.0, IRIS_GRN, 0, -6 + pulse,
                  (90, 185, 220))
        self._eye(draw, 335, 132, 1.0, IRIS_GRN, 0, -6 + pulse,
                  (90, 185, 220))
        self._blush(draw, (90, 185, 220))
        self._smile(draw, color=(0, 100, 50))

        # Animated sound rings on left and right
        for side_cx in [28, 452]:
            for i in range(3):
                phase = (f * 0.12 + i * 0.7) % (2 * math.pi)
                r     = int(18 + i * 14 + 6 * math.sin(phase))
                alpha = max(60, int(180 - i * 50))
                col   = (0, 160 - i * 30, 80)
                flip_start = 270 if side_cx < 240 else 90
                flip_end   = 90  if side_cx < 240 else 270
                draw.arc(
                    [side_cx - r, 130 - r, side_cx + r, 130 + r],
                    start=flip_start, end=flip_end,
                    fill=col, width=2
                )

        draw.text((165, 284), "LISTENING...", fill=(0, 90, 50))
        self._write(img)

    def _f_thinking(self, f):
        """Thinking — eyes look up-right, thought bubble"""
        img, draw = self._canvas((85, 165, 215))

        # Pupils drift up-right in a slow arc
        angle = f * 0.04
        dx    = int(10 * math.cos(angle))
        dy    = int(-8 + 4 * math.sin(angle))

        # Left eye slightly squinted
        self._eye(draw, 145, 135, 0.55, IRIS_BLUE,  dx,  dy,
                  (85, 165, 215))
        self._eye(draw, 335, 135, 1.0,  IRIS_BLUE,  dx,  dy,
                  (85, 165, 215))
        self._blush(draw, (85, 165, 215))
        draw.arc([185, 235, 295, 268], start=15, end=165,
                 fill=NAVY, width=2)

        # Thought bubble
        bx, by = 390, 20
        bob    = int(5 * math.sin(f * 0.08))
        for (rx, ry, rw, rh) in [
            (bx - 6,  by + 55 + bob,  12, 10),
            (bx - 10, by + 38 + bob,  18, 14),
            (bx - 22, by + 14 + bob,  44, 32),
        ]:
            draw.ellipse([rx, ry, rx + rw, ry + rh],
                         fill=WHITE, outline=NAVY, width=1)
        dots = "." * (1 + (f // 12) % 3)
        draw.text((180, 285), f"THINKING{dots}", fill=(30, 60, 100))
        self._write(img)

    def _f_answering(self, f):
        """Speaking — animated open/close mouth, sparkle eyes"""
        img, draw = self._canvas((100, 175, 228))

        # Eyes blink less, look forward
        blink_cyc = f % 70
        op = 1.0 if blink_cyc < 65 else max(0.1, 1.0 - (blink_cyc - 65) * 0.2)

        self._eye(draw, 145, 132, op, IRIS_YLW, 0, 0, (100, 175, 228))
        self._eye(draw, 335, 132, op, IRIS_YLW, 0, 0, (100, 175, 228))
        self._blush(draw, (100, 175, 228))

        # Animated speaking mouth
        mo = abs(math.sin(f * 0.35)) * 28
        cx, cy = 240, 248
        # Outer lips
        draw.arc([cx - 58, cy,        cx + 58, cy + int(mo) + 20],
                 start=8, end=172, fill=NAVY, width=3)
        # Inner (tongue/teeth hint)
        if mo > 8:
            draw.arc([cx - 36, cy + 4, cx + 36, cy + int(mo) + 10],
                     start=5, end=175, fill=(180, 60, 60), width=2)

        # Four rotating sparkle dots
        for i in range(4):
            a  = f * 0.09 + i * math.pi / 2
            sx = int(240 + 210 * math.cos(a))
            sy = int(155 + 90  * math.sin(a))
            if 0 < sx < WIDTH and 0 < sy < HEIGHT:
                s = int(4 + 2 * math.sin(f * 0.25 + i))
                draw.ellipse([sx - s, sy - s, sx + s, sy + s],
                             fill=(220, 180, 0))

        draw.text((182, 287), "SPEAKING...", fill=(110, 80, 0))
        self._write(img)

    def _f_music(self, f):
        """Music — bouncing eyes, dancing equalizer bars"""
        img, draw = self._canvas((55, 20, 90))

        # Eyes bounce out of sync
        b1 = int(7 * abs(math.sin(f * 0.22)))
        b2 = int(7 * abs(math.sin(f * 0.22 + math.pi)))

        self._eye(draw, 145, 135 - b1, 1.0, IRIS_PRP, 0, 0,
                  (55, 20, 90))
        self._eye(draw, 335, 135 - b2, 1.0, IRIS_PRP, 0, 0,
                  (55, 20, 90))

        # Blush also bounces
        draw.ellipse([ 55, 192 - b1, 135, 228 - b1], fill=BLUSH)
        draw.ellipse([345, 192 - b2, 425, 228 - b2], fill=BLUSH)

        # Big happy smile
        draw.arc([155, 228, 325, 285],
                 start=8, end=172, fill=(200, 120, 255), width=4)

        # Equalizer bars — 14 bars
        bar_count = 14
        bar_w     = 24
        gap       = 8
        total_w   = bar_count * (bar_w + gap)
        sx        = (WIDTH - total_w) // 2
        for i in range(bar_count):
            h = int(18 + 22 * abs(math.sin(f * 0.2 + i * 0.45)))
            x = sx + i * (bar_w + gap)
            hue = (f * 4 + i * 18) % 360
            r   = int(128 + 127 * math.sin(math.radians(hue)))
            g   = int(128 + 127 * math.sin(math.radians(hue + 120)))
            b   = int(128 + 127 * math.sin(math.radians(hue + 240)))
            r, g, b = (max(0, min(255, v)) for v in (r, g, b))
            draw.rectangle([x, 308 - h, x + bar_w, 308], fill=(r, g, b))

        # Floating music note
        nx = int(440 + 12 * math.sin(f * 0.09))
        ny = int(25  + 10 * math.cos(f * 0.12))
        draw.text((nx, ny), "♪", fill=(200, 140, 255))

        self._write(img)

    def _f_obstacle(self, f):
        """Obstacle — flashing red alert, scared wide eyes"""
        flash  = (f // 7) % 2
        bg     = (170, 15, 15) if flash else (70, 0, 0)
        img, draw = self._canvas(bg)

        # Scared wide eyes — pupils look up (fear)
        self._eye(draw, 145, 128, 1.0, IRIS_RED, 0, -14, bg)
        self._eye(draw, 335, 128, 1.0, IRIS_RED, 0, -14, bg)

        # Fear blush (bright red)
        draw.ellipse([ 55, 185, 135, 220], fill=(255, 80,  80))
        draw.ellipse([345, 185, 425, 220], fill=(255, 80,  80))

        # Warning radial lines
        for i in range(8):
            a  = math.radians(i * 45 + f * 4)
            x1 = int(240 + 165 * math.cos(a))
            y1 = int(160 + 125 * math.sin(a))
            x2 = int(240 + 210 * math.cos(a))
            y2 = int(160 + 145 * math.sin(a))
            draw.line([x1, y1, x2, y2], fill=(255, 210, 0), width=3)

        # Wavy scared mouth
        pts = []
        for xi in range(160, 321, 10):
            wave_y = 258 + int(8 * math.sin((xi - 160) * 0.12 + f * 0.3))
            pts.append((xi, wave_y))
        if len(pts) > 1:
            draw.line(pts, fill=(255, 220, 0), width=3)

        if flash:
            draw.text((135, 282), "OBSTACLE DETECTED!", fill=(255, 255, 0))

        self._write(img)

    def _f_moving(self, f, direction="forward"):
        """Moving — pupils look in direction, speed lines"""
        bg = (80, 155, 210)
        img, draw = self._canvas(bg)

        offsets = {
            "forward":  ( 0, -12),
            "backward": ( 0,  12),
            "left":     (-14,  0),
            "right":    ( 14,  0),
        }
        dx, dy = offsets.get(direction, (0, 0))
        wobble = int(3 * math.sin(f * 0.3))

        self._eye(draw, 145, 135, 1.0, IRIS_ORG,
                  dx + wobble, dy, bg)
        self._eye(draw, 335, 135, 1.0, IRIS_ORG,
                  dx + wobble, dy, bg)
        self._blush(draw, bg)
        self._smile(draw, color=(30, 60, 100))

        # Speed streaks
        streak_col = (160, 210, 240)
        streak_dir = {
            "forward":  [(x, 290, x - 30, 308) for x in range(60, 440, 50)],
            "backward": [(x, 300, x + 30, 282) for x in range(60, 440, 50)],
            "left":     [(80, y, 108, y)        for y in range(260, 310, 14)],
            "right":    [(400, y, 372, y)       for y in range(260, 310, 14)],
        }
        phase_offset = int(25 * ((f * 0.08) % 1.0))
        for x1, y1, x2, y2 in streak_dir.get(direction, []):
            draw.line(
                [x1 + phase_offset, y1, x2 + phase_offset, y2],
                fill=streak_col, width=2
            )

        labels = {
            "forward":  "▲  MOVING FORWARD",
            "backward": "▼  MOVING BACKWARD",
            "left":     "◀  TURNING LEFT",
            "right":    "▶  TURNING RIGHT",
        }
        draw.text((140, 283), labels.get(direction, "MOVING"),
                  fill=(20, 50, 100))
        self._write(img)

    def _f_happy(self, f):
        """Happy — big smile, bouncing, sparkles"""
        img, draw = self._canvas((110, 200, 240))

        bounce = int(8 * abs(math.sin(f * 0.22)))

        # Happy half-moon eyes (upward arc, no white below)
        for cx in [145, 335]:
            cy  = 135 - bounce
            EW, EH = 72, 46
            # White area
            draw.ellipse([cx - EW, cy - EH, cx + EW, cy + EH],
                         fill=WHITE)
            # Cover lower half to make open eye
            draw.rectangle([cx - EW - 2, cy + 1, cx + EW + 2, cy + EH + 4],
                            fill=(110, 200, 240))
            # Happy upward arc
            draw.arc([cx - EW, cy - EH, cx + EW, cy + EH],
                     start=195, end=345, fill=NAVY, width=4)
            # Eyelashes
            for x1, y1, x2, y2 in [
                (-55, 0, -64, -16), (-30, -36, -35, -54),
                (  0, -44,  0, -64), ( 32, -34,  38, -52),
                ( 57, -2,  66, -18),
            ]:
                draw.line([cx + x1, cy + y1, cx + x2, cy + y2],
                          fill=NAVY, width=2)

        # Blush bounces up
        draw.ellipse([ 55, 192 - bounce, 135, 228 - bounce], fill=BLUSH)
        draw.ellipse([345, 192 - bounce, 425, 228 - bounce], fill=BLUSH)

        # Big smile
        draw.arc([145, 228, 335, 292],
                 start=8, end=172, fill=NAVY, width=5)

        # Sparkles
        for i in range(6):
            a  = f * 0.07 + i * math.pi / 3
            sx = int(240 + 215 * math.cos(a))
            sy = int(155 + 118 * math.sin(a))
            if 0 < sx < WIDTH and 0 < sy < HEIGHT:
                s = int(4 + 2 * math.sin(f * 0.18 + i))
                draw.ellipse([sx - s, sy - s, sx + s, sy + s],
                             fill=(255, 220, 0))

        self._write(img)

    # ══════════════════════════════════════
    # ANIMATION ENGINE
    # ══════════════════════════════════════

    def _loop(self):
        f = 0
        while self._anim_running:
            s = self.current_state
            try:
                if   s == "sleeping":             self._f_sleeping(f)
                elif s == "listening":            self._f_listening(f)
                elif s == "thinking":             self._f_thinking(f)
                elif s == "answering":            self._f_answering(f)
                elif s == "music":                self._f_music(f)
                elif s == "obstacle":             self._f_obstacle(f)
                elif s in ("forward", "backward",
                           "left", "right"):      self._f_moving(f, s)
                elif s == "happy":                self._f_happy(f)
                else:                             self._f_normal(f)
            except Exception as e:
                logger.error(f"Frame error [{s}]: {e}")
            f = (f + 1) % 2000
            time.sleep(0.045)   # ~22 fps

    def start_animation(self):
        self._anim_running = True
        self._anim_thread  = threading.Thread(
            target=self._loop, daemon=True
        )
        self._anim_thread.start()
        logger.info("Animation running at ~22 fps")

    def stop_animation(self):
        self._anim_running = False

    # ── Public API (matches what maahi_main.py calls) ──

    def show_state(self, state):
        self.current_state = state
        logger.info(f"Eye state → {state}")

    def show_startup(self):
        """Opening-eyes animation on boot"""
        for i in range(36):
            img, draw = self._canvas(SKY)
            op = min(1.0, i / 24.0)
            self._eye(draw, 145, 135, op, IRIS_BLUE, 0, 0, SKY)
            self._eye(draw, 335, 135, op, IRIS_BLUE, 0, 0, SKY)
            if op > 0.4:
                self._blush(draw, SKY)
            if op > 0.7:
                self._smile(draw)
            if op > 0.9:
                draw.text((142, 285), "Hello! I am MAAHI  ♥",
                          fill=NAVY)
            self._write(img)
            time.sleep(0.04)
        self.show_state("normal")

    def show_song_info(self, title, artist):
        self.show_state("music")

    def show_response(self, text):
        self.show_state("answering")

    # Compatibility aliases
    def start_blink_loop(self):
        self.start_animation()

    def stop_blink_loop(self):
        self.stop_animation()

    def blink_animation(self):
        pass

    def clear(self):
        self.stop_animation()
        img = Image.new('RGB', (WIDTH, HEIGHT), (0, 0, 0))
        self._write(img)


# ══════════════════════════════════════
# STANDALONE TEST
# ══════════════════════════════════════

if __name__ == "__main__":
    import sys

    # Hide terminal cursor on SPI display
    os.system("setterm -cursor off 2>/dev/null")

    print("MAAHI Display Eyes — Animated Test")
    print("Press Ctrl+C to exit\n")

    d = DisplayEyes()
    d.show_startup()
    d.start_animation()

    demo = [
        ("normal",    3.5, "Idle / normal"),
        ("listening", 3.0, "Listening for command"),
        ("thinking",  3.0, "Processing / thinking"),
        ("answering", 3.5, "Speaking response"),
        ("music",     4.0, "Playing music"),
        ("happy",     3.0, "Happy expression"),
        ("sleeping",  3.5, "Sleeping / idle"),
        ("obstacle",  3.0, "Obstacle detected!"),
        ("forward",   2.5, "Moving forward"),
        ("backward",  2.5, "Moving backward"),
        ("left",      2.0, "Turning left"),
        ("right",     2.0, "Turning right"),
        ("normal",    3.0, "Back to normal"),
    ]

    try:
        for state, dur, desc in demo:
            print(f"  [{state:12s}]  {desc}")
            d.show_state(state)
            time.sleep(dur)

        print("\nAll states complete. Looping normal...")
        d.show_state("normal")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")
        d.stop_animation()
        d.clear()
        os.system("setterm -cursor on 2>/dev/null")
        print("Done!")
