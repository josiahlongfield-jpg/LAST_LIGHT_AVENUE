"""Build the weapon sound set from real recordings (openly licensed, see CREDITS below).

Sources are decoded to 44.1 kHz mono WAV in ASSETS (ffmpeg) from the CDDA "CC-Sounds" soundpack
(github.com/Fris0uman/CDDA-Soundpacks), which keeps per-file author + license credits.
Each clip is trimmed, faded, and where noted pitched / layered / given a street-canyon echo.
Carbine and sniper use different recordings for every action so they never sound alike.
"""
import base64, io, json, sys, wave
import numpy as np
from scipy import signal

SR = 44100
ASSETS = sys.argv[1] if len(sys.argv) > 1 else "../assets/wav"
rng = np.random.default_rng(5)


def load(name):
    w = wave.open(f"{ASSETS}/{name}.wav"); assert w.getframerate() == SR
    return np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(float) / 32768


def cut(x, a, b, fin=0.002, fout=0.012):
    y = x[int(a * SR):int(b * SR)].copy()
    n1, n2 = int(fin * SR), int(fout * SR)
    y[:n1] *= np.linspace(0, 1, n1); y[-n2:] *= np.linspace(1, 0, n2)
    return y


def rate(x, r):
    """play back at speed r (pitch and tempo together, like a tape)"""
    if abs(r - 1) < 1e-3: return x
    return np.interp(np.arange(0, len(x) - 1, r), np.arange(len(x)), x)


def lp(x, hz, o=2): b, a = signal.butter(o, hz / (SR / 2), "low"); return signal.lfilter(b, a, x)
def hp(x, hz, o=2): b, a = signal.butter(o, hz / (SR / 2), "high"); return signal.lfilter(b, a, x)
def norm(x, p=0.9): return x / (np.abs(x).max() + 1e-9) * p
def tt(d): return np.arange(int(d * SR)) / SR


def canyon(x, wet=0.2, taps=((0.011, 0.5, 6000), (0.023, 0.36, 4200), (0.037, 0.25, 3000), (0.061, 0.16, 2200), (0.089, 0.1, 1600))):
    """early reflections off the facades of the avenue"""
    out = np.concatenate([x, np.zeros(int((taps[-1][0] + 0.02) * SR))])
    for d, g, c in taps:
        i = int(d * SR); out[i:i + len(x)] += lp(x, c) * g * wet
    return out


def onset_trim(x, pre=0.004, thresh=0.05):
    i = np.argmax(np.abs(x) > thresh * np.abs(x).max())
    return x[max(0, i - int(pre * SR)):]


def fade_end(x, ms=30):
    n = int(ms / 1000 * SR); x = x.copy(); x[-n:] *= np.linspace(1, 0, n) ** 2; return x


# ---------------------------------------------------------------- firing
def carbine_shot(src):
    """5.56 recorded outdoors (Sig MCX Spear LT): tight, snappy crack"""
    x = onset_trim(load(src))[: int(0.62 * SR)]
    return norm(fade_end(canyon(x, 0.18), 60), 0.95)


def sniper_shot():
    """heavy .308: slower, deeper recording plus a low concussion and a long rolling echo down the street"""
    x = rate(onset_trim(load("rifle_1")), 0.86)
    t = tt(1.6)
    boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t / 0.05)) / SR) * np.exp(-t / 0.16)
    y = np.zeros(len(t)); y[:len(x)] += norm(x)
    y += 0.55 * boom
    for d, g, c in ((0.16, 0.32, 2400), (0.34, 0.22, 1700), (0.58, 0.13, 1200), (0.9, 0.07, 900)):
        i = int(d * SR); seg = lp(y[: len(t) - i], c) * g; y[i:] += seg
    y = np.tanh(norm(y, 1.0) * 1.4)
    return norm(fade_end(y, 200), 0.97)


def far(x, cut_hz=1700, gain=0.85):
    """distant shot: highs absorbed by distance, slap-back from the far buildings"""
    y = lp(np.concatenate([x, np.zeros(int(0.6 * SR))]), cut_hz)
    for d, g in ((0.21, 0.35), (0.47, 0.18)):
        i = int(d * SR); y[i:] += y[: len(y) - i] * g
    return norm(fade_end(y, 120), gain)


# ---------------------------------------------------------------- casings (the brass ring of an ejected .308 case hitting the floor)
def casing(src, a, b, r):
    x = hp(cut(load(src), a, b, 0.001, 0.03), 4200, 4)
    return norm(rate(x, r), 0.85)


def wav_b64(x):
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
    return base64.b64encode(b.getvalue()).decode()


if __name__ == "__main__":
    ld03 = load("bolt_action_rifle_load_03")      # IG1889: bolt back, mag out, mag in, lock, bolt forward
    bolt308 = load("brass_eject")                   # .308 bolt: lift + draw back ... push forward + lock, then the case rings
    pp04 = load("pocket_pistol_load_04")            # mag seated with the slide locked back, slide slams home
    pp02 = load("pocket_pistol_load_02")
    S = {}
    # carbine (5.56 semi-auto) ------------------------------------------------
    for i in range(3):
        S[f"shot_c{i}"] = carbine_shot(f"556_auto_rifle_shot_0{i + 1}")
    S["far_c"] = far(S["shot_c1"], 1800, 0.8)
    S["c_magout"] = norm(rate(cut(ld03, 0.47, 1.12), 1.18), 0.8)                 # lighter, quicker aluminium mag release
    S["c_magin"] = norm(canyon(rate(cut(pp04, 0.44, 0.86), 0.9), 0.15), 0.9)      # mag driven home into the well
    S["c_magin2"] = norm(canyon(rate(cut(pp02, 0.4, 0.66), 0.9), 0.15), 0.9)
    S["c_boltrel"] = norm(canyon(rate(cut(pp04, 0.95, 1.36), 0.8), 0.2), 0.95)    # bolt catch hit: carrier slams forward
    S["dry_c"] = norm(cut(load("empty_1"), 0.0, 0.17, 0.001, 0.02), 0.85)
    # sniper (.308 bolt action) ------------------------------------------------
    S["shot_s"] = sniper_shot()
    S["far_s"] = far(S["shot_s"], 1500, 0.9)
    S["s_boltopen"] = norm(cut(bolt308, 0.0, 0.40), 0.85)                          # handle up, bolt drawn back, case extracted
    S["s_boltclose"] = norm(cut(bolt308, 0.555, 0.712, 0.002, 0.008), 0.9)         # bolt run forward, handle locked down
    S["s_magout"] = norm(cut(ld03, 0.47, 1.15), 0.8)
    S["s_magin"] = norm(cut(ld03, 1.74, 2.46), 0.9)
    S["s_maglock"] = norm(cut(ld03, 2.5, 3.02), 0.85)
    S["s_reloadclose"] = norm(cut(ld03, 3.1, 3.71), 0.9)
    S["dry_s"] = norm(rate(cut(load("empty_1"), 0.0, 0.17, 0.001, 0.02), 0.82), 0.85)
    # casings: same real brass ring, pitched for case size (5.56 small and bright, .308 bigger and lower)
    S["case_c0"] = casing("brass_eject", 0.714, 0.95, 1.22)
    S["case_c1"] = casing("brass_eject_1", 1.495, 1.81, 1.32)
    S["case_c2"] = casing("brass_eject", 0.714, 0.95, 1.4)
    S["case_s0"] = casing("brass_eject", 0.714, 0.95, 0.97)
    S["case_s1"] = casing("brass_eject_1", 1.495, 1.81, 1.03)

    # pistol (9mm, M17-style) ------------------------------------------------
    pp01, pp03 = load("pocket_pistol_load_01"), load("pocket_pistol_load_03")
    S["shot_p"] = norm(fade_end(canyon(onset_trim(load("handgun_1"))[: int(0.55 * SR)], 0.2), 80), 0.92)
    S["far_p"] = far(S["shot_p"], 1900, 0.7)
    S["p_magout"] = norm(hp(rate(cut(ld03, 0.47, 1.0), 1.42), 300), 0.75)          # small polymer pistol mag sliding out of the grip
    S["p_magin"] = norm(canyon(cut(pp01, 0.05, 0.55), 0.12), 0.9)                 # mag pushed home and clicked into the catch
    S["p_slide"] = norm(canyon(cut(pp01, 0.66, 1.03), 0.15), 0.9)                 # slide racked / released home
    S["p_slide2"] = norm(canyon(cut(pp03, 1.5, 1.84), 0.15), 0.9)
    S["dry_p"] = norm(cut(load("empty"), 0.0, 0.3, 0.001, 0.03), 0.8)
    # SMG (9mm, roller-delayed) ----------------------------------------------
    ld02, ld04 = load("bolt_action_rifle_load_02"), load("bolt_action_rifle_load_04")
    mg = onset_trim(load("machinegun_1"))
    S["shot_m0"] = norm(fade_end(canyon(rate(mg[: int(0.42 * SR)], 1.12), 0.15), 70), 0.9)
    S["shot_m1"] = norm(fade_end(canyon(rate(mg[: int(0.42 * SR)], 1.2), 0.15), 70), 0.9)
    S["far_m"] = far(S["shot_m0"], 1800, 0.75)
    S["m_magout"] = norm(rate(cut(ld02, 0.0, 0.34), 1.22), 0.8)                   # curved steel mag rocked out of the well
    S["m_magin"] = norm(canyon(rate(cut(ld04, 1.36, 1.78), 1.15), 0.15), 0.9)     # rocked in, clicks home
    S["m_charge"] = norm(canyon(rate(cut(ld04, 2.14, 2.74), 1.25), 0.18), 0.95)   # cocking handle pulled and slapped down
    S["dry_m"] = norm(rate(cut(load("empty_1"), 0.0, 0.17, 0.001, 0.02), 1.12), 0.85)
    # pump shotgun (12 gauge) ---------------------------------------------------
    sg = onset_trim(load("shotgun_1"))
    S["shot_g"] = norm(fade_end(canyon(sg[: int(1.25 * SR)], 0.22), 250), 0.97)
    S["far_g"] = far(S["shot_g"], 1400, 0.85)
    ck = load("default")                                                          # "chik-chak": slide back, slide forward
    S["g_pumpback"] = norm(rate(cut(ck, 0.14, 0.5), 0.86), 0.9)
    S["g_pumpfwd"] = norm(rate(cut(ck, 0.5, 1.05), 0.86), 0.9)
    for i, (f, on) in enumerate((("shell_load_01", 0.16), ("shell_load_02", 0.51), ("shell_load_03", 0.69), ("shell_load_04", 0.65))):
        S[f"g_shell{i}"] = norm(canyon(cut(load(f), on - 0.14, on + 0.2), 0.1), 0.85)   # shell thumbed past the carrier into the tube
    S["dry_g"] = norm(rate(cut(load("empty_1"), 0.0, 0.17, 0.001, 0.02), 0.7), 0.85)
    # casings: 9mm brass (small, bright) and plastic shotgun hulls (dull, hollow)
    S["case_p0"] = casing("brass_eject", 0.714, 0.95, 1.55)
    S["case_p1"] = casing("brass_eject_1", 1.495, 1.81, 1.62)
    for i, (src, a, b) in enumerate((("brass_eject", 0.714, 0.95), ("brass_eject_1", 1.495, 1.81))):
        x = cut(load(src), a, b, 0.001, 0.03)
        S[f"case_g{i}"] = norm(lp(hp(rate(x, 0.55), 250), 2600), 0.8)
    snd = json.load(open("city_sounds.json"))
    for k in [k for k in snd if k.startswith(("c_", "s_", "brass")) or k in ("shot", "dry", "bolt", "magout", "magin")]:
        del snd[k]                                     # retire the synthesized versions these replace
    for k, v in S.items():
        assert np.isfinite(v).all(); snd[k] = wav_b64(v)
    json.dump(snd, open("city_sounds.json", "w"))
    reel = np.concatenate([np.concatenate([v, np.zeros(int(0.3 * SR))]) for v in S.values()])
    with wave.open("real_reel.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(reel, -1, 1) * 32767).astype("<i2").tobytes())
    print({k: round(len(v) / SR, 2) for k, v in S.items()})
    print("sounds json KB", len(json.dumps(snd)) // 1024)
