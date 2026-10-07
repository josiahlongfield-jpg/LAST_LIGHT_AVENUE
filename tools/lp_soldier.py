"""Low-poly soldier with richer colouring and accessories, in an aiming pose for the
detailed rifle. Exports bone groups for the street game.

Colour roles (resolved per soldier in the game):
  camo     - team colour with faceted shade variation (per-triangle 'shade')
  team_dk  - darker team colour (pockets, collar, cuffs)
  team     - solid team colour (helmet band, shoulder patches, armband)
  gear     - load-bearing gear colour (coyote / black / ranger green per soldier)
  gear_dk  - straps and webbing
  fixed    - everything else (skin, black, boots, metal, lens, olive...)
"""
import json, math
import numpy as np
import knight as K
from knight import box, prism, tapered_box, dome, octa, rot_x, rot_y, rot_z, align_y_to, tris_from_faces

K.parts.clear(); K.part_bones.clear()
META = []   # (role, acc) per part, parallel to K.parts
CUR = {"acc": None}

def add(role, tris, R=None, t=(0, 0, 0), scale=(1, 1, 1), acc=None):
    K.add(role, tris, R=R, t=t, scale=scale)
    META.append((role, acc if acc is not None else CUR["acc"]))

def seg(role, a, b, r0, r1, n=6, acc=None):
    a, b = np.asarray(a, float), np.asarray(b, float); d = b - a
    add(role, prism(n, r0, r1, np.linalg.norm(d)), R=align_y_to(d), t=a, acc=acc)

def ik(S, H, L1, L2, pole):
    d = H - S; dist = np.linalg.norm(d)
    dist = min(max(dist, abs(L1 - L2) + 1e-4), L1 + L2 - 1e-4)
    u = d / np.linalg.norm(d)
    a = (L1 * L1 - L2 * L2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(L1 * L1 - a * a, 0))
    w = pole - u * (pole @ u); w /= np.linalg.norm(w)
    return S + u * a + w * h

# ---------------------------------------------------------------- legs
for s in (1, -1):
    x = 0.13 * s; side = "L" if s > 0 else "R"
    K.BONE = "foot_" + side
    add("sole", tapered_box(0.15, 0.15, 0.035, 0.29, 0.29), t=(x, 0, 0.035))
    add("boots", tapered_box(0.14, 0.115, 0.11, 0.27, 0.17), t=(x, 0.035, 0.03))
    add("boots", prism(6, 0.075, 0.08, 0.12), t=(x, 0.12, 0))
    add("boots_dk", tapered_box(0.12, 0.10, 0.04, 0.09, 0.07), t=(x, 0.11, 0.115))          # toe cap
    for k in range(3):                                                                    # laces
        add("laces", box(0.07, 0.012, 0.012), t=(x, 0.13 + k * 0.035, 0.075 - k * 0.004))
    K.BONE = "shin_" + side
    add("camo", prism(7, 0.09, 0.105, 0.25), t=(x, 0.22, 0))
    add("team_dk", prism(7, 0.087, 0.09, 0.03), t=(x, 0.205, 0))                          # blousing
    add("black", tapered_box(0.13, 0.12, 0.13, 0.06, 0.05), t=(x, 0.43, 0.075))           # knee pad
    add("gear_dk", box(0.135, 0.022, 0.13), t=(x, 0.45, 0.01))                             # knee pad strap
    add("team_dk", box(0.04, 0.09, 0.06), t=(x + 0.09 * s, 0.33, 0.0), R=rot_z(0.05 * s))  # calf pocket
    K.BONE = "thigh_" + side
    add("camo", prism(7, 0.105, 0.125, 0.36), t=(x, 0.46, 0))
    add("team_dk", box(0.05, 0.15, 0.13), t=(x + 0.118 * s, 0.655, 0.0))                  # cargo pocket
    add("team_dk", box(0.055, 0.035, 0.135), t=(x + 0.12 * s, 0.735, 0.0))                 # pocket flap
    add("team", box(0.135, 0.045, 0.14), t=(x, 0.79, 0.0), acc="armband")                  # team ID band on thigh
# drop holster with pistol on the right thigh, leg strap
K.BONE = "thigh_R"
add("gear", box(0.075, 0.17, 0.11), t=(-0.255, 0.70, 0.03), R=rot_z(0.06))
add("black", box(0.045, 0.07, 0.05), t=(-0.255, 0.80, 0.0))
add("gear_dk", box(0.27, 0.025, 0.25), t=(-0.15, 0.66, 0.0))

# ---------------------------------------------------------------- hips & belt
K.BONE = "hips"
add("camo", prism(8, 0.25, 0.23, 0.15, sz=0.8), t=(0, 0.80, 0))
add("gear", prism(8, 0.258, 0.258, 0.075, sz=0.82), t=(0, 0.915, 0))
add("gear_dk", prism(8, 0.262, 0.262, 0.03, sz=0.83), t=(0, 0.938, 0))
for a, kind in ((0.75, "mag"), (1.15, "mag"), (1.7, "pouch"), (2.4, "dump"), (-2.4, "ifak"), (-1.65, "pouch")):
    R = rot_y(a)
    if kind == "mag":
        add("gear", box(0.045, 0.1, 0.04), R=R, t=R @ np.array([0, 0, 0.22]) + (0, 0.9, 0))
        add("gear_dk", box(0.047, 0.025, 0.045), R=R, t=R @ np.array([0, 0, 0.222]) + (0, 0.955, 0))
    elif kind == "dump":
        add("gear", prism(6, 0.07, 0.09, 0.14), R=R, t=R @ np.array([0, 0, 0.25]) + (0, 0.78, 0))
    elif kind == "ifak":
        add("gear", box(0.11, 0.09, 0.07), R=R, t=R @ np.array([0, 0, 0.235]) + (0, 0.89, 0))
        add("red", box(0.035, 0.035, 0.01), R=R, t=R @ np.array([0, 0, 0.272]) + (0, 0.9, 0))
    else:
        add("gear", box(0.09, 0.1, 0.06), R=R, t=R @ np.array([0, 0, 0.22]) + (0, 0.9, 0))
add("metal", box(0.07, 0.04, 0.03), t=(0, 0.95, 0.21))                                    # buckle
CUR["acc"] = "knife"
add("black", box(0.035, 0.16, 0.025), t=(0.2, 0.86, 0.1), R=rot_y(0.6) @ rot_z(-0.2))       # knife sheath on belt
add("black", prism(6, 0.016, 0.016, 0.08), t=(0.215, 0.93, 0.105), R=rot_z(-0.2))
CUR["acc"] = None

# ---------------------------------------------------------------- torso & plate carrier
K.BONE = "chest"
add("camo", prism(8, 0.22, 0.27, 0.32, sz=0.72), t=(0, 0.97, 0))
add("camo", prism(8, 0.27, 0.17, 0.12, sz=0.72), t=(0, 1.29, 0))
add("gear", tapered_box(0.36, 0.38, 0.38, 0.07, 0.07), t=(0, 0.98, 0.17))
add("gear", tapered_box(0.36, 0.38, 0.40, 0.07, 0.07), t=(0, 0.98, -0.17))
add("gear", prism(8, 0.258, 0.258, 0.2, sz=0.8), t=(0, 1.0, 0))
for y in (1.03, 1.09, 1.15):                                                               # MOLLE rows on the cummerbund
    add("gear_dk", prism(8, 0.262, 0.262, 0.018, sz=0.81), t=(0, y, 0))
for s in (1, -1):
    add("gear", box(0.09, 0.035, 0.38), t=(0.13 * s, 1.37, 0))
    add("gear_dk", box(0.1, 0.02, 0.14), t=(0.13 * s, 1.392, 0.0))                       # shoulder pads
for i in (-1, 0, 1):                                                                        # rifle mag pouches + flaps + tabs
    add("gear", box(0.105, 0.14, 0.065), t=(i * 0.115, 1.06, 0.237))
    add("gear_dk", box(0.108, 0.035, 0.07), t=(i * 0.115, 1.14, 0.238))
    add("black", box(0.03, 0.03, 0.01), t=(i * 0.115, 1.12, 0.275))
add("gear", box(0.28, 0.085, 0.045), t=(0, 1.215, 0.228))                                  # admin pouch
add("team", box(0.09, 0.03, 0.01), t=(0.07, 1.225, 0.252))                                 # name tape in team colour
add("black", box(0.04, 0.13, 0.04), t=(-0.15, 1.27, 0.215), R=rot_z(0.2))                  # tourniquet
add("red", box(0.042, 0.025, 0.042), t=(-0.159, 1.33, 0.215), R=rot_z(0.2))
add("chem", box(0.012, 0.07, 0.012), t=(0.155, 1.31, 0.225), R=rot_z(-0.3))                # chemlight
CUR["acc"] = "grenades"
for x in (-0.13, 0.13):                                                                     # frag pouches + grenades
    add("gear", box(0.07, 0.08, 0.06), t=(x * 1.4, 1.02, 0.17), R=rot_y(-x * 4))
    add("olive", octa(0.042) * np.array([1, 1.15, 1]), t=(x * 1.4, 1.1, 0.17))
    add("metal", box(0.015, 0.03, 0.04), t=(x * 1.4, 1.155, 0.17))
CUR["acc"] = None
# back: radio pouch, antenna, hydration carrier, drag handle
add("gear", box(0.3, 0.32, 0.07), t=(0, 1.12, -0.24))
add("gear_dk", box(0.16, 0.03, 0.04), t=(0, 1.31, -0.215))
add("radio", box(0.08, 0.14, 0.055), t=(0.1, 1.33, -0.245))
add("black", box(0.03, 0.025, 0.03), t=(0.12, 1.41, -0.245))
seg("black", (0.12, 1.42, -0.245), (0.16, 1.72, -0.31), 0.007, 0.004, n=4)
CUR["acc"] = "backpack"
add("gear", box(0.34, 0.38, 0.14), t=(0, 1.08, -0.33))
add("gear_dk", box(0.30, 0.10, 0.03), t=(0, 0.98, -0.41))
add("gear_dk", box(0.32, 0.06, 0.145), t=(0, 1.27, -0.33))
add("team", box(0.06, 0.04, 0.01), t=(0.1, 1.16, -0.403))
CUR["acc"] = None

# ---------------------------------------------------------------- neck & head
add("skin", prism(6, 0.065, 0.06, 0.1), t=(0, 1.38, 0.0))
add("team_dk", prism(8, 0.1, 0.085, 0.05), t=(0, 1.38, 0))
K.BONE = "head"
add("skin", prism(8, 0.095, 0.105, 0.2, sz=1.08), t=(0, 1.45, 0.01))
add("skin", tapered_box(0.15, 0.17, 0.06, 0.12, 0.15), t=(0, 1.43, 0.035))
add("skin", tapered_box(0.03, 0.02, 0.05, 0.03, 0.02), t=(0, 1.53, 0.11))
for s in (1, -1):
    add("skin", box(0.02, 0.05, 0.035), t=(0.103 * s, 1.55, 0.0))
    add("black", box(0.022, 0.012, 0.012), t=(s * 0.04, 1.585, 0.102), acc="facepaint")       # eye-black stripes
    add("black", box(0.02, 0.01, 0.01), t=(s * 0.045, 1.535, 0.1), acc="facepaint")
# balaclava variant (covers the lower face)
CUR["acc"] = "balaclava"
add("black", prism(8, 0.1, 0.108, 0.13, sz=1.1), t=(0, 1.42, 0.012))
add("black", tapered_box(0.155, 0.175, 0.07, 0.125, 0.155), t=(0, 1.425, 0.036))
CUR["acc"] = None
# eye protection
add("lens", tapered_box(0.205, 0.215, 0.045, 0.05, 0.05), t=(0, 1.555, 0.09))
add("black", box(0.215, 0.012, 0.055), t=(0, 1.604, 0.09))
add("black", box(0.21, 0.01, 0.2), t=(0, 1.585, 0.0))
# helmet with team-colour band, side rails, NVG mount, cover, counterweight
add("helmet", dome(0.155, 10, 3), t=(0, 1.61, -0.005), scale=(1, 0.95, 1.12))
add("helmet", prism(10, 0.162, 0.157, 0.05, sz=1.12), t=(0, 1.585, -0.005))
add("team", prism(10, 0.159, 0.152, 0.03, sz=1.12), t=(0, 1.64, -0.005))
add("black", box(0.07, 0.055, 0.03), t=(0, 1.665, 0.165), R=rot_x(-0.3))
for s in (1, -1):
    add("black", box(0.02, 0.03, 0.12), t=(0.148 * s, 1.625, 0.0))
    seg("black", (0.11 * s, 1.60, 0.06), (0.085 * s, 1.43, 0.06), 0.008, 0.008, n=4)
add("black", box(0.07, 0.05, 0.03), t=(0, 1.685, -0.15), R=rot_x(0.5))
add("team_dk", box(0.1, 0.02, 0.12), t=(0, 1.755, -0.02))
CUR["acc"] = "goggles"                                                                      # goggles pushed up on the helmet
add("black", prism(10, 0.162, 0.162, 0.022, sz=1.13), t=(0, 1.665, -0.005))
add("lens_goggle", tapered_box(0.15, 0.15, 0.05, 0.035, 0.03), t=(0, 1.675, 0.175), R=rot_x(-0.45))
CUR["acc"] = "nvg"                                                                          # flipped-up night vision
add("black", box(0.05, 0.045, 0.06), t=(0, 1.73, 0.17), R=rot_x(-0.9))
add("black", prism(6, 0.02, 0.02, 0.06), t=(-0.025, 1.74, 0.2), R=rot_x(-0.9))
add("black", prism(6, 0.02, 0.02, 0.06), t=(0.025, 1.74, 0.2), R=rot_x(-0.9))
CUR["acc"] = "headset"                                                                      # comms headset ear cups + boom mic
for s in (1, -1):
    add("radio", prism(8, 0.045, 0.045, 0.05), R=rot_z(s * math.pi / 2), t=(s * 0.1, 1.555, 0.0))
seg("black", (-0.12, 1.53, 0.03), (-0.06, 1.49, 0.11), 0.005, 0.005, n=4)
add("black", box(0.02, 0.015, 0.02), t=(-0.055, 1.49, 0.115))
CUR["acc"] = None

# ---------------------------------------------------------------- arms in the aiming pose (detailed rifle shouldered)
W = json.load(open("weapon_hd.json"))
RIFLE_O = np.array([-0.12, 1.36, 0.37])          # rifle local origin (top of pistol grip) in body space; rifle points +Z
HAND_R = RIFLE_O + np.array([0, -0.05, -0.02])
HAND_L = RIFLE_O + np.array([0, -0.02, 0.30])
K.BONE = "chest"
for s, hand, pole in ((-1, HAND_R, np.array([-1.0, -0.6, -0.4])), (1, HAND_L, np.array([0.8, -1.0, 0.0]))):
    sh = np.array([0.27 * s, 1.33, 0.0])
    L1, L2 = 0.29, (0.36 if s < 0 else 0.46)
    el = ik(sh, hand, L1, L2, pole)
    add("camo", dome(0.11, 8, 2), t=sh + (0.01 * s, 0, 0), scale=(1, 0.8, 1))
    seg("camo", sh, el, 0.075, 0.068, n=7)
    up = (el - sh) / np.linalg.norm(el - sh)
    out = np.array([s, 0, 0.0])
    add("team_dk", box(0.035, 0.08, 0.09), R=align_y_to(up), t=sh + (el - sh) * 0.4 + out * 0.07)     # shoulder pocket
    add("team", box(0.012, 0.045, 0.06), R=align_y_to(up), t=sh + (el - sh) * 0.4 + out * 0.09)       # team patch
    add("team", prism(7, 0.077, 0.077, 0.035), R=align_y_to(up), t=sh + (el - sh) * 0.7, acc="armband")
    add("camo", octa(0.07), t=el)
    add("black", octa(0.05), t=el + (0.02 * s, 0, -0.03))
    d = (hand - el) / np.linalg.norm(hand - el)
    wrist = hand - d * 0.05
    seg("camo", el, wrist, 0.065, 0.055, n=7)
    seg("team_dk", wrist - d * 0.03, wrist, 0.058, 0.058, n=7)                                        # cuff
    add("gloves", box(0.085, 0.10, 0.09), R=align_y_to(d), t=hand)
    add("gloves", box(0.03, 0.05, 0.03), R=align_y_to(d), t=hand + (0.03 * s * -1, 0.03, 0.02))      # thumb
    if s > 0:
        add("black", prism(8, 0.06, 0.06, 0.025), R=align_y_to(d), t=wrist - d * 0.06, acc="watch")

# ---------------------------------------------------------------- export bone groups
GROUP_OF = {"hips": "hips", "chest": "upper", "head": "head"}
for s in "LR":
    for b in ("thigh", "shin", "foot"):
        GROUP_OF[f"{b}_{s}"] = f"{b}_{s}"
PIVOT = {"hips": (0, 0.88, 0), "upper": (0, 0.95, 0), "head": (0, 1.42, 0)}
PARENT = {"hips": None, "upper": "hips", "head": "upper"}
for s, x in (("L", 0.13), ("R", -0.13)):
    PIVOT[f"thigh_{s}"] = (x, 0.82, 0); PARENT[f"thigh_{s}"] = "hips"
    PIVOT[f"shin_{s}"] = (x, 0.47, 0); PARENT[f"shin_{s}"] = f"thigh_{s}"
    PIVOT[f"foot_{s}"] = (x, 0.10, 0); PARENT[f"foot_{s}"] = f"shin_{s}"

def camo_shade(c):
    """Blotchy faceted camo: quantised smooth noise of the triangle centre."""
    v = (math.sin(c[0] * 23 + c[1] * 7) + math.sin(c[1] * 19 - c[2] * 13 + 1.3) + math.sin(c[2] * 29 + c[0] * 11 + 2.1)) / 3
    v += 0.25 * math.sin(c[0] * 61 + c[1] * 47 + c[2] * 53)
    return 0.72 if v < -0.35 else 0.88 if v < -0.05 else 1.0 if v < 0.3 else 1.14

groups = {}
for (role, tris), bone, (_, acc) in zip(K.parts, K.part_bones, META):
    g = GROUP_OF[bone]
    key = (g, role, acc)
    entry = groups.setdefault(key, {"tris": [], "shade": []})
    entry["tris"].append(tris - np.array(PIVOT[g]))
    if role == "camo":
        entry["shade"] += [camo_shade(c) for c in tris.mean(1)]
out = []
for name in PIVOT:
    par = PARENT[name]; pp = PIVOT[par] if par else (0, 0, 0)
    parts = []
    for (g, role, acc), e in groups.items():
        if g != name:
            continue
        p = dict(role=role, pos=np.round(np.concatenate(e["tris"]).reshape(-1), 4).tolist())
        if acc: p["acc"] = acc
        if e["shade"]: p["shade"] = e["shade"]
        parts.append(p)
    out.append(dict(name=name, parent=par, offset=[round(a - b, 4) for a, b in zip(PIVOT[name], pp)], parts=parts))
rifle_pos = (RIFLE_O - np.array(PIVOT["upper"])).round(4).tolist()
muzzle = (RIFLE_O + np.array(W["muzzle"]) - np.array(PIVOT["upper"])).round(4).tolist()
json.dump(dict(groups=out, rifle=rifle_pos, muzzle=muzzle), open("soldier_lp.json", "w"), separators=(",", ":"))
print("parts", len(K.parts), "tris", sum(len(t) for t in K.parts.__iter__() for t in [t[1]]),
      "accessories", sorted({a for _, a in META if a}))
