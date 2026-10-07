"""Sounds for the Hunted mode's horrors (husks, the Still, wailers) and radios, cut from the same openly licensed recordings as horror_audio.py
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

# husks: dead soldiers. A dying man's cry slowed right down and doubled a little out of tune, so it sounds drowned and far off
for i, k in enumerate(("", "3", "4")):
    x = load(f"re_player_death{k}"); a = rate(x, 0.45); b = rate(x, 0.41)
    w = pad(a, max(len(a), len(b))) + 0.7 * pad(b, max(len(a), len(b)))
    S[f"husk_moan{i}"] = norm(fades(trem(lp(hp(w, 90), 1600), 4.5, 0.3), 0.05, 0.4), 0.8)
# when one hears you: a shout, slowed and smeared, that trails off backwards
for i, k in enumerate(("re_player_pain3", "re_player_death2")):
    x = rate(load(k), 0.62); tail = lp(rate(x[::-1], 0.5), 1200)[: int(0.9 * SR)]
    w = np.concatenate([x, np.zeros(int(0.05 * SR))]); w = pad(w, len(w) + len(tail)); w[len(x):len(x) + len(tail)] += 0.5 * tail * np.linspace(1, 0, len(tail))
    S[f"husk_alert{i}"] = norm(fades(np.tanh(norm(hp(w, 120)) * 1.4), 0.01, 0.3), 0.85)
# rising out of a body: a long breath drawn in backwards, a low swell and a shimmer of bells run in reverse
T = 2.4
br = at(lp(rate(load("fatigue_low")[int(0.1 * SR):int(2.0 * SR)][::-1], 0.6), 1800), 0.0, T)
sw = at(lp(rate(load("re_ambience_wind")[: int(3 * SR)], 0.5), 400), 0.0, T) * np.linspace(0, 1, int(T * SR)) ** 2
bell = at(fades(rate(load("church_bells")[::-1][: int(2.2 * SR)], 0.7), 0.6, 0.3), 0.2, T)
S["husk_rise"] = norm(fades(norm(br) + 0.6 * norm(sw) + 0.18 * norm(bell), 0.3, 0.25), 0.8)
# shot dead: it breathes out and blows away
T = 2.2
ex = at(bp(rate(load("fatigue_low")[int(0.1 * SR):int(1.6 * SR)], 0.55), 120, 2500), 0.0, T)
wh = at(hp(rate(load("re_ambience_wind")[: int(2.5 * SR)], 1.3), 600), 0.1, T) * np.exp(-np.arange(int(T * SR)) / SR / 0.6)
S["husk_die"] = norm(fades(norm(ex) + 0.7 * norm(wh), 0.01, 0.4), 0.85)
# a boot dragged along the asphalt
for i, ks in enumerate((("_1", "_4"), ("_3", "_2"))):
    x = np.concatenate([rate(load(f"smash_fail_concrete{k}"), 0.6) for k in ks])
    S[f"husk_drag{i}"] = norm(fades(lp(hp(x, 80), 1800), 0.02, 0.06), 0.6)

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
for k in [k for k in snd if k.startswith("crawl_")]: del snd[k]      # the crawlers are gone; husks took their place
for k, v in S.items(): snd[k] = wav_b64(v)
json.dump(snd, open("city_sounds.json", "w"))
print("added", list(S))
