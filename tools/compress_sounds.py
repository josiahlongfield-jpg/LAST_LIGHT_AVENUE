"""Re-encode every sound in city_sounds.json (WAV) to mono MP3 so the page stays small; writes city_sounds_mp3.json."""
import base64, json, subprocess, concurrent.futures as cf
src = json.load(open("city_sounds.json"))
LOUD = ("shot_", "far_", "amb_")          # gunshots and ambience get a higher bitrate
def enc(item):
    k, v = item
    br = "128k" if k.startswith(LOUD) else "96k"
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "wav", "-i", "pipe:0", "-ac", "1", "-c:a", "libmp3lame", "-b:a", br, "-f", "mp3", "pipe:1"],
                       input=base64.b64decode(v), capture_output=True, check=True)
    return k, base64.b64encode(p.stdout).decode()
with cf.ThreadPoolExecutor(8) as ex:
    out = dict(ex.map(enc, src.items()))
json.dump(out, open("city_sounds_mp3.json", "w"))
print(len(out), "sounds; wav MB", round(len(json.dumps(src)) / 1e6, 2), "-> mp3 MB", round(len(json.dumps(out)) / 1e6, 2))
