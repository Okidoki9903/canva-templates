"""Kinetic-typography motion graphics for the FOA 2026 video templates.

Renders, per section, a beat-cut intro (~8 s) and one shared outro (~4.5 s) as
1080x1920 MP4 files in the style of fast Canva "typography reels": bold words
popping on white, hard cuts, colour flashes with rotated giant type, a hand-drawn
circle, an ink wipe and a repeating-word end card.

Run:  python3 motion.py            (all sections)
      python3 motion.py day-1      (one section)
Needs: pillow, numpy, imageio-ffmpeg
"""
import math
import os
import subprocess
import sys
from functools import lru_cache

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "motion")
FONT = os.path.join(ROOT, "fonts", "Montserrat%5Bwght%5D.ttf")

W, H, FPS = 1080, 1920, 30
WHITE = (255, 255, 255)
INK = (12, 12, 14)
PAPER = (248, 247, 244)

EVENT_DATES = "30 SEPT – 03 OCT 2026"
EVENT_CITY = "TORONTO"

SECTIONS = {
    "day-1": dict(
        accent=(242, 84, 45), w1="Toronto", w2="Let's begin", flash="NOW",
        scroll=("IS THE TIME", "DAY ONE"), circle=["the", "16th", "African", "Summit"],
        stack=["DAY", "ONE"], final=["DAY", "1"],
    ),
    "job-fair": dict(
        accent=(31, 163, 74), w1="Hello", w2="Future talent", flash="HIRED",
        scroll=("YOUR NEXT MOVE", "JOB FAIR"), circle=["meet", "your", "next", "employer"],
        stack=["JOB", "FAIR"], final=["JOB", "FAIR"],
    ),
    "market-place": dict(
        accent=(242, 140, 30), w1="Made", w2="In Africa", flash="SHOP",
        scroll=("LOCAL BRANDS", "MARKET PLACE"), circle=["discover", "support", "buy", "African"],
        stack=["MARKET", "PLACE"], final=["MARKET", "PLACE"],
    ),
    "panels": dict(
        accent=(47, 111, 237), w1="Listen", w2="Debate", flash="TALK",
        scroll=("BIG IDEAS", "PANELS"), circle=["real", "talks", "for", "Africa"],
        stack=["THE", "PANELS"], final=["PANEL", "TALKS"],
    ),
    "speakers": dict(
        accent=(227, 165, 59), w1="Voices", w2="That lead", flash="HEAR",
        scroll=("ON STAGE", "SPEAKERS"), circle=["leaders", "who", "shape", "Africa"],
        stack=["ON", "STAGE"], final=["THE", "SPEAKERS"],
    ),
    "graduations": dict(
        accent=(123, 63, 228), w1="Class", w2="Of 2026", flash="GRAD",
        scroll=("BEST  ×  STEP", "GRADUATION"), circle=["from", "learning", "to", "leading"],
        stack=["BEST", "STEP"], final=["CLASS", "OF 2026"],
    ),
}


# ------------------------------------------------------------------ helpers

@lru_cache(maxsize=256)
def font(size, weight=800):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_axes([weight])
    return f


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = min(max(x, 0.0), 1.0)
    return 3 * x * x - 2 * x * x * x


@lru_cache(maxsize=512)
def text_layer(text, size, color, weight=800, dot=None):
    """Tightly cropped RGBA image of `text`, optionally followed by a coloured dot."""
    f = font(size, weight)
    l, t, r, b = f.getbbox(text + (". " if dot else ""))
    img = Image.new("RGBA", (r - l + 10, b - t + 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((5 - l, 5 - t), text, font=f, fill=color)
    if dot:
        x = 5 - l + d.textlength(text, font=f)
        d.text((x, 5 - t), ".", font=f, fill=dot)
    return img


def paste(canvas, layer, x, y, anchor="mm", scale=1.0, rot=0.0, alpha=1.0):
    if scale != 1.0:
        layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))),
                             Image.BICUBIC)
    if rot:
        layer = layer.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1.0:
        a = layer.getchannel("A").point(lambda v: int(v * alpha))
        layer = layer.copy()
        layer.putalpha(a)
    ax = {"l": 0, "m": 0.5, "r": 1}[anchor[0]]
    ay = {"t": 0, "m": 0.5, "b": 1}[anchor[1]]
    canvas.alpha_composite(layer, (int(x - layer.width * ax), int(y - layer.height * ay)))


def blank(color=PAPER):
    return Image.new("RGBA", (W, H), color + (255,))


def fit(lines, max_size, width=860, weight_ratio=0.8):
    """Largest size whose longest line fits `width` px."""
    f = font(100, 900)
    longest = max(f.getlength(l) for l in lines) / 100
    return int(min(max_size, width / longest))


def pop(lt, dur=0.18):
    """Overshoot scale for a word that 'pops' in."""
    x = min(lt / dur, 1.0)
    return 0.6 + 0.4 * ease_out(x) + 0.08 * math.sin(x * math.pi)


# ------------------------------------------------------------------ textures

_rng = np.random.default_rng(7)


def _noise(w, h, octaves=4, seed=0):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        cells = 4 * 2 ** o
        small = rng.random((cells * h // w + 2, cells + 2)).astype(np.float32)
        im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += amp * (np.asarray(im, np.float32) / 255)
        tot += amp
        amp *= 0.5
    return acc / tot


@lru_cache(maxsize=16)
def brush_bg(color):
    """Painterly colour field like the orange frames of the reference."""
    n = _noise(270, 480, 5, seed=sum(color))
    strokes = Image.new("L", (270, 480), 128)
    d = ImageDraw.Draw(strokes)
    rng = np.random.default_rng(sum(color) + 1)
    for _ in range(90):
        x, y = rng.integers(-40, 270), rng.integers(-40, 480)
        wv, hv = rng.integers(40, 160), rng.integers(12, 40)
        d.rounded_rectangle((x, y, x + wv, y + hv), radius=10, fill=int(rng.integers(95, 165)))
    strokes = strokes.filter(ImageFilter.GaussianBlur(4))
    s = np.asarray(strokes, np.float32) / 255 - 0.5
    shade = 1 + (n - 0.5) * 0.28 + s * 0.22
    base = np.array(color, np.float32)[None, None, :]
    rgb = np.clip(base * shade[..., None], 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb).resize((W, H), Image.BICUBIC)
    grain = (_rng.random((H, W)) * 18 - 9).astype(np.float32)
    arr = np.clip(np.asarray(img, np.float32) + grain[..., None], 0, 255).astype(np.uint8)
    return Image.fromarray(arr).convert("RGBA")


@lru_cache(maxsize=1)
def ink_field():
    """Distance + noise field; thresholding it gives an organic ink spread."""
    n = _noise(270, 480, 5, seed=42)
    yy, xx = np.mgrid[0:480, 0:270].astype(np.float32)
    d = np.sqrt(((xx - 135) / 270) ** 2 + ((yy - 200) / 480) ** 2) / 0.62
    return d * 0.62 + n * 0.55


def ink_mask(p):
    f = ink_field()
    m = (f < p * 1.25).astype(np.uint8) * 255
    im = Image.fromarray(m).filter(ImageFilter.GaussianBlur(1.2)).resize((W, H), Image.BICUBIC)
    return im.point(lambda v: 255 if v > 128 else 0).filter(ImageFilter.GaussianBlur(2))


@lru_cache(maxsize=4)
def pattern_tile(word, color):
    f = font(170, 900)
    tile = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    step_x = int(d.textlength(word + "  ", font=f))
    for row, y in enumerate(range(-200, H * 2, 190)):
        off = (row * step_x // 3) % step_x
        for x in range(-step_x - off, W * 2, step_x):
            d.text((x, y), word, font=f, fill=color)
    return tile.rotate(24, resample=Image.BICUBIC)


# ------------------------------------------------------------------ scenes

def sc_hello(lt, dur, s):
    c = blank()
    x0, y = 150, 760
    paste(c, text_layer(s["w1"], 118, INK, 800, s["accent"]), x0, y, "lm", scale=pop(lt))
    if lt > dur * 0.5:
        k = (lt - dur * 0.5) / (dur * 0.45)
        full = s["w2"]
        shown = full[: max(1, int(len(full) * min(k, 1) + 0.999))]
        paste(c, text_layer(shown, 118, INK, 800, s["accent"] if len(shown) == len(full) else None),
              x0, y + 150, "lm")
    return c


def sc_split(lt, dur, s):
    # quick grey dip then inverted split layout
    if lt < 0.12:
        c = sc_hello(10, 1, s)
        dim = Image.new("RGBA", (W, H), (60, 60, 60, 130))
        c.alpha_composite(dim)
        return c
    c = blank(INK)
    paste(c, text_layer(s["w1"], 104, WHITE, 800, s["accent"]), 120, 230, "lm")
    shift = int(60 * (1 - ease_out((lt - 0.12) / 0.2)))
    paste(c, text_layer(s["w2"], 104, WHITE, 800, s["accent"]), 120 - shift, H - 260, "lm")
    return c


def sc_flash_word(lt, dur, s):
    c = blank()
    paste(c, text_layer(s["flash"], 230, s["accent"], 900), W / 2, H / 2, scale=pop(lt, 0.14))
    return c


def sc_spin(lt, dur, s):
    c = brush_bg(s["accent"]).copy()
    k = ease_in_out(lt / dur)
    paste(c, text_layer(s["flash"], 150, WHITE, 900), W / 2 + 40 * k, H / 2 + 60 * k,
          scale=1.0 - 0.35 * k, rot=-60 * k)
    return c


def sc_columns(lt, dur, s):
    c = brush_bg(s["accent"]).copy()
    k = lt / dur
    a, b = s["scroll"]
    la = text_layer((a + "   ") * 3, 300, WHITE, 900).rotate(-90, expand=True)
    lb = text_layer((b + "   ") * 3, 300, WHITE, 900).rotate(90, expand=True)
    span = la.height - H
    c.alpha_composite(la, (W - la.width + 20, int(-span * (0.15 + 0.5 * k))))
    span_b = lb.height - H
    c.alpha_composite(lb, (-20, int(-span_b * (0.65 - 0.5 * k))))
    # white bar peeking at the bottom like the reference
    ImageDraw.Draw(c).rectangle((0, H - 60, int(W * 0.25 * (1 - k)), H - 30), fill=WHITE)
    return c


def sc_circle(lt, dur, s):
    c = blank()
    d = ImageDraw.Draw(c)
    cx, cy, r = W / 2, 760, 330
    sketch = min(lt / (dur * 0.35), 1.0)
    if sketch < 1.0:
        # dashed sketch strokes appearing
        n = int(18 * ease_out(sketch)) + 1
        for i in range(n):
            a0 = i * 20 - 90
            d.arc((cx - r, cy - r, cx + r, cy + r), a0, a0 + 11, fill=INK, width=20)
    else:
        sweep = ease_out((lt - dur * 0.35) / (dur * 0.25))
        d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * sweep, fill=INK, width=26)
        d.arc((cx - r - 18, cy - r + 6, cx + r - 6, cy + r + 14), -60, -60 + 300 * sweep,
              fill=INK, width=12)
        words = s["circle"]
        per = (dur * 0.4) / len(words)
        base = lt - dur * 0.5
        y = cy - 70 * (len(words) - 1) / 2
        for i, w in enumerate(words):
            if base >= i * per:
                col = s["accent"] if i == len(words) - 1 else INK
                size = min(92, int(430 / max(font(100, 800).getlength(w) / 100, 0.1)))
                paste(c, text_layer(w, size, col, 800), cx - 215, y + i * 80, "lm",
                      scale=pop(base - i * per, 0.12))
    return c


def sc_stack_ink(lt, dur, s):
    c = blank()
    lines = s["stack"]
    size = fit(lines, 250)
    soft = tuple(int(v * 0.75 + 255 * 0.25) for v in s["accent"])
    y0 = 560
    for i, ln in enumerate(lines):
        if lt > i * 0.12:
            paste(c, text_layer(ln, size, soft, 900), 110, y0 + i * size * 0.95, "lm",
                  scale=pop(lt - i * 0.12, 0.12))
    p = (lt - dur * 0.3) / (dur * 0.62)
    if p > 0:
        m = ink_mask(ease_in_out(p))
        inv = blank(INK)
        for i, ln in enumerate(lines):
            paste(inv, text_layer(ln, size, (236, 236, 236), 900), 110, y0 + i * size * 0.95, "lm")
        c.paste(inv, (0, 0), m)
    return c


def sc_rotated(lt, dur, s):
    c = blank()
    layer = Image.new("RGBA", (H, W), (0, 0, 0, 0))
    title = " ".join(s["final"])
    big = text_layer(title, fit([title], 250, width=1500), INK, 900)
    small1 = text_layer(EVENT_DATES, 84, INK, 700)
    small2 = text_layer(EVENT_CITY, 120, INK, 800, s["accent"])
    small3 = text_layer("16th African Economic Summit", 64, INK, 600)
    x = 200
    k = ease_out(lt / 0.2)
    layer.alpha_composite(big, (x - int(80 * (1 - k)), 170))
    if lt > 0.1:
        layer.alpha_composite(small1, (x, 460))
    if lt > 0.2:
        layer.alpha_composite(small2, (x, 580))
    if lt > 0.3:
        layer.alpha_composite(small3, (x, 740))
    c.alpha_composite(layer.rotate(90, expand=True), (0, 0))
    return c


def sc_final(lt, dur, s):
    c = blank()
    lines = s["final"]
    size = fit(lines, 230)
    y0 = H / 2 - size * 0.5 * (len(lines) - 1) - 40
    for i, ln in enumerate(lines):
        last = i == len(lines) - 1
        dot = s["accent"] if (last and lt > dur * 0.45) else None
        paste(c, text_layer(ln, size, INK, 900, dot), 120, y0 + i * size, "lm")
    return c


def sc_pattern_end(lt, dur, s, word="FOA2026", main=("see you", "there")):
    c = blank()
    tile = pattern_tile(word, (236, 235, 232))
    k = lt / dur
    fade = ease_out(lt / 0.3)
    ox = int(-W * 0.5 - 120 * k)
    oy = int(-H * 0.5 - 60 * k)
    t = tile.copy()
    t.putalpha(t.getchannel("A").point(lambda v: int(v * fade)))
    c.alpha_composite(t, (ox, oy))
    paste(c, text_layer(main[0], 120, INK, 800), W / 2, H / 2 - 80)
    paste(c, text_layer(main[1], 150, INK, 900, s["accent"]), W / 2, H / 2 + 80,
          scale=pop(lt, 0.2))
    return c


def sc_outro_thanks(lt, dur, s):
    c = blank()
    paste(c, text_layer("Thank you", 130, INK, 800, s["accent"]), W / 2, H / 2 - 60,
          scale=pop(lt))
    if lt > dur * 0.45:
        paste(c, text_layer("for being part of it", 60, INK, 600), W / 2, H / 2 + 80)
    return c


def sc_outro_black(lt, dur, s):
    c = blank(INK)
    items = [
        (text_layer("CASA FOUNDATION", 78, WHITE, 800), 300),
        (text_layer("×", 78, s["accent"], 800), 400),
        (text_layer("FRIENDS OF AFRICA", 78, WHITE, 800), 500),
        (text_layer(EVENT_DATES, 70, WHITE, 800), H - 470),
        (text_layer("Metro Toronto Convention Centre", 50, (200, 200, 200), 600), H - 380),
        (text_layer("#FOA2026  ·  @friendsofafricafoa", 46, s["accent"], 700), H - 300),
    ]
    for i, (layer, y) in enumerate(items):
        k = ease_out((lt - i * 0.08) / 0.25)
        if k > 0:
            paste(c, layer, 110 - 90 * (1 - k), y, "lm", alpha=k)
    # accent bar growing across the middle
    bw = int((W - 220) * ease_in_out((lt - 0.3) / 0.8))
    if bw > 0:
        ImageDraw.Draw(c).rectangle((110, H / 2 - 8, 110 + bw, H / 2 + 8), fill=s["accent"])
    return c


# ------------------------------------------------------------------ timelines

def intro_timeline():
    # (duration seconds, scene) — cuts land on a ~120 bpm grid
    return [
        (1.2, sc_hello), (0.6, sc_split), (0.5, sc_flash_word), (0.5, sc_spin),
        (1.4, sc_columns), (1.8, sc_circle), (1.3, sc_stack_ink), (0.9, sc_rotated),
        (1.0, sc_final),
    ]


def outro_timeline():
    return [
        (1.2, sc_outro_thanks), (1.6, sc_outro_black), (1.8, sc_pattern_end),
    ]


def render(timeline, s, path):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-movflags", "+faststart", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total = sum(d for d, _ in timeline)
    n = int(round(total * FPS))
    starts, acc = [], 0.0
    for d, f in timeline:
        starts.append((acc, d, f))
        acc += d
    for i in range(n):
        t = i / FPS
        for st, d, f in starts:
            if st <= t < st + d or (f is starts[-1][2] and t >= st):
                frame = f(t - st, d, s)
                break
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()
    print("wrote", os.path.relpath(path, ROOT), f"({total:.1f}s)")


def main():
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:] or list(SECTIONS)
    for i, key in enumerate(SECTIONS, 1):
        if key not in only:
            continue
        s = SECTIONS[key]
        render(intro_timeline(), s, os.path.join(OUT, f"{i:02d}-{key}-intro.mp4"))
        render(outro_timeline(), s, os.path.join(OUT, f"{i:02d}-{key}-outro.mp4"))


if __name__ == "__main__":
    main()
