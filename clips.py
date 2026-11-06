import os, random, requests


def get_clips(keywords):
    files = []
    for i, k in enumerate(keywords):
        r = requests.get("https://pixabay.com/api/videos/",
                         params={"key": os.environ["PEXELS_API_KEY"],
                                 "q": k, "per_page": 20},
                         timeout=30).json()
        hits = r.get("hits", [])
        if not hits:
            continue
        v = random.choice(hits)["videos"]
        pick = v.get("medium") or v.get("small") or v.get("tiny")
        p = f"clip{i}.mp4"
        with open(p, "wb") as f:
            f.write(requests.get(pick["url"], timeout=120).content)
        files.append(p)
    if not files:
        raise RuntimeError("No stock clips found")
    return files
