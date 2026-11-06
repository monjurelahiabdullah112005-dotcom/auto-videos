import textwrap
from PIL import Image, ImageDraw, ImageFont
from video import run

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def render_final(lines, total):
    n = sum(len(l) for l in lines)
    t = 0.0
    flt = []
    for i, l in enumerate(lines):
        w = total * len(l) / n
        with open(f"cap{i}.txt", "w") as f:
            f.write(textwrap.fill(l, 22))
        flt.append(
            f"drawtext=fontfile={FONT}:textfile=cap{i}.txt:fontsize=64:fontcolor=white:"
            f"borderw=6:bordercolor=black:x=(w-text_w)/2:y=h*0.62:line_spacing=10:"
            f"enable='between(t,{t:.2f},{t + w:.2f})'")
        t += w
    run(["ffmpeg", "-y", "-i", "base.mp4", "-i", "voice.mp3", "-vf", ",".join(flt),
         "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast",
         "-c:a", "aac", "-shortest", "final.mp4"])


def make_cover(title):
    run(["ffmpeg", "-y", "-ss", "1", "-i", "final.mp4", "-frames:v", "1", "frame.jpg"])
    im = Image.open("frame.jpg").convert("RGB")
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 90)
    d.multiline_text((60, 400), textwrap.fill(title, 16), font=f, fill="white",
                     stroke_width=8, stroke_fill="black")
    im.save("cover.jpg")
