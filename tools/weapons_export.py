"""High-detail pistol, SMG and pump shotgun for the street game, each with low-poly gloved hands
(left and right arms exported as separate groups so the reload rig can move the left arm).
Run after rifle_export.py and sniper_export.py; replaces any earlier pistol/smg/shotgun entries in weapon_hd.json."""
import json, math
import numpy as np
from wlib import *
import knight as K

def lerp3(a, b, t): return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t

# ================================================================ PISTOL (striker-fired 9mm, FDE polymer frame, black slide)
def pistol():
    g = Gun("pistol"); R_ = "rifle"; S_ = "slide"
    GT = np.array([0, -0.004, 0.0]); GAX = norm([0, -1, -0.3])
    # --- slide: rounded box with chamfered top, cocking serrations, ejection port, sights
    sl = [(-0.032, 0.002), (0.16, 0.002), (0.163, 0.006), (0.163, 0.028), (0.158, 0.034), (-0.028, 0.034), (-0.032, 0.03)]
    g.add(S_, "gun", side_profile(chaikin(sl), 0.0245, 0.003, 2), angle=40)
    for k in range(7):                                   # rear serrations, both sides
        for xs in (0.0124, -0.0124):
            g.add(S_, "rubber", bx(0.0012, 0.022, 0.0022, 0.0006), t=(xs, 0.019, -0.026 + k * 0.0045))
    for k in range(5):                                   # front serrations
        for xs in (0.0124, -0.0124):
            g.add(S_, "rubber", bx(0.0012, 0.018, 0.002, 0.0006), t=(xs, 0.02, 0.122 + k * 0.0045))
    g.add(S_, "rubber", bx(0.003, 0.012, 0.042, 0.0015), t=(-0.0115, 0.026, 0.035))      # ejection port (right side)
    g.add(S_, "hardware", bx(0.016, 0.007, 0.04, 0.002), t=(-0.002, 0.031, 0.036))       # barrel hood showing through the port
    g.add(S_, "hardware", bx(0.0022, 0.004, 0.014, 0.0008), t=(-0.0128, 0.026, 0.012))  # extractor
    g.add(S_, "gun", bx(0.018, 0.008, 0.012, 0.002), t=(0, 0.038, -0.022))               # rear sight block
    g.add(S_, "rubber", bx(0.004, 0.006, 0.013, 0.0005), t=(0, 0.041, -0.022))           # notch
    g.add(S_, "gun", bx(0.0045, 0.008, 0.008, 0.0015), t=(0, 0.038, 0.152))              # front post
    for xs in (0.0055, -0.0055):
        g.add(S_, "dial", sphere(0.0013, 8, 6), angle=None, t=(xs, 0.0385, -0.0288))     # tritium dots
    g.add(S_, "dial", sphere(0.0014, 8, 6), angle=None, t=(0, 0.0395, 0.1477))
    g.add(S_, "rubber", ring(0.1632, 0.0035, 0.0062, 20, y=0.019))                       # slide face round the muzzle
    # --- barrel crown inside the slide
    g.add(R_, "hardware", ztube(0.12, 0.162, 0.0062, 20, y=0.019, cap=False), angle=None)
    g.add(R_, "rubber", ring(0.161, 0.0, 0.0045, 16, y=0.019))
    # --- frame: dust cover with rail, trigger guard, grip with stippling, beavertail, controls
    fr = [(-0.036, 0.0), (0.16, 0.0), (0.16, -0.012), (0.075, -0.014), (0.068, -0.016), (0.0, -0.016), (-0.036, -0.004)]
    g.add(R_, "fde", side_profile(chaikin(fr), 0.027, 0.003, 2), angle=40)
    for k in range(3):                                   # accessory rail slots
        g.add(R_, "rubber", bx(0.022, 0.003, 0.004, 0.0008), t=(0, -0.0135, 0.1 + k * 0.016))
    tg = catmull([(0, -0.014, 0.005), (0, -0.04, 0.012), (0, -0.046, 0.04), (0, -0.04, 0.066), (0, -0.016, 0.07)], 6)
    g.add(R_, "fde", tube(tg, 0.0034, 8, uv_scale=8), angle=None)
    g.add(R_, "hardware", tube(catmull([(0, -0.014, 0.034), (0, -0.026, 0.036), (0, -0.034, 0.03)], 4), 0.0028, 8, uv_scale=8), angle=None)   # trigger
    g.add(R_, "rubber", bx(0.0012, 0.012, 0.0022, 0.0005), t=(0, -0.025, 0.0365))       # trigger safety blade
    g.add(R_, "fde", superquadric(0.0148, 0.058, 0.024, 0.45, 0.55, 24, 18, 8), angle=None, R=align((0, 1, 0), GAX), t=GT + GAX * 0.052)
    for k in range(6):                                   # stippled panels
        for xs in (0.0142, -0.0142):
            g.add(R_, "polymer", bx(0.0014, 0.012, 0.03, 0.002), R=align((0, 1, 0), GAX), t=GT + GAX * (0.028 + k * 0.013) + np.array([xs, 0, 0.0]))
    g.add(R_, "fde", superquadric(0.012, 0.006, 0.014, 0.6, 0.8, 12, 8), angle=None, t=(0, 0.0, -0.036))   # beavertail
    g.add(R_, "hardware", bx(0.006, 0.005, 0.012, 0.0015), t=(0.0128, -0.012, 0.012))   # mag release (left)
    g.add(R_, "hardware", bx(0.0035, 0.005, 0.028, 0.0012), t=(0.0136, -0.004, 0.052))  # slide stop lever (left)
    g.add(R_, "hardware", bx(0.003, 0.004, 0.008, 0.001), t=(0.0136, -0.006, 0.09))     # takedown lever
    g.add(R_, "hardware", xtube(-0.0138, 0.0138, 0.0018, 8, y=-0.008, z=0.098), angle=None)   # pins
    g.add(R_, "hardware", xtube(-0.0138, 0.0138, 0.0018, 8, y=-0.01, z=-0.012), angle=None)
    # --- magazine: steel body along the grip axis, flared polymer baseplate (hidden in the grip once seated)
    MAX = GAX; mtop = GT + MAX * 0.004
    body = bx(0.021, 0.112, 0.03, 0.004)
    g.add("mag", "gun", body, R=align((0, 1, 0), MAX), t=mtop + MAX * 0.056 + np.array([0, 0, 0.004]))
    g.add("mag", "polymer", bx(0.026, 0.012, 0.038, 0.004), R=align((0, 1, 0), MAX), t=mtop + MAX * 0.116 + np.array([0, 0, 0.004]))
    g.add("mag", "brass", ztube(-0.012, 0.01, 0.0045, 10, y=0.0), R=None, t=mtop + np.array([0, -0.006, 0.004]))  # top round
    out, tri = g.export()
    wR, elR = right_hand(GT, GAX, 0.028, (-0.09, -0.3, -0.18)); rpart = take_hand_parts("pistol", "armR")
    wL, elL = left_hand_support(GT, GAX); lpart = take_hand_parts("pistol", "armL")
    info = dict(muzzle=[0, 0.019, 0.165], sightY=0.042, magOut=MAX.tolist(), magDepth=0.06,
                guard=(GT + GAX * 0.05 + np.array([0.034, 0, -0.008])).tolist(), wrist=wL.tolist(), elbow=elL.tolist(),
                port=[-0.013, 0.026, 0.035], slideTravel=0.042)
    return out + rpart + lpart, tri, info

# ================================================================ SMG (roller-delayed 9mm, stamped receiver, curved mag, retractable stock)
def smg():
    g = Gun("smg"); R_ = "rifle"
    GT = np.array([0, -0.004, 0.0]); GAX = norm([0, -1, -0.26]); BY = 0.026
    # --- receiver: stamped steel tube with ribs, welded rail claws, ejection port
    g.add(R_, "gun", zloft([(-0.09, 0.0165, 0.022), (0.235, 0.0165, 0.022)], 28, y=BY + 0.004, e=2.6), angle=40)
    g.add(R_, "gun", zloft([(-0.095, 0.0155, 0.02), (-0.09, 0.0165, 0.022)], 28, y=BY + 0.004, e=2.6))
    for xs in (0.0166, -0.0166):                         # pressed stiffening ribs
        g.add(R_, "gun", bx(0.002, 0.004, 0.27, 0.0012), t=(xs, BY + 0.008, 0.07))
    g.add(R_, "rubber", bx(0.0025, 0.014, 0.05, 0.002), t=(-0.0162, BY + 0.004, 0.04))   # ejection port
    for z in (-0.04, 0.12):                              # claw-mount bases
        g.add(R_, "gun", bx(0.03, 0.006, 0.012, 0.002), t=(0, BY + 0.028, z))
    # cocking tube running forward over the barrel, with its slot and handle
    g.add(R_, "gun", ztube(0.235, 0.43, 0.0105, 20, y=BY + 0.012), angle=None)
    g.add(R_, "rubber", bx(0.003, 0.004, 0.11, 0.0012), R=rz(0.6), t=(0.0085, BY + 0.016, 0.31))      # cocking slot
    C_ = "charge"
    g.add(C_, "gun", bx(0.026, 0.006, 0.01, 0.002), R=rz(0.6), t=(0.022, BY + 0.024, 0.34))           # cocking handle, folded forward
    g.add(C_, "polymer", sphere(0.0062, 12, 8), angle=None, t=(0.034, BY + 0.031, 0.34))
    # front sight hood and post, barrel with three lugs
    g.add(R_, "gun", bx(0.012, 0.03, 0.02, 0.003), t=(0, BY + 0.03, 0.418))
    g.add(R_, "gun", zloft([(0.41, 0.014), (0.426, 0.014)], 24, y=BY + 0.05, cap0=False, cap1=False), angle=40)
    g.add(R_, "gun", ring(0.426, 0.0115, 0.014, 24, y=BY + 0.05)); g.add(R_, "gun", ring(0.41, 0.014, 0.0115, 24, y=BY + 0.05))
    g.add(R_, "gun", zloft([(0.41, 0.0116), (0.426, 0.0116)], 24, y=BY + 0.05, cap0=False, cap1=False))
    g.add(R_, "hardware", bx(0.0025, 0.012, 0.004, 0.0008), t=(0, BY + 0.044, 0.418))
    g.add(R_, "gun", ztube(0.235, 0.475, 0.0078, 18, y=BY - 0.004), angle=None)
    for a in (0, 2.09, 4.19):
        g.add(R_, "gun", bx(0.004, 0.004, 0.018, 0.001), R=rz(a), t=(math.cos(a + 1.57) * 0.0085, BY - 0.004 + math.sin(a + 1.57) * 0.0085, 0.462))
    g.add(R_, "rubber", ring(0.4752, 0.0, 0.0042, 14, y=BY - 0.004))
    # rear diopter drum
    g.add(R_, "gun", bx(0.026, 0.012, 0.02, 0.003), t=(0, BY + 0.03, -0.065))
    g.add(R_, "gun", ring(-0.058, 0.0055, 0.0125, 24, y=BY + 0.048))                    # rear aperture: a ring you look through
    g.add(R_, "gun", ring(-0.072, 0.0125, 0.0055, 24, y=BY + 0.048))
    g.add(R_, "gun", zloft([(-0.072, 0.0125), (-0.058, 0.0125)], 24, y=BY + 0.048, cap0=False, cap1=False), angle=40)
    g.add(R_, "gun", zloft([(-0.072, 0.0055), (-0.058, 0.0055)], 16, y=BY + 0.048, cap0=False, cap1=False))
    for xs in (0.0128, -0.0128):
        g.add(R_, "gun", bx(0.004, 0.014, 0.01, 0.002), t=(xs, BY + 0.054, -0.065))    # protective ears
    # --- polymer handguard (slim, ribbed)
    g.add(R_, "polymer", zloft([(0.238, 0.021, 0.022), (0.25, 0.022, 0.024), (0.38, 0.0205, 0.022), (0.395, 0.018, 0.019)], 24, y=BY - 0.008, e=2.4), angle=40)
    for z in np.arange(0.262, 0.375, 0.016):
        for xs in (0.0215, -0.0215):
            g.add(R_, "rubber", bx(0.002, 0.016, 0.004, 0.001), t=(xs, BY - 0.012, z))
    # --- lower: polymer trigger housing, grip, guard, selector, magwell and paddle
    lw = [(-0.06, 0.006), (0.09, 0.006), (0.09, -0.012), (0.06, -0.016), (-0.02, -0.016), (-0.06, -0.006)]
    g.add(R_, "polymer", side_profile(chaikin(lw), 0.03, 0.003, 2), angle=40)
    g.add(R_, "polymer", superquadric(0.0148, 0.054, 0.022, 0.5, 0.6, 24, 18, 8), angle=None, R=align((0, 1, 0), GAX), t=GT + GAX * 0.05)
    for k in range(3):
        g.add(R_, "polymer", superquadric(0.0132, 0.0045, 0.006, 0.8, 0.8, 12, 8), angle=None, R=align((0, 1, 0), GAX), t=GAX * (0.03 + k * 0.02) + np.array([0, 0, 0.02]))
    g.add(R_, "polymer", tube(catmull([(0, -0.016, 0.008), (0, -0.04, 0.016), (0, -0.044, 0.05), (0, -0.03, 0.07), (0, -0.016, 0.072)], 5), 0.0035, 8, uv_scale=8), angle=None)
    g.add(R_, "hardware", tube(catmull([(0, -0.016, 0.034), (0, -0.026, 0.036), (0, -0.034, 0.03)], 4), 0.0026, 8, uv_scale=8), angle=None)
    g.add(R_, "hardware", xtube(0.0, 0.017, 0.006, 14, y=-0.002, z=-0.022), angle=None)  # selector drum (left)
    g.add(R_, "hardware", bx(0.004, 0.012, 0.004, 0.001), R=rx(0.4), t=(0.0175, 0.002, -0.022))
    for c_, col in ((0.02, "red"), (0.03, "dial")):
        pass
    g.add(R_, "gun", bx(0.03, 0.03, 0.044, 0.003), t=(0, BY - 0.032, 0.105))           # magwell
    g.add(R_, "hardware", bx(0.022, 0.004, 0.012, 0.001), R=rx(-0.3), t=(0, -0.008, 0.078))   # paddle release
    # --- retractable stock: two rods and a rubber-faced buttplate
    for xs in (0.013, -0.013):
        g.add(R_, "gun", ztube(-0.33, -0.08, 0.0042, 10, x=xs, y=BY + 0.012), angle=None)
    g.add(R_, "gun", bx(0.034, 0.012, 0.016, 0.003), t=(0, BY + 0.012, -0.085))
    bp = [(-0.33, 0.05), (-0.345, 0.05), (-0.35, -0.065), (-0.335, -0.07), (-0.33, -0.02)]
    g.add(R_, "gun", side_profile(chaikin(bp), 0.036, 0.004, 2))
    g.add(R_, "rubber", side_profile([(-0.348, 0.048), (-0.358, 0.048), (-0.36, -0.066), (-0.35, -0.068)], 0.04, 0.004))
    g.add(R_, "hardware", bx(0.006, 0.02, 0.008, 0.002), t=(0.018, BY + 0.01, -0.3))   # sling loop
    # --- curved 30-round magazine, swept along an arc (rocked in at the front)
    path = catmull([(0, BY - 0.022, 0.104), (0, -0.05, 0.11), (0, -0.12, 0.128), (0, -0.19, 0.158)], 6)
    T = np.diff(path, axis=0); T = np.vstack([T, T[-1:]]); T /= np.linalg.norm(T, axis=1, keepdims=True)
    rings = []
    for p, tdir in zip(path, T):
        fwd = norm(np.cross(tdir, (1, 0, 0)))
        rings.append(place_ring(superellipse(16, 0.011, 0.016, 3.5), p, (1, 0, 0), fwd))
    g.add("mag", "gun", loft(rings, True, True, uv_scale=8), angle=40)
    for t_ in (0.35, 0.6, 0.85):                         # stiffening ribs down the sides
        i = int(t_ * (len(path) - 1))
        for xs in (0.0112, -0.0112):
            g.add("mag", "gun", bx(0.0016, 0.004, 0.026, 0.0008), R=align((0, 1, 0), -T[i]), t=path[i] + np.array([xs, 0, 0]))
    g.add("mag", "gun", bx(0.026, 0.008, 0.038, 0.002), R=align((0, 1, 0), -T[-1]), t=path[-1] - T[-1] * 0.002)  # floorplate
    g.add("mag", "brass", ztube(-0.01, 0.012, 0.0045, 10), t=path[0] + np.array([0, 0.004, 0.0]))
    out, tri = g.export()
    wR, elR = right_hand(GT, GAX, 0.03); rpart = take_hand_parts("smg", "armR")
    c = np.array([0, BY - 0.008, 0.31])
    wL, elL = left_hand_guard(c, 0.026); lpart = take_hand_parts("smg", "armL")
    mag_axis = norm(path[2] - path[0])
    info = dict(muzzle=[0, BY - 0.004, 0.478], sightY=BY + 0.048, magOut=mag_axis.tolist(), magDepth=0.05,
                guard=c.tolist(), wrist=wL.tolist(), elbow=elL.tolist(), port=[-0.017, BY + 0.004, 0.04],
                charge=[0.022, BY + 0.024, 0.34])
    return out + rpart + lpart, tri, info

# ================================================================ PUMP SHOTGUN (12 gauge, walnut furniture, tube magazine)
def shotgun():
    g = Gun("shotgun"); R_ = "rifle"; P_ = "pump"
    GT = np.array([0, -0.004, 0.0]); GAX = norm([0, -1, -0.32]); BY = 0.018
    # --- receiver: milled steel with rounded top, loading & ejection ports, rollmark panel
    rc = [(-0.045, 0.034), (0.17, 0.034), (0.172, 0.03), (0.172, -0.026), (0.168, -0.03), (-0.04, -0.03), (-0.048, -0.02), (-0.048, 0.026)]
    g.add(R_, "gun", side_profile(chaikin(rc), 0.034, 0.006, 3), angle=40)
    g.add(R_, "rubber", bx(0.003, 0.022, 0.06, 0.002), t=(-0.0165, 0.012, 0.075))       # ejection port (right)
    g.add(R_, "hardware", bx(0.003, 0.012, 0.05, 0.001), t=(-0.0158, 0.012, 0.075))     # bolt face visible in the port
    g.add(R_, "rubber", bx(0.026, 0.004, 0.1, 0.002), t=(0, -0.03, 0.09))                # loading port underneath
    g.add(R_, "hardware", bx(0.02, 0.003, 0.06, 0.001), t=(0, -0.0285, 0.11))           # shell lifter
    g.add(R_, "hardware", bx(0.0012, 0.012, 0.05, 0.001), t=(0.0172, 0.005, 0.07))      # rollmark plate (left)
    g.add(R_, "hardware", xtube(-0.0175, 0.0175, 0.0022, 8, y=-0.022, z=0.01), angle=None)   # trigger-plate pins
    g.add(R_, "hardware", xtube(-0.0175, 0.0175, 0.0022, 8, y=-0.022, z=0.15), angle=None)
    g.add(R_, "hardware", bx(0.006, 0.008, 0.01, 0.002), t=(0.0, -0.035, -0.008))       # action release
    # --- barrel with ventilated rib and brass bead; magazine tube, barrel clamp, knurled cap
    g.add(R_, "gun", zloft([(0.17, 0.0125), (0.2, 0.0118), (0.68, 0.0108)], 24, y=BY), angle=None)
    g.add(R_, "rubber", ring(0.6802, 0.0, 0.0093, 20, y=BY))
    g.add(R_, "gun", bx(0.008, 0.0025, 0.5, 0.001), t=(0, BY + 0.0175, 0.428))          # rib
    for z in np.arange(0.2, 0.67, 0.03):
        g.add(R_, "gun", bx(0.004, 0.006, 0.006, 0.001), t=(0, BY + 0.013, z))
    g.add(R_, "brass", sphere(0.0022, 10, 8), angle=None, t=(0, BY + 0.0215, 0.672))
    MY = BY - 0.026
    g.add(R_, "gun", ztube(0.17, 0.6, 0.0108, 20, y=MY), angle=None)
    g.add(R_, "gun", zloft([(0.6, 0.0118), (0.635, 0.0118), (0.64, 0.009)], 20, y=MY), angle=None)   # mag cap
    for k in range(10):
        a = k / 10 * 2 * math.pi
        g.add(R_, "rubber", bx(0.0016, 0.0016, 0.03, 0.0005), t=(math.cos(a) * 0.0118, MY + math.sin(a) * 0.0118, 0.617))
    g.add(R_, "gun", side_profile(chaikin([(0.57, BY + 0.012), (0.595, BY + 0.012), (0.595, MY - 0.012), (0.57, MY - 0.012)]), 0.026, 0.003))  # barrel clamp / sling mount
    g.add(R_, "hardware", xtube(-0.014, 0.014, 0.003, 10, y=MY - 0.008, z=0.583), angle=None)
    # --- pump: walnut forend with grip grooves, on twin action bars (all slide together)
    g.add(P_, "wood", zloft([(0.235, 0.0185, 0.02), (0.245, 0.0215, 0.024), (0.385, 0.0215, 0.024), (0.395, 0.0185, 0.02)], 28, y=MY - 0.002, e=2.3), angle=40)
    for z in np.arange(0.255, 0.38, 0.012):
        g.add(P_, "rubber", zloft([(z, 0.0218, 0.0243), (z + 0.003, 0.0218, 0.0243)], 28, y=MY - 0.002, cap0=False, cap1=False, e=2.3))
    for xs in (0.012, -0.012):
        g.add(P_, "gun", bx(0.003, 0.006, 0.075, 0.001), t=(xs, MY + 0.002, 0.2))
    # --- trigger group, guard and crossbolt safety
    g.add(R_, "gun", tube(catmull([(0, -0.03, 0.0), (0, -0.05, 0.01), (0, -0.054, 0.045), (0, -0.04, 0.07), (0, -0.03, 0.072)], 5), 0.0036, 8, uv_scale=8), angle=None)
    g.add(R_, "hardware", tube(catmull([(0, -0.03, 0.034), (0, -0.04, 0.036), (0, -0.048, 0.03)], 4), 0.0028, 8, uv_scale=8), angle=None)
    g.add(R_, "red", xtube(-0.019, 0.019, 0.0032, 10, y=-0.034, z=0.062), angle=None)   # crossbolt safety (red ring shows "fire")
    # --- walnut stock with pistol grip, checkering and a rubber recoil pad
    g.add(R_, "wood", superquadric(0.0158, 0.056, 0.023, 0.5, 0.6, 24, 18, 8), angle=None, R=align((0, 1, 0), GAX), t=GT + GAX * 0.048 + np.array([0, -0.006, -0.004]))
    for k in range(4):
        for xs in (0.0152, -0.0152):
            g.add(R_, "rubber", bx(0.0012, 0.012, 0.02, 0.002), R=align((0, 1, 0), GAX), t=GT + GAX * (0.03 + k * 0.014) + np.array([xs, -0.006, 0.0]))
    st = [(-0.045, 0.03), (-0.37, 0.032), (-0.375, 0.022), (-0.37, -0.1), (-0.25, -0.075), (-0.1, -0.04), (-0.05, -0.028)]
    g.add(R_, "wood", side_profile(chaikin(st, 2), 0.036, 0.006, 3), angle=40)
    g.add(R_, "rubber", side_profile(chaikin([(-0.372, 0.034), (-0.392, 0.034), (-0.392, -0.104), (-0.372, -0.102)]), 0.04, 0.006))
    for z in np.arange(-0.385, -0.374, 0.004):
        g.add(R_, "polymer", bx(0.041, 0.13, 0.0012, 0.0005), t=(0, -0.034, z))
    g.add(R_, "hardware", bx(0.004, 0.012, 0.016, 0.002), t=(0, -0.084, -0.29))          # sling swivel
    # --- one 12-gauge shell (carried in the hand when loading; also the spent hull model)
    def shell(group, origin, axis):
        Rm = align((0, 0, 1), axis)
        g.add(group, "hull", ztube(0.0, 0.056, 0.0102, 18), angle=None, R=Rm, t=origin)
        g.add(group, "brass", zloft([(-0.012, 0.0112), (0.0, 0.0112), (0.0005, 0.0104)], 18), angle=None, R=Rm, t=origin)
        g.add(group, "hardware", ring(-0.0122, 0.0, 0.0035, 12), R=Rm, t=origin)
        g.add(group, "rubber", ring(0.0562, 0.0, 0.009, 18), R=Rm, t=origin)       # crimp
    shell("mag", np.array([0, MY - 0.012, 0.075]), np.array([0, 0.15, 1.0]) / np.linalg.norm([0, 0.15, 1.0]))
    out, tri = g.export()
    wR, elR = right_hand(GT, GAX, 0.031); rpart = take_hand_parts("shotgun", "armR")
    c = np.array([0, MY - 0.002, 0.315])
    wL, elL = left_hand_guard(c, 0.029); lpart = take_hand_parts("shotgun", "armL")
    info = dict(muzzle=[0, BY, 0.685], sightY=BY + 0.024, shellAxis=(np.array([0, 0.15, 1.0]) / np.linalg.norm([0, 0.15, 1.0])).tolist(), shellPos=[0, MY - 0.012, 0.075], magDepth=0.04, guard=c.tolist(), wrist=wL.tolist(), elbow=elL.tolist(),
                port=[-0.017, 0.012, 0.075], loadPort=[0, -0.035, 0.09], pumpTravel=0.085, tubeY=MY)
    return out + rpart + lpart, tri, info


W = json.load(open("weapon_hd.json"))
W["vm"] = [e for e in W["vm"] if e.get("weapon", "carbine") in ("carbine", "sniper")]
W["mats"].update({
    "fde": dict(color=(0.42, 0.34, 0.24), metal=0.0, rough=0.75, smooth=True),
    "wood": dict(color=(0.30, 0.16, 0.07), metal=0.0, rough=0.5, smooth=True),
    "brass": dict(color=(0.78, 0.58, 0.25), metal=0.9, rough=0.3, smooth=True),
    "hull": dict(color=(0.62, 0.08, 0.06), metal=0.0, rough=0.55, smooth=True),
    "red": dict(color=(0.75, 0.08, 0.05), metal=0.0, rough=0.5, smooth=True),
})
W["arms"] = {"carbine": dict(guard=[0, 0.018, 0.30]), "sniper": dict(guard=[0, 0.012, 0.36])}
for fn in (pistol, smg, shotgun):
    out, tri, info = fn()
    name = out[0]["weapon"]
    W["vm"] += out
    W[name] = info
    print(name, "tris", tri)
json.dump(W, open("weapon_hd.json", "w"), separators=(",", ":"))
print("KB", len(json.dumps(W)) // 1024)
