import subprocess


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def dur(p):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                   "format=duration", "-of", "csv=p=0", p])
    return float(out.decode().strip())


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
