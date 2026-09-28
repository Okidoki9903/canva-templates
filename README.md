# AES 2026 – Video templates (Canva)

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

Each template has 5 scenes: **Opener → Video + lower third → Video + name card →
Video + quote/caption → Outro (event info + partners)**.

## How to use in Canva

1. Open the template, then **File → Make a copy** (keep the original clean).
2. **Upload** your clips (Uploads tab).
3. **Drag a clip onto the “DROP YOUR VIDEO HERE” image** – it replaces it and
   keeps the dark gradient and captions on top. Use *Trim* to pick the part you want.
   (The opener/outro backgrounds can be replaced by video the same way.)
4. Click any text to edit it (titles, names, quotes…).
5. Set the length of each scene with the ⏱ timing button above the timeline.
6. Add music: **Elements → Audio** (or upload your own track) and drop it on the timeline.
7. Optional: add transitions between scenes (hover between two pages → *Add transition*),
   and replace the text logos with the real CASA / FOA logo files.
8. **Share → Download → MP4 Video**.

## Rebuilding

```
pip install python-pptx pillow
python3 build_templates.py
```
