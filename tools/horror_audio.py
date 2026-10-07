"""Footsteps, impacts, voices, ambience and gear sounds from openly licensed asset packs
(CDDA "CC-Sounds" soundpack and the Red Eclipse sound repository; per-file credits in the game's Sound credits).
Replaces every synthesized sound left in city_sounds.json."""
import base64, io, json, sys, wave
import numpy as np
from scipy import signal

SR = 44100
A = sys.argv[1] if len(sys.argv) > 1 else "../assets/wav2"
W1 = "../assets/wav"
rng = np.random.default_rng(9)

def load(name, d=A):
    w = wave.open(f"{d}/{name}.wav"); assert w.getframerate() == SR
    return np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32768
def lp(x, hz, o=2): b, a = signal.butter(o, hz / (SR / 2), "low"); return signal.lfilter(b, a, x)
def hp(x, hz, o=2): b, a = signal.butter(o, hz / (SR / 2), "high"); return signal.lfilter(b, a, x)
def bp(x, lo, hi, o=2): b, a = signal.butter(o, [lo / (SR / 2), hi / (SR / 2)], "band"); return signal.lfilter(b, a, x)
def norm(x, p=0.9): return x / (np.abs(x).max() + 1e-9) * p
def fades(x, fin=0.002, fout=0.02):
    x = x.copy(); a, b = int(fin * SR), int(fout * SR)
    if a: x[:a] *= np.linspace(0, 1, a)
    if b: x[-b:] *= np.linspace(1, 0, b) ** 2
    return x
def rate(x, r):
    if abs(r - 1) < 1e-3: return x
    return np.interp(np.arange(0, len(x) - 1, r), np.arange(len(x)), x)
def env_db(x, h=220):
    n = len(x) // h; e = np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1) + 1e-12); return 20 * np.log10(e)
def around_peak(x, pre=0.04, post=0.3):
    """cut a single footfall: the strongest transient, a little before it and the decay after"""
    db = env_db(hp(x, 120)); i = int(np.argmax(db)) * 220
    a = max(0, i - int(pre * SR)); return fades(x[a:a + int((pre + post) * SR)], 0.004, 0.06)
def at(x, s, T):
    o = np.zeros(int(T * SR)); i = int(s * SR); n = min(len(x), len(o) - i); o[i:i + n] += x[:n]; return o
def loop(x, cf=1.2):
    """seamless loop: crossfade the tail into the head"""
    n = int(cf * SR); w = np.linspace(0, 1, n); y = x.copy()
    y[:n] = x[:n] * w + x[-n:] * (1 - w); return y[:-n]
def varirate(x, r0, r1):
    """playback rate glides from r0 to r1 (a rising / falling whine)"""
    pos, t, out = 0.0, 0, []
    L = len(x) / ((r0 + r1) / 2)
    while pos < len(x) - 1:
        r = r0 + (r1 - r0) * min(1, t / L); i = int(pos); f = pos - i
        out.append(x[i] * (1 - f) + x[i + 1] * f); pos += r; t += 1
    return np.array(out)
def wav_b64(x):
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
    return base64.b64encode(b.getvalue()).decode()


S = {}
# barefoot steps on asphalt: slow, a little heavy, slightly too far apart
for i, k in enumerate((1, 2, 4, 9)):
    x = around_peak(load(f"walk_barefoot_{k}"), 0.03, 0.25)
    x = lp(hp(x, 60), 6000); tt_ = np.arange(len(x)) / SR; x *= np.where(tt_ < 0.04, 1, np.exp(-(tt_ - 0.04) / 0.06))
    S[f"fig_step{i}"] = norm(rate(x, 0.82), 0.85)
# breathing: real breaths, slowed and darkened until they don't sound quite human
br = load("fatigue_low")
for i, (a, b) in enumerate(((0.1, 2.0), (2.1, 4.0), (4.1, 6.1))):
    x = rate(br[int(a * SR):int(b * SR)], 0.6)
    S[f"fig_breath{i}"] = norm(fades(lp(x, 2200), 0.05, 0.3), 0.8)
# the stinger: a slam of metal, a low bell and a blast of static all at once, then a long reversed metal groan
T = 3.2
hit = at(rate(load("smash_success_metal")[:int(0.7 * SR)], 0.55), 0, T)
bell = at(fades(rate(load("church_bells")[:int(2.0 * SR)], 0.5), 0.001, 0.8), 0, T)
stat = load("static"); stat = at(norm(np.tile(stat, 2)[:int(0.9 * SR)]) * np.exp(-np.arange(int(0.9 * SR)) / SR / 0.25), 0, T)
groan = at(fades(rate(load("smash_fail_metal_3")[::-1], 0.4), 0.3, 0.6), 0.25, T)
S["fig_sting"] = norm(np.tanh(norm(hit) * 1.3 + norm(bell) * 0.9 + stat * 0.7 + norm(groan) * 0.6), 0.97)
# heartbeat: lub-dub from a boot stomp, filtered down to the chest
st = lp(rate(load("walk_t_floor_4")[:int(0.25 * SR)], 0.6), 160, 4)
S["heart"] = norm(fades(at(norm(st), 0, 0.7) + 0.7 * at(norm(st), 0.17, 0.7), 0.001, 0.1), 0.9)
# goggles shorting out
S["nv_glitch"] = norm(fades(hp(np.tile(load("static"), 2)[:int(1.6 * SR)], 400), 0.005, 0.3), 0.8)
snd = json.load(open("city_sounds.json"))
for k, v in S.items(): snd[k] = wav_b64(v)
json.dump(snd, open("city_sounds.json", "w"))
print("added", list(S))
