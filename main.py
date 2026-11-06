import os, json, asyncio, random, subprocess, textwrap
import requests, edge_tts
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
from clips import get_clips

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
VOICE = "en-US-AndrewNeural"


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def dur(p):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                   "format=duration", "-of", "csv=p=0", p])
    return float(out.decode().strip())


def make_script():
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.5-flash")
    angle = random.choice(["World Cup", "legendary players", "transfer records",
                           "stadiums", "unbelievable records", "weird rules",
                           "underdog stories", "goals and comebacks"])
    prompt = f"""Write an original viral YouTube Shorts script (30-40 seconds)
about a surprising, TRUE football (soccer) fact. Angle: {angle}.
Return ONLY JSON with keys:
title (max 70 chars, catchy),
lines (list of 6-8 short sentences, first one is a strong hook),
keywords (3 simple English stock-footage search terms, e.g. football stadium),
description (2 sentences),
hashtags (list of 5 strings starting with #)."""
    r = model.generate_content(prompt)
    t = r.text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(t)


async def tts(text, path):
    await edge_tts.Communicate(text, VOICE, rate="+8%").save(path)


def build_video(clips, total):
    seg = total / len(clips) + 0.1
    parts = []
    for i, c in enumerate(clips):
        o = f"seg{i}.mp4"
        run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", c, "-t", f"{seg:.2f}",
             "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
             "-an", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", o])
        parts.append(o)
    with open("list.txt", "w") as f:
        f.write("".join(f"file '{p}'\n" for p in parts))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "base.mp4"])


def render_final(lines, total):
    n = sum(len(l) for l in lines)
