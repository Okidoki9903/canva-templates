"""Generate the AES 2026 (16th African Economic Summit) vertical video templates.

Each template is a 1080x1920 (9:16, Reels/Stories/TikTok) .pptx file that is
imported into Canva as a video design. Every page is one scene of the video:

  1. Opener         - event branding + section title
  2. Video + lower third
  3. Video + name card (speaker / panel / exhibitor / employer / graduate)
  4. Video + big caption at the top
  5. Outro          - thank-you + event info + partners

Full-bleed "DROP YOUR VIDEO HERE" images are placeholders: in Canva, drag a
video onto them to replace them.

Run:  python3 build_templates.py
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Pt

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "templates")

W, H = 1080, 1920

NAVY = "0A1A3F"
NAVY_DEEP = "050D24"
GOLD = "E3A53B"
ORANGE = "F08A24"
GREEN = "2E9E4F"
RED = "D8342B"
SKY = "3FA9F5"
WHITE = "FFFFFF"
SOFT = "C9D3EA"

FONT_HEAD = "Montserrat"
FONT_BODY = "Montserrat"

EVENT = "16TH AFRICAN ECONOMIC SUMMIT"
THEME = "SCALING STRATEGIC AND GLOBAL PARTNERSHIPS"
DATES = "30 SEPT – 03 OCT 2026"
VENUE = "METRO TORONTO CONVENTION CENTRE"
PARTNERS = "Scotiabank  ·  Toronto Metropolitan University  ·  Carleton University  ·  City of Toronto  ·  Canada"
HASHTAGS = "#AES2026   #FriendsOfAfrica   @friendsofafricafoa"


def px(v):
    return Emu(int(round(v * 9525)))


def pt(px_size):
    return Pt(px_size * 0.75)


def rgb(hex_):
    return RGBColor.from_string(hex_)


def hex_to_tuple(hex_, a=255):
    return tuple(int(hex_[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


# ---------------------------------------------------------------- raster assets

def _font(size, bold=True):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)


def make_glow_background(path, accent):
    """Deep navy background with a warm glow and a subtle dot grid."""
    img = Image.new("RGB", (W, H), hex_to_tuple(NAVY_DEEP)[:3])
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((W * 0.25, H * 0.30, W * 1.45, H * 0.80), fill=hex_to_tuple(accent, 150))
    g.ellipse((-W * 0.5, -H * 0.15, W * 0.55, H * 0.35), fill=hex_to_tuple("1D3F8F", 170))
    glow = glow.filter(ImageFilter.GaussianBlur(220))
    img.paste(glow, (0, 0), glow)
    d = ImageDraw.Draw(img)
    for y in range(40, H, 48):
        for x in range(40, W, 48):
            d.ellipse((x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=(40, 58, 100))
    img.save(path, quality=92)


def make_video_placeholder(path, accent):
    """Full-bleed stand-in that the team replaces with their footage."""
    img = Image.new("RGB", (W, H), (22, 30, 52))
    d = ImageDraw.Draw(img)
    for i in range(0, W + H, 60):
        d.line([(i, 0), (i - H, H)], fill=(28, 38, 64), width=18)
    cx, cy, r = W // 2, int(H * 0.42), 110
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=hex_to_tuple(accent)[:3], width=8)
    tri = [(cx - 35, cy - 55), (cx - 35, cy + 55), (cx + 60, cy)]
    d.polygon(tri, fill=hex_to_tuple(accent)[:3])
    for text, size, dy, col in (
        ("DROP YOUR VIDEO HERE", 52, 170, (255, 255, 255)),
        ("Drag a video from Uploads onto this image", 30, 245, (170, 182, 210)),
    ):
        f = _font(size, bold=size > 40)
        w = d.textlength(text, font=f)
        d.text((cx - w / 2, cy + dy), text, font=f, fill=col)
    img.save(path, quality=90)


def make_bottom_fade(path, height_ratio=0.55, strength=235):
    """Transparent-to-navy gradient so captions stay readable on any footage."""
    h = int(H * height_ratio)
    img = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    base = hex_to_tuple(NAVY_DEEP)[:3]
    px_ = img.load()
    for y in range(h):
        a = int(strength * (y / h) ** 1.6)
        for x in range(W):
            px_[x, y] = base + (a,)
    img.save(path)


def make_top_fade(path, height_ratio=0.40, strength=225):
    h = int(H * height_ratio)
    img = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    base = hex_to_tuple(NAVY_DEEP)[:3]
    px_ = img.load()
    for y in range(h):
        a = int(strength * (1 - y / h) ** 1.6)
        for x in range(W):
            px_[x, y] = base + (a,)
    img.save(path)


# ---------------------------------------------------------------- pptx helpers

def add_rect(slide, x, y, w, h, color, shape=MSO_SHAPE.RECTANGLE, rot=0, line=None):
    s = slide.shapes.add_shape(shape, px(x), px(y), px(w), px(h))
    if color:
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(color)
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = rgb(line[0])
        s.line.width = px(line[1])
    else:
        s.line.fill.background()
    s.rotation = rot
    s.shadow.inherit = False
    return s


def add_text(slide, x, y, w, h, text, size, color=WHITE, bold=False, align=PP_ALIGN.LEFT,
             font=FONT_BODY, anchor=MSO_ANCHOR.TOP, spacing=None, line_spacing=None):
    tb = slide.shapes.add_textbox(px(x), px(y), px(w), px(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    lines = text if isinstance(text, list) else [text]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if line_spacing:
            p.line_spacing = line_spacing
        r = p.add_run()
        r.text = line
        r.font.size = pt(size)
        r.font.bold = bold
        r.font.name = font
        r.font.color.rgb = rgb(color)
        if spacing is not None:
            rPr = r._r.get_or_add_rPr()
            rPr.set("spc", str(int(spacing * 100)))
    return tb


def add_image(slide, path, x=0, y=0, w=W, h=H):
    return slide.shapes.add_picture(path, px(x), px(y), px(w), px(h))


def pattern_band(slide, y, accent, size=34, gap=14):
    """Row of diamonds echoing the textile pattern used on the event flyer."""
    step = size + gap
    n = int(W / step) + 1
    colors = [accent, WHITE, accent, GREEN]
    for i in range(n):
        cx = i * step + step / 2
        col = colors[i % len(colors)]
        add_rect(slide, cx - size / 2, y, size, size, None if i % 2 else col,
                 MSO_SHAPE.DIAMOND, line=(col, 3) if i % 2 else None)


def brand_header(slide, accent, y=90):
    add_text(slide, 70, y, 460, 60, "CASA FOUNDATION", 30, WHITE, bold=True, spacing=3)
    add_text(slide, 70, y + 42, 460, 40, "PRESENTS", 18, SOFT, spacing=6)
    add_text(slide, 550, y, 460, 60, "FRIENDS OF AFRICA", 30, WHITE, bold=True,
             align=PP_ALIGN.RIGHT, spacing=3)
    add_text(slide, 550, y + 42, 460, 40, "COALITION  ·  CANADA", 18, SOFT,
             align=PP_ALIGN.RIGHT, spacing=6)
    add_rect(slide, 70, y + 100, W - 140, 3, accent)


def corner_bug(slide, label, accent):
    """Small persistent tag shown on every footage scene."""
    add_rect(slide, 60, 90, 20, 70, accent)
    add_text(slide, 96, 88, 700, 40, "AES 2026", 30, WHITE, bold=True, spacing=4)
    add_text(slide, 96, 126, 700, 40, label, 22, accent, bold=True, spacing=4)


def event_footer(slide, accent, y):
    add_rect(slide, 70, y, 12, 12, accent, MSO_SHAPE.OVAL)
    add_text(slide, 100, y - 10, 900, 40, DATES, 30, WHITE, bold=True, spacing=2)
    add_rect(slide, 70, y + 52, 12, 12, accent, MSO_SHAPE.OVAL)
    add_text(slide, 100, y + 42, 900, 40, VENUE + ", TORONTO", 24, SOFT, spacing=2)


def fit_size(lines, max_size, width=930):
    """Largest font size (px) that keeps the longest all-caps line inside `width`."""
    longest = max(len(l) for l in lines)
    return min(max_size, int(width / (0.75 * longest)))


# ---------------------------------------------------------------- scenes

def scene_opener(prs, t, a):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_image(s, a["glow"])
    brand_header(s, t["accent"])
    add_text(s, 70, 330, 940, 40, THEME, 22, t["accent"], bold=True, spacing=5)
    add_text(s, 70, 380, 940, 200, ["16TH AFRICAN", "ECONOMIC SUMMIT"], 58, WHITE,
             bold=True, font=FONT_HEAD, line_spacing=1.0)
    add_text(s, 70, 540, 600, 40, "CANADA 2026", 26, SOFT, bold=True, spacing=8)

    add_rect(s, 70, 760, 140, 10, t["accent"])
    add_text(s, 70, 800, 960, 420, t["title_lines"], fit_size(t["title_lines"], t.get("title_size", 150)), t["accent"],
             bold=True, font=FONT_HEAD, line_spacing=0.95)
    add_text(s, 70, 1230, 940, 140, t["subtitle"], 40, WHITE, line_spacing=1.1)

    pattern_band(s, 1480, t["accent"])
    event_footer(s, t["accent"], 1620)
    add_text(s, 70, 1790, 940, 40, HASHTAGS, 22, SOFT, spacing=1)


def scene_lower_third(prs, t, a):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_image(s, a["video"])
    add_image(s, a["fade_bottom"], 0, H - int(H * 0.55), W, int(H * 0.55))
    corner_bug(s, t["bug"], t["accent"])
    add_rect(s, 70, 1400, 16, 250, t["accent"])
    add_text(s, 115, 1395, 900, 60, t["lt_kicker"], 28, t["accent"], bold=True, spacing=4)
    add_text(s, 115, 1445, 900, 160, t["lt_title"], 64, WHITE, bold=True, font=FONT_HEAD,
             line_spacing=1.0)
    add_text(s, 115, 1600, 900, 60, t["lt_sub"], 32, SOFT)
    pattern_band(s, 1790, t["accent"], size=24, gap=12)


def scene_name_card(prs, t, a):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_image(s, a["video"])
    add_image(s, a["fade_bottom"], 0, H - int(H * 0.55), W, int(H * 0.55))
    corner_bug(s, t["bug"], t["accent"])
    card_y = 1330
    add_rect(s, 60, card_y, W - 120, 420, NAVY, MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.06
    add_rect(s, 60, card_y, W - 120, 14, t["accent"])
    add_text(s, 110, card_y + 50, 860, 50, t["card_kicker"], 28, t["accent"], bold=True, spacing=5)
    add_text(s, 110, card_y + 100, 860, 130, t["card_name"], 64, WHITE, bold=True,
             font=FONT_HEAD, line_spacing=1.0)
    add_text(s, 110, card_y + 250, 860, 140, t["card_role"], 32, SOFT, line_spacing=1.15)


def scene_caption(prs, t, a):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_image(s, a["video"])
    add_image(s, a["fade_top"], 0, 0, W, int(H * 0.40))
    corner_bug(s, t["bug"], t["accent"])
    add_text(s, 70, 230, 120, 160, "“", 200, t["accent"], bold=True, font="Georgia")
    add_text(s, 70, 360, 940, 360, t["caption"], 58, WHITE, bold=True, font=FONT_HEAD,
             line_spacing=1.05)
    add_text(s, 70, 640, 940, 60, t["caption_by"], 30, t["accent"], bold=True, spacing=2)


def scene_outro(prs, t, a):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_image(s, a["glow"])
    brand_header(s, t["accent"])
    size = fit_size(t["outro_lines"], 120)
    add_text(s, 70, 300, 940, 430, t["outro_lines"], size, WHITE, bold=True, font=FONT_HEAD,
             line_spacing=0.95)
    sub_y = 300 + len(t["outro_lines"]) * size * 1.14 + 30
    add_text(s, 70, sub_y, 940, 120, t["outro_sub"], 38, t["accent"], bold=True, line_spacing=1.1)
    add_rect(s, 70, 930, 940, 3, SOFT)
    event_footer(s, t["accent"], 990)

    add_rect(s, 70, 1140, 940, 150, None, MSO_SHAPE.ROUNDED_RECTANGLE, line=(t["accent"], 3))
    add_text(s, 110, 1170, 860, 50, "CONNECT.  COLLABORATE.  CREATE IMPACT.", 30, WHITE,
             bold=True, spacing=2)
    add_text(s, 110, 1225, 860, 40, "Register & info: link in bio  ·  @friendsofafricafoa", 24, SOFT)

    pattern_band(s, 1360, t["accent"], size=26, gap=12)
    add_text(s, 70, 1450, 940, 40, "IN PARTNERSHIP WITH", 22, t["accent"], bold=True,
             align=PP_ALIGN.CENTER, spacing=6)
    add_rect(s, 60, 1510, W - 120, 200, WHITE, MSO_SHAPE.ROUNDED_RECTANGLE).adjustments[0] = 0.08
    add_text(s, 100, 1540, W - 200, 150, PARTNERS, 28, NAVY, bold=True, align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.2)
    add_text(s, 70, 1780, 940, 40, HASHTAGS, 22, SOFT, align=PP_ALIGN.CENTER, spacing=1)


# ---------------------------------------------------------------- content

TEMPLATES = [
    dict(
        slug="01-day-1", name="AES 2026 – Day 1 (Video Template)", accent=GOLD,
        title_lines=["DAY 1"], title_size=230,
        subtitle="Opening Day Highlights",
        bug="DAY 1 HIGHLIGHTS",
        lt_kicker="OPENING CEREMONY", lt_title="Add your headline here",
        lt_sub="Short description of this moment",
        card_kicker="ON STAGE", card_name="Speaker Name",
        card_role="Title, Organization",
        caption="Add a key quote or highlight from Day 1 here.",
        caption_by="— NAME, ORGANIZATION",
        outro_lines=["THAT'S A", "WRAP ON DAY 1"], outro_sub="See you tomorrow for Day 2!",
    ),
    dict(
        slug="02-job-fair", name="AES 2026 – Job Fair (Video Template)", accent=GREEN,
        title_lines=["JOB", "FAIR"], title_size=200,
        subtitle="Connecting talent with opportunity",
        bug="JOB FAIR",
        lt_kicker="CAREER OPPORTUNITIES", lt_title="Add your headline here",
        lt_sub="Recruiters, candidates, on-the-spot interviews…",
        card_kicker="HIRING PARTNER", card_name="Company Name",
        card_role="Now hiring: Role 1 · Role 2 · Role 3",
        caption="Add a testimonial from a candidate or recruiter here.",
        caption_by="— NAME, COMPANY",
        outro_lines=["YOUR NEXT", "OPPORTUNITY", "STARTS HERE"], outro_sub="Bring your CV. Meet the employers.",
    ),
    dict(
        slug="03-market-place", name="AES 2026 – Market Place (Video Template)", accent=ORANGE,
        title_lines=["MARKET", "PLACE"], title_size=180,
        subtitle="Showcase your business at FOA 2026",
        bug="MARKET PLACE",
        lt_kicker="MADE BY AFRICA", lt_title="Add your headline here",
        lt_sub="Products, exhibitors & entrepreneurs",
        card_kicker="EXHIBITOR", card_name="Business Name",
        card_role="What they offer  ·  Booth #00",
        caption="Add a quote from an exhibitor or visitor here.",
        caption_by="— NAME, BUSINESS",
        outro_lines=["SHOP.", "CONNECT.", "GROW."], outro_sub="Visit the Market Place at AES 2026",
    ),
    dict(
        slug="04-panels", name="AES 2026 – Panels (Video Template)", accent=SKY,
        title_lines=["PANEL", "SESSIONS"], title_size=170,
        subtitle="Panel topic goes here",
        bug="PANEL SESSION",
        lt_kicker="PANEL DISCUSSION", lt_title="Add the panel topic here",
        lt_sub="Moderated by Name, Organization",
        card_kicker="PANELISTS", card_name="Name 1  ·  Name 2  ·  Name 3",
        card_role="Moderator: Name, Organization",
        caption="Add a key takeaway from the panel here.",
        caption_by="— PANELIST NAME, ORGANIZATION",
        outro_lines=["THE", "CONVERSATION", "CONTINUES"], outro_sub="Join us at the next session",
    ),
    dict(
        slug="05-speakers", name="AES 2026 – Speakers (Video Template)", accent=GOLD,
        title_lines=["FEATURED", "SPEAKER"], title_size=165,
        subtitle="Dr. Speaker Name  ·  Title, Organization",
        bug="FEATURED SPEAKER",
        lt_kicker="KEYNOTE", lt_title="Speaker Name",
        lt_sub="Title, Organization",
        card_kicker="FEATURED SPEAKER", card_name="Dr. Speaker Name",
        card_role="President & CEO, Organization, Country",
        caption="Add a powerful quote from the speaker here.",
        caption_by="— SPEAKER NAME",
        outro_lines=["SHE'LL BE", "THERE.", "WILL YOU?"], outro_sub="Edit this line for each speaker",
    ),
    dict(
        slug="06-graduations-best-step", name="AES 2026 – Graduations BEST / STEP (Video Template)",
        accent=GOLD,
        title_lines=["GRADUATION"], title_size=190,
        subtitle="BEST  |  STEP  ·  Class of 2026",
        bug="GRADUATION  ·  BEST / STEP",
        lt_kicker="CLASS OF 2026", lt_title="Congratulations, graduates!",
        lt_sub="BEST / STEP Program",
        card_kicker="GRADUATE  ·  BEST", card_name="Graduate Name",
        card_role="Program: BEST / STEP  ·  Cohort 2026",
        caption="Add a message from a graduate or mentor here.",
        caption_by="— NAME, BEST / STEP GRADUATE",
        outro_lines=["CONGRATS,", "GRADUATES!"], outro_sub="BEST | STEP · Class of 2026",
    ),
]


def build():
    os.makedirs(ASSETS, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    shared = {
        "fade_bottom": os.path.join(ASSETS, "fade-bottom.png"),
        "fade_top": os.path.join(ASSETS, "fade-top.png"),
    }
    make_bottom_fade(shared["fade_bottom"])
    make_top_fade(shared["fade_top"])

    for t in TEMPLATES:
        acc = t["accent"]
        a = dict(shared)
        a["glow"] = os.path.join(ASSETS, f"bg-glow-{acc}.jpg")
        a["video"] = os.path.join(ASSETS, f"video-placeholder-{acc}.jpg")
        if not os.path.exists(a["glow"]):
            make_glow_background(a["glow"], acc)
        if not os.path.exists(a["video"]):
            make_video_placeholder(a["video"], acc)

        prs = Presentation()
        prs.slide_width, prs.slide_height = px(W), px(H)
        prs.core_properties.title = t["name"]
        for scene in (scene_opener, scene_lower_third, scene_name_card, scene_caption, scene_outro):
            scene(prs, t, a)
        out = os.path.join(OUT, f"{t['slug']}.pptx")
        prs.save(out)
        print("wrote", os.path.relpath(out, ROOT))


if __name__ == "__main__":
    build()
