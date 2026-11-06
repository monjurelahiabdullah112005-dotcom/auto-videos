import os, asyncio
from clips import get_clips
from script import make_script, tts
from video import dur, build_video
from final import render_final, make_cover
from upload import upload_youtube, upload_facebook


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
