import os, json, random, edge_tts
import google.generativeai as genai

VOICE = "en-US-AndrewNeural"
MODELS = ["gemini-3.0-flash", "gemini-3-flash", "gemini-flash-latest",
          "gemini-2.5-flash-lite", "gemini-2.5-flash"]


def make_script():
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
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
    last = None
    for name in MODELS:
        try:
            r = genai.GenerativeModel(name).generate_content(prompt)
            t = r.text.strip().replace("```json", "").replace("```", "").strip()
            print("Model used:", name)
            return json.loads(t)
        except Exception as e:
            print("Model failed:", name, str(e)[:100])
            last = e
    raise last


async def tts(text, path):
    await edge_tts.Communicate(text, VOICE, rate="+8%").save(path)
