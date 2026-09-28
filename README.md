# FOA 2026 – Video templates (Canva)

Vertical (1080×1920, 9:16) video templates for the **16th African Economic Summit**
(CASA Foundation × Friends of Africa Coalition, 30 Sept – 03 Oct 2026, Metro Toronto
Convention Centre).

| File | Section |
|---|---|
| `templates/01-day-1.pptx` | Day 1 |
| `templates/02-job-fair.pptx` | Job Fair |
| `templates/03-market-place.pptx` | Market Place |
| `templates/04-panels.pptx` | Panels |
| `templates/05-speakers.pptx` | Speakers |
| `templates/06-graduations-best-step.pptx` | Graduations (BEST / STEP) |

Each template has 6 pages: **animated intro (MP4, kinetic typography) → clip + headline →
clip + name card → clip + big statement → clean clip → animated outro (MP4)**.
The intros/outros are rendered by `motion.py` and live in `motion/`.

## How to use in Canva

1. Open the template, then **File → Make a copy**.
2. Upload your clips, then **drag each clip onto a “DROP YOUR CLIP HERE” image**.
   Video pages automatically take the clip's length; trim with *Trim*.
3. Click the texts to edit them (headline, names, statement).
4. Logos: **Brand → Logos** and drag the CASA / FOA logos onto the corner tag or the outro.
5. Add music (Elements → Audio or your own track). Cuts in the intro are on a ~120 BPM grid.
6. Duplicate clip pages as needed, then **Share → Download → MP4**.

## Rebuilding

```
pip install python-pptx pillow numpy imageio-ffmpeg
python3 motion.py && python3 build_templates.py
```
