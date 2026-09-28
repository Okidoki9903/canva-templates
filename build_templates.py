"""Build the FOA 2026 vertical video templates (.pptx) that get imported into Canva.

Every template is 1080x1920 (9:16) and follows one structure:

  1. Intro   - kinetic-typography MP4 from motion.py
  2. Clip    - footage + headline lower third
  3. Clip    - footage + name card
  4. Clip    - footage + big statement at the top
  5. Clip    - footage, clean (corner tag only)
  6. Outro   - kinetic-typography MP4 from motion.py

The "DROP YOUR CLIP HERE" images are placeholders: in Canva, drag a video onto
them to replace them. All text is editable Canva text.

Run:  python3 motion.py && python3 build_templates.py
"""
import os
import subprocess

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Pt

from motion import FONT, SECTIONS, STORIES

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
MOTION = os.path.join(ROOT, "motion")
OUT = os.path.join(ROOT, "templates")

W, H = 1080, 1920
INK = "0C0C0E"
WHITE = "FFFFFF"
GREY = "5C5C62"
FONT_NAME = "Montserrat"

COPY = {
    "day-1": dict(
        name="FOA 2026 – Day 1", tag="DAY 1",
        lt_kicker="OPENING DAY", lt_title="Add your headline",
        card_kicker="ON STAGE", card_name="Speaker Name", card_role="Title, Organization",
        statement="Add the moment of the day",
    ),
    "job-fair": dict(
        name="FOA 2026 – Job Fair", tag="JOB FAIR",
        lt_kicker="NOW HIRING", lt_title="Add your headline",
        card_kicker="HIRING PARTNER", card_name="Company Name", card_role="Roles: Role 1 · Role 2 · Role 3",
        statement="Bring your CV. Meet the employers",
    ),
    "market-place": dict(
        name="FOA 2026 – Market Place", tag="MARKET PLACE",
        lt_kicker="MADE IN AFRICA", lt_title="Add your headline",
        card_kicker="EXHIBITOR", card_name="Business Name", card_role="What they sell · Booth #00",
        statement="Shop local. Support African brands",
    ),
    "panels": dict(
        name="FOA 2026 – Panels", tag="PANELS",
        lt_kicker="PANEL", lt_title="Add the panel topic",
        card_kicker="PANELISTS", card_name="Name · Name · Name", card_role="Moderated by Name, Organization",
        statement="Add a key takeaway from the panel",
    ),
    "speakers": dict(
        name="FOA 2026 – Speakers", tag="SPEAKERS",
        lt_kicker="KEYNOTE", lt_title="Add the talk title",
        card_kicker="FEATURED SPEAKER", card_name="Dr. Speaker Name", card_role="President & CEO, Organization",
        statement="Add a quote from the speaker",
    ),
    "graduations": dict(
        name="FOA 2026 – Graduations BEST / STEP", tag="GRADUATION · BEST / STEP",
        lt_kicker="CLASS OF 2026", lt_title="Congrats, graduates",
        card_kicker="BEST GRADUATE", card_name="Graduate Name", card_role="Program: BEST / STEP · Cohort 2026",
        statement="From learning to leading",
    ),
}


def px(v):
    return Emu(int(round(v * 9525)))


def hexc(rgb):
    return "%02X%02X%02X" % rgb


# ------------------------------------------------------------------ assets

def make_placeholder(path, accent):
    img = Image.new("RGB", (W, H), (214, 214, 210))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, 64)
    f.set_variation_by_axes([900])
    fs = ImageFont.truetype(FONT, 34)
    fs.set_variation_by_axes([600])
    for y in range(-200, H + 200, 150):
        d.text((-60 + (y // 150 % 2) * 120, y), "CLIP  CLIP  CLIP  CLIP  CLIP", font=f, fill=(204, 204, 200))
    cx, cy = W // 2, int(H * 0.40)
    d.ellipse((cx - 90, cy - 90, cx + 90, cy + 90), fill=(12, 12, 14))
    d.polygon([(cx - 26, cy - 44), (cx - 26, cy + 44), (cx + 46, cy)], fill=accent)
    for text, font_, dy in (("DROP YOUR CLIP HERE", f, 150), ("drag a video from Uploads onto this image", fs, 240)):
        w = d.textlength(text, font=font_)
        d.text((cx - w / 2, cy + dy), text, font=font_, fill=(12, 12, 14))
    img.save(path, quality=90)


def poster(mp4, png, at="last"):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    args = [ff, "-loglevel", "error", "-y"]
    args += ["-sseof", "-0.1"] if at == "last" else ["-ss", "0.9"]
    args += ["-i", mp4, "-frames:v", "1", png]
    subprocess.run(args, check=True)


# ------------------------------------------------------------------ pptx helpers

def rect(slide, x, y, w, h, color, radius=None):
    shape = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    s = slide.shapes.add_shape(shape, px(x), px(y), px(w), px(h))
    if radius:
        s.adjustments[0] = radius
    s.fill.solid()
    s.fill.fore_color.rgb = RGBColor.from_string(color)
    s.line.fill.background()
    s.shadow.inherit = False
    return s


def text(slide, x, y, w, h, runs, size, bold=True, align=PP_ALIGN.LEFT, spacing=None,
         anchor=MSO_ANCHOR.TOP, line_spacing=None):
    """runs: list of (text, hex colour); a '\\n' inside text starts a new paragraph."""
    tb = slide.shapes.add_textbox(px(x), px(y), px(w), px(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    if line_spacing:
        p.line_spacing = line_spacing
    for chunk, color in runs:
        parts = chunk.split("\n")
        for i, part in enumerate(parts):
            if i:
                p = tf.add_paragraph()
                p.alignment = align
                if line_spacing:
                    p.line_spacing = line_spacing
            if not part:
                continue
            r = p.add_run()
            r.text = part
            r.font.size = Pt(size * 0.75)
            r.font.bold = bold
            r.font.name = FONT_NAME
            r.font.color.rgb = RGBColor.from_string(color)
            if spacing is not None:
                r._r.get_or_add_rPr().set("spc", str(int(spacing * 100)))
    return tb


def full_image(slide, path):
    return slide.shapes.add_picture(path, 0, 0, px(W), px(H))


def corner_tag(slide, label, accent):
    rect(slide, 60, 90, 22, 22, accent, radius=0.5)
    text(slide, 96, 84, 800, 40, [("FOA 2026  ·  " + label, WHITE)], 26, spacing=3)


# ------------------------------------------------------------------ pages

def page_motion(prs, mp4, poster_png):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.shapes.add_movie(mp4, 0, 0, px(W), px(H), poster_frame_image=poster_png, mime_type="video/mp4")


def page_lower_third(prs, c, acc, ph):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    full_image(s, ph)
    corner_tag(s, c["tag"], acc)
    rect(s, 60, 1440, 360, 64, INK)
    text(s, 84, 1454, 320, 40, [(c["lt_kicker"], WHITE)], 26, spacing=3)
    rect(s, 60, 1504, 960, 170, WHITE)
    text(s, 96, 1530, 900, 120, [(c["lt_title"], INK), (".", acc)], 66, anchor=MSO_ANCHOR.MIDDLE)


def page_name_card(prs, c, acc, ph):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    full_image(s, ph)
    corner_tag(s, c["tag"], acc)
    rect(s, 60, 1330, 960, 400, WHITE, radius=0.04)
    text(s, 110, 1380, 860, 40, [(c["card_kicker"], acc)], 28, spacing=4)
    text(s, 110, 1435, 860, 180, [(c["card_name"], INK), (".", acc)], 80, line_spacing=0.95)
    text(s, 110, 1630, 860, 60, [(c["card_role"], GREY)], 32, bold=False)


def page_statement(prs, c, acc, ph):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    full_image(s, ph)
    rect(s, 0, 0, W, 640, WHITE)
    text(s, 70, 110, 700, 40, [("FOA 2026  ·  " + c["tag"], INK)], 26, spacing=3)
    text(s, 70, 190, 940, 400, [(c["statement"], INK), (".", acc)], 92, line_spacing=0.95)


def page_clean(prs, c, acc, ph):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    full_image(s, ph)
    corner_tag(s, c["tag"], acc)


def build():
    os.makedirs(ASSETS, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    for i, (key, sec) in enumerate(SECTIONS.items(), 1):
        c, acc = COPY[key], hexc(sec["accent"])
        ph = os.path.join(ASSETS, f"clip-placeholder-{acc}.jpg")
        if not os.path.exists(ph):
            make_placeholder(ph, sec["accent"])
        intro = os.path.join(MOTION, f"{i:02d}-{key}-intro.mp4")
        outro = os.path.join(MOTION, f"{i:02d}-{key}-outro.mp4")
        intro_png = os.path.join(ASSETS, f"{i:02d}-{key}-intro.png")
        outro_png = os.path.join(ASSETS, f"{i:02d}-{key}-outro.png")
        poster(intro, intro_png)
        poster(outro, outro_png)

        prs = Presentation()
        prs.slide_width, prs.slide_height = px(W), px(H)
        prs.core_properties.title = c["name"]
        page_motion(prs, intro, intro_png)
        page_lower_third(prs, c, acc, ph)
        page_name_card(prs, c, acc, ph)
        page_statement(prs, c, acc, ph)
        page_clean(prs, c, acc, ph)
        page_motion(prs, outro, outro_png)
        out = os.path.join(OUT, f"{i:02d}-{key}.pptx")
        prs.save(out)
        print("wrote", os.path.relpath(out, ROOT))


def page_story_editable(prs, key, st, ph):
    """Static, fully editable story: photo/video on top, message card below."""
    acc = hexc(st["accent"])
    s = prs.slides.add_slide(prs.slide_layouts[6])
    full_image(s, ph)
    rect(s, 0, 980, W, 940, WHITE)
    text(s, 90, 1040, 600, 40, [("FOA 2026", INK), (".", acc)], 34, spacing=2)
    msg = "\n".join(st["final"])
    size = 120 if max(len(l) for l in st["final"]) <= 11 else 96
    text(s, 90, 1110, 900, 480, [(msg, INK), (".", acc)], size, line_spacing=0.92)
    rect(s, 90, 1110 + int(len(st["final"]) * size * 1.02) + 30, 240, 14, acc)
    text(s, 90, 1110 + int(len(st["final"]) * size * 1.02) + 80, 900, 140,
         [("\n".join(st["info"]), INK)], 44, bold=False)
    text(s, 90, 1810, 900, 40, [("#FOA2026  ·  @friendsofafricafoa", GREY)], 30, bold=False)


def build_stories():
    anim = Presentation()
    anim.slide_width, anim.slide_height = px(W), px(H)
    edit = Presentation()
    edit.slide_width, edit.slide_height = px(W), px(H)
    for i, (key, st) in enumerate(STORIES.items(), 1):
        mp4 = os.path.join(MOTION, f"story-{i:02d}-{key}.mp4")
        png = os.path.join(ASSETS, f"story-{i:02d}-{key}.png")
        poster(mp4, png)
        page_motion(anim, mp4, png)
        ph = os.path.join(ASSETS, f"clip-placeholder-{hexc(st['accent'])}.jpg")
        if not os.path.exists(ph):
            make_placeholder(ph, st["accent"])
        page_story_editable(edit, key, st, ph)
    for prs, name in ((anim, "07-stories-animated.pptx"), (edit, "08-stories-editable.pptx")):
        prs.save(os.path.join(OUT, name))
        print("wrote templates/" + name)


if __name__ == "__main__":
    build()
    build_stories()
