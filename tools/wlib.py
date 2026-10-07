"""Shared helpers for the first-person weapon exporters.
Local weapon space: top of the pistol grip at the origin, +Z toward the muzzle, +Y up, +X = the gun's left side."""
import math
import numpy as np
import hd_lib as H
from hd_lib import loft, tube, superquadric, sphere, extrude, rounded_rect, superellipse, place_ring, catmull, norm, rx, ry, rz, align
import knight as K
from knight import box, prism, limb, align_y_to, rot_y, rot_z


class Gun:
    def __init__(self, name):
        self.name = name
        self.parts = []           # (group, mat, geo, angle)

    def add(self, group, mat, geo, angle=32, R=None, t=(0, 0, 0)):
        self.parts.append((group, mat, geo.xform(R, t), angle))

    def export(self):
        groups, out, tri = {}, [], 0
        for g, mat, geo, ang in self.parts:
            groups.setdefault((g, mat), []).append((geo, ang))
        for (g, mat), lst in groups.items():
            Ps, Ns, Fs, o = [], [], [], 0
            for geo, ang in lst:
                P, N, UV, F = H.finalize(geo, ang)
                Ps.append(P); Ns.append(N); Fs.append(F + o); o += len(P)
            P, N, F = np.concatenate(Ps), np.concatenate(Ns), np.concatenate(Fs); tri += len(F)
            out.append(dict(weapon=self.name, group=g, mat=mat, pos=np.round(P.reshape(-1), 5).tolist(),
                            nrm=np.round(N.reshape(-1), 3).tolist(), idx=F.reshape(-1).tolist()))
        return out, tri


SIDE = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], float)     # (z,y) profile, extruded along x
def side_profile(pts_zy, width, bevel=0.002, steps=2):
    return extrude(np.asarray(pts_zy, float), width, bevel, steps, uv_scale=8).xform(SIDE)
def bx(w, h, d, r=0.0015):
    r = min(r, w / 2.2, h / 2.2)
    return extrude(rounded_rect(w, h, r, 2), d, min(r, d / 2.2) * 0.8, 1, uv_scale=8)
def ztube(z0, z1, r, n=20, x=0.0, y=0.0, cap=True):
    return tube([(x, y, z0), (x, y, (z0 + z1) / 2), (x, y, z1)], r, n, cap, 8, up=(0, 1, 0))
def xtube(x0, x1, r, n=16, y=0.0, z=0.0, cap=True):
    return tube([(x0, y, z), ((x0 + x1) / 2, y, z), (x1, y, z)], r, n, cap, 8, up=(0, 1, 0))
def zloft(profile, n=28, x=0.0, y=0.0, cap0=True, cap1=True, ry_=None, e=2.0):
    """profile: [(z, r)] or [(z, rx, ry)]"""
    rings = []
    for p in profile:
        z, a = p[0], p[1]; b = p[2] if len(p) > 2 else a
        rings.append(place_ring(superellipse(n, a, b, e), (x, y, z), (1, 0, 0), (0, 1, 0)))
    return loft(rings, cap0, cap1, uv_scale=8)
def ring(z, r0, r1, n=24, x=0.0, y=0.0):       # flat annulus facing +Z
    return loft([place_ring(superellipse(n, r, r), (x, y, z), (1, 0, 0), (0, 1, 0)) for r in (r1, r0)], uv_scale=8)
def chaikin(poly, it=1):
    P = np.asarray(poly, float)
    for _ in range(it):
        Q = []
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]
            Q += [a * 0.75 + b * 0.25, a * 0.25 + b * 0.75]
        P = np.array(Q)
    return P
SL = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], float)      # turn a bx so its depth runs along x (slots on a side face)


# ---------------------------------------------------------------- low-poly gloved hands (same style as the carbine's)
def seg(mat, a, b, r0, r1, n=6):
    limb(mat, np.asarray(a, float), np.asarray(b, float), r0, r1, n=n)
def wrap_points(center, axis, ref, radius, angs, along):
    axis = norm(axis); ref = norm(ref - axis * (ref @ axis)); side = np.cross(axis, ref)
    return [center + axis * along + (ref * math.cos(a) + side * math.sin(a)) * radius for a in angs]

def right_hand(GT, GAX, grip_r=0.031, elbow_off=(-0.15, -0.21, -0.32)):
    """right hand wrapped round a pistol grip whose top is GT and which runs along GAX. Returns (wrist, elbow)."""
    gc = GT + GAX * 0.045
    back = np.array([0, 0, -1.0]); rgt = np.array([-1.0, 0, 0])
    pdir = norm(back * 0.7 + rgt * 0.7)
    K.add("gloves", box(0.075, 0.09, 0.03), R=align_y_to(-GAX) @ rot_y(-math.pi / 4), t=gc + pdir * grip_r)
    K.add("pads", box(0.06, 0.012, 0.03), R=align_y_to(-GAX) @ rot_y(-math.pi / 4), t=gc + pdir * (grip_r + 0.017))
    for k, along in enumerate((0.012, 0.034, 0.055)):
        pts = wrap_points(gc, GAX, back, grip_r, np.radians([-100, -160, -215, -250]), along)
        for a, b in zip(pts[:-1], pts[1:]):
            seg("gloves", a, b, 0.0115 - 0.0008 * k, 0.0105 - 0.0008 * k)
    seg("gloves", GT + (-0.024, -0.028, -0.006), GT + (-0.024, -0.024, 0.028), 0.011, 0.0105)     # trigger finger, indexed along the frame
    seg("gloves", GT + (-0.024, -0.024, 0.028), GT + (-0.022, -0.018, 0.055), 0.0105, 0.009)
    seg("gloves", gc + pdir * grip_r + (0.01, 0.01, 0.0), GT + (0.026, -0.006, -0.012), 0.012, 0.011)  # thumb
    seg("gloves", GT + (0.026, -0.006, -0.012), GT + (0.024, 0.008, 0.02), 0.011, 0.0095)
    wR = GT + np.array([-0.03, 0.012, -0.085])
    seg("gloves", gc + pdir * grip_r, wR, 0.032, 0.03, n=7)
    elR = wR + np.array(elbow_off)
    seg("sleeve", wR - (wR - elR) * 0.04, elR, 0.045, 0.058, n=7)
    seg("cuff", wR - (wR - elR) * 0.02, wR - (wR - elR) * 0.12, 0.047, 0.048, n=7)
    return wR, elR

def left_hand_guard(c, r=0.034, wrist_off=(0.06, -0.055, -0.07), elbow_off=(0.2, -0.24, -0.15)):
    """left hand cupping a handguard / pump centred on c (axis along Z). Returns (wrist, elbow)."""
    zax = np.array([0, 0, 1.0]); left = np.array([1.0, 0, 0])
    pd = norm(np.array([0.6, -0.8, 0]))
    K.add("gloves", box(0.075, 0.03, 0.09), R=rot_z(-0.65), t=c + pd * (r + 0.004))
    K.add("pads", box(0.06, 0.03, 0.012), R=rot_z(-0.65), t=c + pd * (r + 0.021))
    for k, along in enumerate((0.03, 0.01, -0.01, -0.03)):
        pts = [wrap_points(c, zax, left, r_, [a_], along)[0] for r_, a_ in zip((r + 0.002, r - 0.001, r - 0.002, r - 0.003), np.radians([-50, -105, -150, -185]))]
        for a, b in zip(pts[:-1], pts[1:]):
            seg("gloves", a, b, 0.011 - (0.001 if k == 3 else 0), 0.0098 - (0.001 if k == 3 else 0))
    seg("gloves", c + pd * (r + 0.004) + (0.004, 0.012, -0.03), c + (r - 0.003, 0.012, -0.004), 0.012, 0.011)
    seg("gloves", c + (r - 0.003, 0.012, -0.004), c + (r - 0.008, 0.026, 0.034), 0.011, 0.0095)
    wL = c + np.array(wrist_off)
    seg("gloves", c + pd * (r + 0.004), wL, 0.032, 0.03, n=7)
    elL = wL + np.array(elbow_off)
    sleeve_watch(wL, elL)
    return wL, elL

def left_hand_support(GT, GAX):
    """pistol support hand: palm on the left of the grip, fingers wrapped over the right hand's fingers."""
    gc = GT + GAX * 0.05
    K.add("gloves", box(0.03, 0.085, 0.07), R=align_y_to(-GAX) @ rot_y(0.25), t=gc + np.array([0.034, 0.0, -0.008]))
    K.add("pads", box(0.012, 0.06, 0.05), R=align_y_to(-GAX) @ rot_y(0.25), t=gc + np.array([0.052, 0.0, -0.01]))
    for k, along in enumerate((-0.03, -0.01, 0.01, 0.03)):
        a = gc + GAX * along + np.array([0.032, 0.0, 0.03])
        b = gc + GAX * along + np.array([0.0, -0.004, 0.052])
        cc = gc + GAX * along + np.array([-0.03, -0.004, 0.044])
        seg("gloves", a, b, 0.0112, 0.0105); seg("gloves", b, cc, 0.0105, 0.0095)
    seg("gloves", gc + np.array([0.036, 0.02, 0.02]), GT + np.array([0.03, 0.006, 0.05]), 0.012, 0.011)   # thumb forward along the frame
    seg("gloves", GT + np.array([0.03, 0.006, 0.05]), GT + np.array([0.026, 0.008, 0.085]), 0.011, 0.0095)
    wL = gc + np.array([0.075, -0.045, -0.05])
    seg("gloves", gc + np.array([0.036, 0.0, -0.01]), wL, 0.032, 0.03, n=7)
    elL = wL + np.array([0.1, -0.3, -0.17])
    sleeve_watch(wL, elL)
    return wL, elL

def sleeve_watch(wL, elL):
    seg("sleeve", wL - (wL - elL) * 0.04, elL, 0.045, 0.058, n=7)
    seg("cuff", wL - (wL - elL) * 0.02, wL - (wL - elL) * 0.12, 0.047, 0.048, n=7)
    d = (elL - wL) / np.linalg.norm(elL - wL); wc = wL + d * 0.14
    seg("watch", wc - d * 0.012, wc + d * 0.012, 0.05, 0.05, n=8)
    us = np.cross(d, (1, 0, 0)); us /= np.linalg.norm(us)
    if us[1] < 0: us = -us
    K.add("watch", prism(8, 0.017, 0.016, 0.012), R=align_y_to(us), t=wc + us * 0.044)
    K.add("dial", prism(8, 0.012, 0.012, 0.002), R=align_y_to(us), t=wc + us * 0.056)

def take_hand_parts(weapon, group):
    by = {}
    for mat, tris in K.parts:
        by.setdefault(mat, []).append(tris)
    K.parts.clear(); K.part_bones.clear()
    return [dict(weapon=weapon, group=group, mat=mat, flat=np.round(np.concatenate(lst).reshape(-1), 5).tolist()) for mat, lst in by.items()]
