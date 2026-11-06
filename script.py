import os, json, random, edge_tts
import google.generativeai as genai

VOICE = "en-US-AndrewNeural"


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
