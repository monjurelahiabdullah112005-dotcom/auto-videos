import os, json, asyncio, random, subprocess, textwrap
import requests, edge_tts
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

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


def get_clips(keywords):
    h = {"Authorization": os.environ["PEXELS_API_KEY"]}
    files = []
    for i, k in enumerate(keywords):
        r = requests.get("https://api.pexels.com/videos/search", headers=h,
                         params={"query": k, "orientation": "portrait", "per_page": 10},
                         timeout=30).json()
        vids = r.get("videos", [])
        if not vids:
            continue
        v = random.choice(vids)
        vf = sorted([f for f in v["video_files"] if f.get("width") and f["width"] <= 1080],
                    key=lambda f: -f["width"])
        if not vf:
            continue
        p = f"clip{i}.mp4"
        with open(p, "wb") as f:
            f.write(requests.get(vf[0]["link"], timeout=120).content)
        files.append(p)
    if not files:
        raise RuntimeError("No stock clips found")
    return files


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


def upload_youtube(title, desc, tags):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"],
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=os.environ["YT_CLIENT_ID"],
                        client_secret=os.environ["YT_CLIENT_SECRET"])
    yt = build("youtube", "v3", credentials=creds)
    body = {"snippet": {"title": title[:90] + " #Shorts", "description": desc,
                        "tags": tags, "categoryId": "17"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    media = MediaFileUpload("final.mp4", mimetype="video/mp4", resumable=True)
    res = yt.videos().insert(part="snippet,status", body=body, media_body=media).execute()
    print("YouTube done:", res.get("id"))


def upload_facebook(title, desc):
    pid = os.environ["FB_PAGE_ID"]
    with open("final.mp4", "rb") as f:
        r = requests.post(f"https://graph.facebook.com/v21.0/{pid}/videos",
                          data={"access_token": os.environ["FB_PAGE_TOKEN"],
                                "title": title, "description": desc},
                          files={"source": f}, timeout=900)
    print("Facebook:", r.text)


def main():
    d = make_script()
    print("Title:", d["title"])
    asyncio.run(tts(" ".join(d["lines"]), "voice.mp3"))
    total = dur("voice.mp3")
    build_video(get_clips(d["keywords"]), total)
    render_final(d["lines"], total)
    make_cover(d["title"])
    desc = d["description"] + "\n\n" + " ".join(d["hashtags"])
    tags = [h.strip("#") for h in d["hashtags"]]
    if os.environ.get("YT_REFRESH_TOKEN"):
        try:
            upload_youtube(d["title"], desc, tags)
        except Exception as e:
            print("YouTube error:", e)
    if os.environ.get("FB_PAGE_TOKEN"):
        try:
            upload_facebook(d["title"], desc)
        except Exception as e:
            print("Facebook error:", e)


if __name__ == "__main__":
    main()
