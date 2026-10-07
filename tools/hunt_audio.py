"""Sounds for the Hunted mode's horrors and radios, cut from the same openly licensed recordings as horror_audio.py
(CDDA "CC-Sounds" soundpack and the Red Eclipse sound repository; credits are in the game's Sound credits panel).
Run from data/ after horror_audio.py:  python3 ../tools/hunt_audio.py  (then compress_sounds.py)."""
import json, sys
import numpy as np
# borrow horror_audio's helpers (loading, filters, cutting) without running its sound list
_src = open("../tools/horror_audio.py").read(); exec(_src[:_src.index("\nS = {}")])

rng = np.random.default_rng(31)
S = {}
def ringmod(x, hz, mix=0.6):
    t = np.arange(len(x)) / SR; return x * (1 - mix) + x * np.sin(2 * np.pi * hz * t) * mix
def trem(x, hz, depth):
    t = np.arange(len(x)) / SR; return x * (1 - depth + depth * (0.5 + 0.5 * np.sin(2 * np.pi * hz * t)))
def pad(x, n): return np.pad(x, (0, max(0, n - len(x))))[:n] if n > len(x) else x

# crawlers: quick wet knuckle-and-heel taps, too many and too fast
for i, k in enumerate((3, 5, 7, 10)):
    x = around_peak(load(f"walk_barefoot_{k}"), 0.01, 0.12)
    x = hp(rate(x, 1.7), 280); t = np.arange(len(x)) / SR
    S[f"crawl_step{i}"] = norm(fades(x * np.exp(-t / 0.035), 0.001, 0.02), 0.8)
# their screech: a human scream pushed up, ring-modulated so it stops sounding human, then clipped hard
for i, k in enumerate(("", "2", "3")):
    x = load(f"re_player_death{k}")
    x = rate(x, 1.45); x = ringmod(x, 63 + i * 17, 0.7); x = hp(x, 350)
    S[f"crawl_screech{i}"] = norm(fades(np.tanh(norm(x) * 2.2), 0.002, 0.12), 0.9)
# idle: fast shallow breathing through teeth
br = load("fatigue_high")
for i, (a, b) in enumerate(((0.2, 1.4), (1.6, 2.8))):
    x = rate(br[int(a * SR):int(b * SR)], 1.35); x = bp(x, 900, 7000)
    S[f"crawl_hiss{i}"] = norm(fades(x, 0.04, 0.2), 0.7)
# the lunge and the death
x = ringmod(rate(load("re_player_pain3"), 1.3), 90, 0.6); S["crawl_lunge"] = norm(fades(np.tanh(norm(hp(x, 300)) * 1.8), 0.002, 0.08), 0.9)
x = rate(load("re_player_death4"), 0.85); g = lp(rate(load("walk_water_3")[:int(0.6 * SR)], 0.6), 900)
S["crawl_die"] = norm(fades(ringmod(x, 45, 0.5) + 0.6 * at(norm(g), 0.25, len(x) / SR), 0.002, 0.25), 0.9)

# the Still: stone dragged over asphalt, only ever heard after it has moved
for i, ks in enumerate((("_2", "_4", "_1"), ("_3", "", "_2"))):
    x = np.concatenate([rate(load(f"smash_fail_concrete{k}"), 0.45 + 0.05 * j) for j, k in enumerate(ks)]); x = lp(x, 2400)
    S[f"still_scrape{i}"] = norm(fades(x, 0.02, min(0.3, len(x) / SR / 3)), 0.85)
T = 2.2
hit = at(rate(load("smash_success_metal_1")[:int(0.8 * SR)], 0.5), 0, T)
con = at(rate(load("smash_fail_concrete_3"), 0.6), 0, T)
stat = load("static"); stat = at(norm(np.tile(stat, 2)[:int(0.7 * SR)]) * np.exp(-np.arange(int(0.7 * SR)) / SR / 0.2), 0, T)
S["still_hit"] = norm(np.tanh(norm(hit) * 1.2 + norm(con) * 0.9 + stat * 0.5), 0.95)

# wailers: a long inhale, then a scream slowed to half speed, doubled and detuned, wavering
x = load("fatigue_low")[int(0.1 * SR):int(1.9 * SR)][::-1]
S["wail_in"] = norm(fades(lp(rate(x, 0.75), 2500), 0.05, 0.25), 0.75)
sc = load("re_player_death5")
a = varirate(sc, 0.42, 0.5); b = varirate(sc, 0.44, 0.53)
c = varirate(sc[::-1], 0.36, 0.42)                      # then it keeps going, reversed and lower, as if it never has to breathe
n = max(len(a), len(b)); w = pad(a, n) + 0.8 * pad(b, n)
xf = int(0.3 * SR); w = np.concatenate([w[:-xf], w[-xf:] * np.linspace(1, 0, xf) + c[:xf] * np.linspace(0, 1, xf), c[xf:]]); n = len(w)
w = trem(hp(w, 160), 6.5, 0.35)
bell = at(fades(rate(load("church_bells")[::-1][:int(2.5 * SR)], 0.5), 0.5, 0.4), 0, n / SR)
S["wail"] = norm(fades(np.tanh(norm(w) * 1.6) + 0.25 * norm(bell), 0.08, 0.6), 0.95)

# radios: a burst of keyed static, and the reply that crackles back when a call goes through
st = np.tile(load("static"), 3)[:int(1.3 * SR)]
gate = np.repeat(rng.random(26) < 0.65, int(0.05 * SR))[:len(st)]
S["radio_tx"] = norm(fades(bp(st, 350, 3200) * pad(gate.astype(float), len(st)), 0.01, 0.1), 0.6)
ch = load("inaudible_chatter_2")[:int(1.8 * SR)]
S["radio_ok"] = norm(fades(bp(np.tanh(norm(ch) * 2.5), 400, 2800) + 0.3 * bp(st[:len(ch)], 500, 3000), 0.01, 0.2), 0.7)

snd = json.load(open("city_sounds.json"))
for k, v in S.items(): snd[k] = wav_b64(v)
json.dump(snd, open("city_sounds.json", "w"))
print("added", list(S))
