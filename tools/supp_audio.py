"""Suppressed carbine shots (shot_sup0..2), cut from openly licensed recordings in assets/wav3:
  suppressed_fpa90   Astronaut77890 (freesound.org/s/714332), modified by VMSolidus, CC BY 4.0
  suppressed_carlfnf Carlfnf (freesound.org/s/690099), CC0
  suppressed_hushpup UnderlinedDesigns (freesound 188499) + DrinkingWindGames (freesound 789647), modified by Halycon, CC BY 4.0
Run from data/:  python3 ../tools/supp_audio.py  (then compress_sounds.py)."""
import json
import numpy as np
# borrow horror_audio's helpers (loading, filters, cutting) without running its sound list
_src = open("../tools/horror_audio.py").read(); exec(_src[:_src.index("\nS = {}")])
D = "../assets/wav3"
def get(n): return load(f"suppressed_{n}", f"{D}/suppressed_{n}")
def trim(x, db=-40):
    """drop leading silence so the shot lands on the trigger pull"""
    e = env_db(x, 64); i = int(np.argmax(e > e.max() + db)) * 64; return x[max(0, i - 32):]
def soft(x, k=1.6): return np.tanh(x * k) / np.tanh(k)

fpa, carl, hush = trim(get("fpa90")), trim(get("carlfnf")), trim(get("hushpup"))
S = {}
# the FPA-90 recording is the cleanest: as is, and a touch lower and darker for variety
S["shot_sup0"] = fades(norm(hp(fpa, 70)), 0.001, 0.08)
S["shot_sup1"] = fades(norm(lp(rate(hp(fpa, 70), 0.94), 5500)), 0.001, 0.08)
# Carlfnf's clip is harshly clipped: tame its top end and give it the hushpup's mechanical tail
tail = lp(hush[:int(0.55 * SR)], 4000) * 0.5
S["shot_sup2"] = fades(norm(soft(at(lp(carl, 3200), 0, 0.6) + at(tail, 0.01, 0.6))), 0.001, 0.12)

snd = json.load(open("city_sounds.json"))
for k, v in S.items(): snd[k] = wav_b64(v); print(k, round(len(v) / SR, 2), "s")
json.dump(snd, open("city_sounds.json", "w"))
