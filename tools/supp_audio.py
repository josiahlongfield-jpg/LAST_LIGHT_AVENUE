"""Suppressed shots: the carbine (shot_sup0..2), the sniper (sup_s0..1) and the SMG (sup_m0..2), from assets/wav3:
  sabacky_silenced_rifle_carbine.wav   "Silenced Rifle Carabine Shot", Sabacky (freesound.org/s/769636), CC BY 4.0
  qubodup_silenced_sniper_rifle.wav    "Silenced Sniper Rifle", qubodup (freesound.org/s/182815), CC0
  delisle_suppressed_3shots.wav        De Lisle Carbine .45ACP suppressed, Pole Position Production, from the Sonniss
                                       #GameAudioGDC 2016 bundle (royalty free, no attribution required; see sonniss-gdc-license.txt).
                                       Only three trimmed shots are kept here; the bundle's raw take is not redistributed.
Run from data/:  python3 ../tools/supp_audio.py  (then compress_sounds.py)."""
import json
import numpy as np
# borrow horror_audio's helpers (loading, filters, cutting) without running its sound list
_src = open("../tools/horror_audio.py").read(); exec(_src[:_src.index("\nS = {}")])
D = "../assets/wav3"
def shots(x, L, gap=0.5, rel=-12):
    """each separate shot in a take: an onset within rel dB of the loudest, cut to L s with its tail"""
    h = 64; e = env_db(x, h); top = e.max(); out = []; last = -1e9
    for i in range(2, len(e)):
        if e[i] > top + rel and e[i] - e[i - 2] > 6 and (i - last) * h / SR > gap:
            a = max(0, i * h - 96); out.append(fades(x[a:a + int(L * SR)], 0.001, 0.15)); last = i
    return out
def level(v): return norm(v, 0.9)

S = {}
# carbine: one clean shot, and two slightly retuned copies so a burst doesn't machine-gun the same sample
c = shots(load("sabacky_silenced_rifle_carbine", D), 0.6)[0]
for i, r in enumerate([1.0, 1.04, 0.96]): S[f"shot_sup{i}"] = level(rate(c, r))
# sniper: the take's second shot (the one the player picked), with its whole echo
S["sup_s0"] = level(shots(load("qubodup_silenced_sniper_rifle", D), 1.6, gap=1.0)[0])
# SMG: three different shots of the De Lisle
for i, s in enumerate(shots(load("delisle_suppressed_3shots", D), 0.6, gap=0.5)[:3]): S[f"sup_m{i}"] = level(s)

snd = json.load(open("city_sounds.json"))
snd.pop("sup_s1", None)
for k, v in S.items(): snd[k] = wav_b64(v); print(k, round(len(v) / SR, 2), "s")
json.dump(snd, open("city_sounds.json", "w"))
