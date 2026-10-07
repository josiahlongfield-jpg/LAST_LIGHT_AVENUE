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
# ---------------------------------------------------------------- footsteps by surface
for i, k in enumerate((2, 3, 5, 7, 8, 10)):                 # boots on concrete / asphalt (InspectorJ)
    x = lp(hp(around_peak(load(f"walk_t_concrete_{k}"), 0.035, 0.3), 70), 9000)
    tt_ = np.arange(len(x)) / SR; x *= np.where(tt_ < 0.045, 1, np.exp(-(tt_ - 0.045) / 0.07))   # gate the recording hiss after the footfall
    S[f"st_con{i}"] = norm(x, 0.9)
for i, k in enumerate((2, 3, 6, 7, 9, 10)):                 # tar-and-gravel roofs (ali-6868)
    S[f"st_grav{i}"] = norm(around_peak(load(f"walk_t_gravel_{k}"), 0.03, 0.3), 0.85)
for i, k in enumerate((1, 2, 3, 4, 5)):                     # fire-escape grating and ladder rungs (GiocoSound)
    S[f"st_met{i}"] = norm(around_peak(load(f"walk_metal_{k}"), 0.03, 0.3), 0.85)
for i, k in enumerate((3, 4, 5, 7)):                        # puddles (dawidwmika)
    S[f"st_wat{i}"] = norm(around_peak(load(f"walk_water_{k}"), 0.05, 0.35), 0.8)
# landings: a heavy boot stomp, pitched down, with grit on top
S["land_con"] = norm(at(fades(rate(load("walk_t_floor_4")[:int(0.6 * SR)], 0.78)), 0, 0.8) + 0.5 * at(around_peak(load("walk_t_gravel_1"), 0.02, 0.25), 0.0, 0.8), 0.95)
S["land_met"] = norm(at(fades(rate(load("walk_metal_1"), 0.82)), 0, 0.6) + 0.35 * at(rate(around_peak(load("walk_metal_5")), 0.9), 0.05, 0.6), 0.95)
# ---------------------------------------------------------------- hits, voices, UI
for i in range(4): S[f"hurt{i}"] = norm(fades(load(f"hurt_m_{i + 1}")), 0.85)                        # micahlg
for i, k in enumerate((2, 3, 4, 5)): S[f"flesh{i}"] = norm(around_peak(load(f"unarmed_hit_flesh_{k}"), 0.01, 0.2), 0.85)
# hit marker: a padded body thud instead of a high "tink", and a heavier double thump for a kill (flesh hits by freesound user 7146007)
def thump(f0, f1, dur, tau):
    t = np.arange(int(dur * SR)) / SR; f = f1 + (f0 - f1) * np.exp(-t / 0.025)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / tau) * (1 - np.exp(-t / 0.0015))
def gate(x, keep, tau):
    t = np.arange(len(x)) / SR; return x * np.where(t < keep, 1, np.exp(-(t - keep) / tau))
pad = lp(hp(gate(around_peak(load("unarmed_hit_flesh_5"), 0.004, 0.12), 0.012, 0.025), 180), 2800)   # the punchy mids of a body blow, no top end
S["hit"] = norm(fades(at(norm(pad), 0, 0.14) + at(thump(230, 130, 0.14, 0.025), 0, 0.14) * 0.3, 0.0005, 0.03), 0.8)
pad2 = lp(hp(gate(around_peak(load("unarmed_hit_flesh_3"), 0.004, 0.18), 0.02, 0.04), 160), 2400)
pad3 = lp(hp(gate(around_peak(load("unarmed_hit_flesh_4"), 0.004, 0.18), 0.02, 0.04), 160), 2400)
S["hit_kill"] = norm(fades(at(norm(rate(pad2, 0.85)), 0, 0.32) + at(thump(180, 90, 0.22, 0.05), 0, 0.32) * 0.35
                         + at(norm(rate(pad3, 0.8)), 0.075, 0.32) * 0.7 + at(thump(160, 80, 0.2, 0.04), 0.075, 0.32) * 0.25, 0.0005, 0.05), 0.85)
# ---------------------------------------------------------------- bullets: supersonic crack from the real 5.56 recordings' leading edge, plus air
wind = load("re_ambience_wind")
for i in range(3):
    shot = load(f"556_auto_rifle_shot_0{i + 1}", W1)
    j = int(np.argmax(np.abs(shot) > 0.3 * np.abs(shot).max()))
    snap = hp(shot[j:j + int(0.03 * SR)], 2500, 4) * np.exp(-np.arange(int(0.03 * SR)) / SR / 0.006)
    air = bp(wind[int((3 + i * 4) * SR):int((3.3 + i * 4) * SR)], 800, 6000) * np.hanning(int(0.3 * SR)) ** 2
    S[f"crack{i}"] = norm(at(norm(snap), 0.06, 0.3) * 1.0 + at(norm(air), 0.0, 0.3) * 0.35, 0.85)
for i in range(4):                                           # ricochets and hits on steel (dheming), pitched up
    S[f"ric{i}"] = norm(fades(rate(load(f"smash_fail_metal_{i + 1}")[:int(0.7 * SR)], 1.55), 0.001, 0.08), 0.8)
for i in range(4):                                           # chips off concrete and asphalt (oscaraudiogeek)
    S[f"imp_con{i}"] = norm(fades(rate(load(f"smash_fail_concrete_{i + 1}" if i else "smash_fail_concrete"), 1.25), 0.001, 0.03), 0.85)
S["imp_met0"] = norm(fades(rate(load("smash_success_metal")[:int(0.45 * SR)], 1.4), 0.001, 0.1), 0.85)   # car body panels (JoelAudio)
S["imp_met1"] = norm(fades(rate(load("smash_success_metal_1")[:int(0.5 * SR)], 1.6), 0.001, 0.1), 0.85)
# ---------------------------------------------------------------- weapon raise / lower (Red Eclipse)
S["raise"] = norm(fades(load("re_weapons_switch")), 0.6)
S["lower"] = norm(fades(rate(load("re_weapons_switch"), 0.85)), 0.55)
# ---------------------------------------------------------------- gear: dropped magazine, torch, night vision
S["magdrop"] = norm(at(rate(load("smash_fail_plastic_2"), 0.82), 0, 0.5) + 0.45 * at(rate(load("smash_fail_plastic_1"), 0.9), 0.13, 0.5), 0.85)
shutter = around_peak(load("camera_shutter_1"), 0.01, 0.15)
S["torch"] = norm(rate(shutter, 1.35), 0.7)
hum = load("electric")
S["nvg_on"] = norm(at(rate(shutter, 0.85), 0, 1.4) + 0.3 * at(fades(hp(varirate(np.tile(hum, 2), 0.8, 3.2), 1500), 0.08, 0.4), 0.12, 1.4), 0.8)
S["nvg_off"] = norm(at(rate(shutter, 0.95), 0, 0.6) + 0.22 * at(fades(hp(varirate(hum[:int(0.5 * SR)], 3.0, 0.7), 900), 0.005, 0.15), 0.05, 0.6), 0.75)
# ---------------------------------------------------------------- radio calls between waves: static, a burst of chatter, a squelch
static = load("static")
for i in range(3):
    ch = load(f"inaudible_chatter_{i + 1}")
    x = at(norm(static[:int(0.25 * SR)]) * 0.5, 0, 1.5) + at(norm(bp(ch, 350, 3200)) * 0.9, 0.18, 1.5) + at(norm(static[int(0.4 * SR):int(0.6 * SR)]) * 0.45, 1.12, 1.5)
    S[f"radio{i}"] = norm(fades(x), 0.75)
# ---------------------------------------------------------------- ambience loops and distant one-shots
S["amb_wind"] = norm(loop(lp(wind, 6000)), 0.6)
S["amb_city"] = norm(loop(load("re_ambience_distant_cars")), 0.6)
S["amb_night"] = norm(loop(load("clear_night_1")[int(2 * SR):int(32 * SR)]), 0.6)
S["siren"] = norm(fades(load("police_siren"), 0.2, 0.6), 0.7)
S["alarm"] = norm(fades(np.tile(load("alarm"), 3), 0.1, 0.8), 0.7)
S["bells"] = norm(fades(load("church_bells"), 0.05, 1.5), 0.7)

snd = json.load(open("city_sounds.json"))
for k in ("step", "land", "hurt", "bodyhit", "hit", "crack", "tink", "ping", "skid", "raise", "lower", "wind", "magdrop", "nvg_on", "nvg_off", "torch", "radio", "shotfar"):
    snd.pop(k, None)
for k, v in S.items():
    assert np.isfinite(v).all(), k
    snd[k] = wav_b64(v)
json.dump(snd, open("city_sounds.json", "w"))
reel = np.concatenate([np.concatenate([v[:int(3 * SR)], np.zeros(int(0.25 * SR))]) for v in S.values()])
with wave.open("asset_reel.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(reel, -1, 1) * 32767).astype("<i2").tobytes())
print(len(S), "sounds;", "json MB", round(len(json.dumps(snd)) / 1e6, 2))
