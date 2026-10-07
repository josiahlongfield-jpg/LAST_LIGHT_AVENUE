"""Procedural low-poly fantasy knight.

Builds a flat-shaded mesh from simple primitives and exports:
  - knight.glb   (glTF 2.0 binary, one primitive per material)
  - knight.json  (geometry per material, for the web viewer)
Y is up, the knight faces +Z, ~2 units tall.
"""
import json, math, struct, sys
import numpy as np

MATERIALS = {
    "steel":      dict(color=(0.74, 0.77, 0.82), metal=0.85, rough=0.35),
    "steel_dark": dict(color=(0.40, 0.43, 0.49), metal=0.75, rough=0.45),
    "gold":       dict(color=(0.93, 0.70, 0.24), metal=0.9,  rough=0.3),
    "blue":       dict(color=(0.13, 0.24, 0.58), metal=0.0,  rough=0.9),
    "red":        dict(color=(0.62, 0.09, 0.11), metal=0.0,  rough=0.9),
    "leather":    dict(color=(0.34, 0.21, 0.12), metal=0.0,  rough=0.85),
    "dark":       dict(color=(0.04, 0.04, 0.06), metal=0.0,  rough=1.0),
}

parts = []  # list of (material, tris array (T,3,3))
part_bones = []  # bone name for each entry in parts (for rigging)
BONE = "root"


# ---------- geometry helpers ----------
def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

def align_y_to(v):
    """Rotation taking +Y onto direction v."""
    v = np.asarray(v, float); v = v / np.linalg.norm(v)
    y = np.array([0, 1.0, 0])
    axis = np.cross(y, v); s = np.linalg.norm(axis); c = float(np.dot(y, v))
    if s < 1e-9:
        return np.eye(3) if c > 0 else rot_x(math.pi)
    axis /= s
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + K * s + K @ K * (1 - c)

def tris_from_faces(verts, faces):
    out = []
    for f in faces:
        for i in range(1, len(f) - 1):
            out.append([verts[f[0]], verts[f[i]], verts[f[i + 1]]])
    return np.array(out, float)

def add(mat, tris, R=None, t=(0, 0, 0), scale=(1, 1, 1)):
    tris = tris * np.asarray(scale, float)
    if R is not None:
        tris = tris @ np.asarray(R).T
    tris = tris + np.asarray(t, float)
    # Every primitive here is (near) convex, so orient each triangle to face
    # away from the part's centroid: guarantees outward normals for the export.
    c = tris.reshape(-1, 3).mean(0)
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    flip = ((tris.mean(1) - c) * n).sum(1) < 0
    tris[flip] = tris[flip][:, [0, 2, 1]]
    parts.append((mat, tris))
    part_bones.append(BONE)

def prism(n, r0, r1, h, caps=True, phase=None, sx=1.0, sz=1.0):
    """n-sided frustum from y=0 (radius r0) to y=h (radius r1)."""
    if phase is None:
        phase = math.pi / n
    v = []
    for y, r in ((0, r0), (h, r1)):
        for i in range(n):
            a = phase + 2 * math.pi * i / n
            v.append((math.sin(a) * r * sx, y, math.cos(a) * r * sz))
    faces = [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    if caps:
        faces.append(list(range(n - 1, -1, -1)))
        faces.append(list(range(n, 2 * n)))
    return tris_from_faces(v, faces)

def box(w, h, d):
    x, y, z = w / 2, h / 2, d / 2
    v = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
         (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    faces = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 4, 7, 3], [1, 2, 6, 5], [3, 7, 6, 2], [0, 1, 5, 4]]
    return tris_from_faces(v, faces)

def tapered_box(w0, w1, h, d0, d1):
    """Box from y=0 (w0 x d0) to y=h (w1 x d1)."""
    v = []
    for y, w, d in ((0, w0, d0), (h, w1, d1)):
        v += [(-w / 2, y, -d / 2), (w / 2, y, -d / 2), (w / 2, y, d / 2), (-w / 2, y, d / 2)]
    faces = [[3, 2, 1, 0], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    return tris_from_faces(v, faces)

def dome(r, nlon=8, nlat=3, top=True):
    """Low-poly hemisphere (y>=0), open at the base."""
    v = [(0, r, 0)]
    for j in range(1, nlat + 1):
        phi = (math.pi / 2) * j / nlat
        for i in range(nlon):
            a = math.pi / nlon + 2 * math.pi * i / nlon
            v.append((math.sin(phi) * math.sin(a) * r, math.cos(phi) * r, math.sin(phi) * math.cos(a) * r))
    faces = [[0, 1 + i, 1 + (i + 1) % nlon] for i in range(nlon)]
    for j in range(nlat - 1):
        b0, b1 = 1 + j * nlon, 1 + (j + 1) * nlon
        for i in range(nlon):
            faces.append([b0 + i, b1 + i, b1 + (i + 1) % nlon, b0 + (i + 1) % nlon])
    if top:
        b = 1 + (nlat - 1) * nlon
        faces.append([b + i for i in range(nlon - 1, -1, -1)])
    return tris_from_faces(v, faces)

def octa(r):
    v = [(r, 0, 0), (-r, 0, 0), (0, r, 0), (0, -r, 0), (0, 0, r), (0, 0, -r)]
    faces = [[0, 2, 4], [4, 2, 1], [1, 2, 5], [5, 2, 0], [4, 3, 0], [1, 3, 4], [5, 3, 1], [0, 3, 5]]
    return tris_from_faces(v, faces)

def extrude(poly, depth, bevel=0.0):
    """Extrude a convex-ish 2D polygon (XY, CCW) along Z, centred on z=0.
    bevel>0 shrinks the front face for a chunky chamfered look."""
    n = len(poly)
    p = np.array(poly, float)
    c = p.mean(axis=0)
    front = c + (p - c) * (1 - bevel)
    v = [(x, y, -depth / 2) for x, y in p] + [(x, y, depth / 2) for x, y in front]
    faces = [list(range(n - 1, -1, -1)), list(range(n, 2 * n))]
    faces += [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    return tris_from_faces(v, faces)

def limb(mat, a, b, r0, r1, n=6, caps=True):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    add(mat, prism(n, r0, r1, np.linalg.norm(d), caps=caps), R=align_y_to(d), t=a)


# ---------- the knight ----------
def build():
    for s in (1, -1):  # s=+1 is the knight's left (+X), -1 right
        x = 0.15 * s
        # sabatons (armoured boots)
        add("steel_dark", tapered_box(0.17, 0.15, 0.16, 0.30, 0.22), t=(x, 0, 0.04))
        add("steel", tapered_box(0.12, 0.02, 0.07, 0.10, 0.04), t=(x, 0.16, 0.12))
        # greaves
        add("steel", prism(6, 0.085, 0.105, 0.34), t=(x, 0.15, 0))
        # knee cop
        add("steel", dome(0.085, 6, 2), R=rot_x(math.pi / 2), t=(x, 0.51, 0.04), scale=(1, 1, 0.7))
        add("gold", octa(0.03), t=(x, 0.51, 0.115))
        # thighs (mail)
        add("steel_dark", prism(6, 0.11, 0.13, 0.36), t=(x, 0.48, 0))

    # faulds / armoured skirt
    add("steel", prism(8, 0.29, 0.24, 0.16, sz=0.78), t=(0, 0.76, 0))
    # belt + buckle
    add("leather", prism(8, 0.255, 0.255, 0.07, sz=0.8), t=(0, 0.88, 0))
    add("gold", box(0.08, 0.07, 0.03), t=(0, 0.915, 0.215))
    # breastplate
    add("steel", prism(8, 0.24, 0.31, 0.30, sz=0.72), t=(0, 0.93, 0))
    add("steel", prism(8, 0.31, 0.2, 0.14, sz=0.72), t=(0, 1.23, 0))
    # tabard front + back (blue with gold trim)
    for zs, rot in ((1, 0), (-1, math.pi)):
        add("blue", tapered_box(0.36, 0.30, 0.78, 0.025, 0.025), R=rot_y(rot), t=(0, 0.52, 0.228 * zs))
        add("gold", tapered_box(0.38, 0.38, 0.03, 0.03, 0.03), R=rot_y(rot), t=(0, 0.52, 0.228 * zs))
    # tabard emblem: gold cross on chest
    add("gold", box(0.05, 0.22, 0.02), t=(0, 1.07, 0.245))
    add("gold", box(0.16, 0.05, 0.02), t=(0, 1.11, 0.245))

    # gorget
    add("steel_dark", prism(8, 0.16, 0.13, 0.08), t=(0, 1.36, 0))

    # great helm
    add("steel", prism(8, 0.18, 0.19, 0.25), t=(0, 1.42, 0))
    add("steel", prism(8, 0.19, 0.09, 0.10), t=(0, 1.67, 0))
    add("steel", prism(8, 0.09, 0.0, 0.03, caps=False), t=(0, 1.77, 0))
    # visor: eye slits laid flat on the three front faces of the helm
    ap = 0.186 * math.cos(math.pi / 8)
    for a in (-math.pi / 4, 0.0, math.pi / 4):
        R = rot_y(a)
        add("dark", box(0.13, 0.034, 0.02), R=R, t=R @ np.array([0, 0, ap]) + (0, 1.585, 0))
    # breathing holes on the knight's right cheek
    R = rot_y(-math.pi / 4)
    for i in range(3):
        for j in range(2):
            p = np.array([-0.02 + i * 0.03, 1.48 + j * 0.05, ap - 0.004])
            add("dark", box(0.016, 0.03, 0.02), R=R, t=R @ p)
    # gold trim: vertical strip + brow band
    add("gold", box(0.035, 0.24, 0.04), t=(0, 1.55, 0.19))
    add("gold", prism(8, 0.195, 0.195, 0.03), t=(0, 1.63, 0))
    # plume
    pts = [(0, 1.79, -0.02), (0, 1.86, -0.12), (0, 1.84, -0.24), (0, 1.74, -0.33), (0, 1.60, -0.36)]
    for i in range(len(pts) - 1):
        limb("red", pts[i], pts[i + 1], 0.06 - i * 0.008, 0.052 - i * 0.008, n=5)

    # cape (shoulders to calves, gently flared and curved)
    segs = 5
    for i in range(segs):
        t0, t1 = i / segs, (i + 1) / segs
        y0, y1 = 1.36 - 1.0 * t0, 1.36 - 1.0 * t1
        w0, w1 = 0.56 + 0.30 * t0, 0.56 + 0.30 * t1
        z0, z1 = -0.25 - 0.10 * t0 ** 1.3, -0.25 - 0.10 * t1 ** 1.3
        for k in range(4):  # 4 columns, slight fold
            u0, u1 = -0.5 + k / 4, -0.5 + (k + 1) / 4
            fold = lambda u, t: 0.035 * t * math.cos(u * math.pi * 4)
            quad = [
                (u0 * w0, y0, z0 - fold(u0, t0)), (u1 * w0, y0, z0 - fold(u1, t0)),
                (u1 * w1, y1, z1 - fold(u1, t1)), (u0 * w1, y1, z1 - fold(u0, t1)),
            ]
            q = np.array(quad)
            back = q + np.array([0, 0, -0.02])
            v = list(q) + list(back)
            f = [[0, 1, 2, 3], [7, 6, 5, 4], [0, 4, 5, 1], [2, 6, 7, 3], [1, 5, 6, 2], [3, 7, 4, 0]]
            add("red", tris_from_faces(v, f))
    add("gold", octa(0.04), t=(0.2, 1.33, -0.2))
    add("gold", octa(0.04), t=(-0.2, 1.33, -0.2))

    # arms
    for s in (1, -1):
        sh = np.array([0.34 * s, 1.30, 0.0])
        # pauldron (two layered plates + gold rim)
        add("steel", dome(0.16, 8, 3, top=False), R=rot_z(-0.35 * s), t=sh + (0.02 * s, 0.02, 0), scale=(1, 0.75, 1))
        add("steel", dome(0.135, 8, 2, top=False), R=rot_z(-0.7 * s), t=sh + (0.07 * s, -0.06, 0), scale=(1, 0.7, 1))
        add("gold", octa(0.035), t=sh + (0.02 * s, 0.15, 0))
        elbow = np.array([0.40 * s, 1.03, -0.02])
        limb("steel_dark", sh, elbow, 0.075, 0.07)
        add("steel", octa(0.075), t=elbow)

    # right arm (-X): sword hand forward
    r_elbow = np.array([-0.40, 1.03, -0.02]); r_hand = np.array([-0.40, 0.92, 0.24])
    limb("steel", r_elbow, r_hand - (0, 0, 0.05), 0.07, 0.085)
    add("steel_dark", box(0.11, 0.11, 0.12), t=r_hand)
    # sword: held upright, angled forward
    up = np.array([-0.32, 1.0, 0.28]); up /= np.linalg.norm(up)
    Rs = align_y_to(up)
    grip_base = r_hand - up * 0.11
    add("leather", prism(6, 0.025, 0.025, 0.22), R=Rs, t=grip_base)
    add("gold", octa(0.045), t=grip_base - up * 0.02)
    guard = grip_base + up * 0.22
    add("gold", box(0.32, 0.04, 0.05), R=Rs, t=guard)
    add("gold", octa(0.035), R=Rs, t=guard + Rs @ np.array([0.17, 0, 0]))
    add("gold", octa(0.035), R=Rs, t=guard + Rs @ np.array([-0.17, 0, 0]))
    # blade: flattened diamond cross-section, tapering to a point
    blade_len = 0.95
    bl = [(0.0, 0.0), (0.045, 0.0), (0.04, blade_len * 0.85), (0.0, blade_len), ]
    v, f = [], []
    # cross-section diamond at base and at 85%, point at tip
    sec = lambda w, y: [(w, y, 0), (0, y, 0.018), (-w, y, 0), (0, y, -0.018)]
    v = sec(0.062, 0) + sec(0.05, blade_len * 0.85) + [(0, blade_len, 0)]
    f = [[0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7], [3, 2, 1, 0],
         [4, 5, 8], [5, 6, 8], [6, 7, 8], [7, 4, 8]]
    add("steel", tris_from_faces(v, f), R=Rs, t=guard + up * 0.02)
    add("steel_dark", box(0.016, blade_len * 0.7, 0.04), R=Rs, t=guard + up * (0.02 + blade_len * 0.37))

    # left arm (+X): shield arm forward
    l_elbow = np.array([0.40, 1.03, -0.02]); l_hand = np.array([0.36, 0.92, 0.2])
    limb("steel", l_elbow, l_hand, 0.07, 0.085)
    add("steel_dark", box(0.11, 0.11, 0.11), t=l_hand)
    # heater shield
    shield = [(-0.24, 0.30), (0.24, 0.30), (0.235, 0.05), (0.19, -0.14), (0.11, -0.27), (0.0, -0.36),
              (-0.11, -0.27), (-0.19, -0.14), (-0.235, 0.05)]
    Rsh = rot_y(0.55) @ rot_x(-0.08)
    sc = np.array([0.48, 0.93, 0.29])
    add("leather", extrude(shield, 0.035), R=Rsh, t=sc + Rsh @ np.array([0, 0, -0.012]))
    add("gold", extrude(shield, 0.012), R=Rsh, t=sc + Rsh @ np.array([0, 0, 0.012]))
    inner = [(x * 0.86, y * 0.86 + 0.01) for x, y in shield]
    add("blue", extrude(inner, 0.012), R=Rsh, t=sc + Rsh @ np.array([0, 0, 0.022]))
    add("leather", box(0.05, 0.05, 0.14), R=Rsh, t=sc + Rsh @ np.array([-0.04, -0.01, -0.07]))
    add("gold", box(0.06, 0.46, 0.02), R=Rsh, t=sc + Rsh @ np.array([0, -0.01, 0.03]))
    add("gold", box(0.34, 0.06, 0.02), R=Rsh, t=sc + Rsh @ np.array([0, 0.09, 0.03]))
    add("gold", octa(0.05), R=Rsh, t=sc + Rsh @ np.array([0, 0.09, 0.042]), scale=(1, 1, 0.6))


def gather():
    by = {}
    for m, t in parts:
        by.setdefault(m, []).append(t)
    return {m: np.concatenate(v) for m, v in by.items()}


def face_normals(tris):
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    l = np.linalg.norm(n, axis=1, keepdims=True); l[l == 0] = 1
    return n / l


def export_glb(groups, path):
    bin_chunks, views, accessors, prims, mats = [], [], [], [], []
    offset = 0
    def push(arr, target):
        nonlocal offset
        b = arr.astype(np.float32).tobytes()
        pad = (-len(b)) % 4
        bin_chunks.append(b + b"\0" * pad)
        views.append(dict(buffer=0, byteOffset=offset, byteLength=len(b), target=target))
        offset += len(b) + pad
        return len(views) - 1
    for i, (m, tris) in enumerate(groups.items()):
        pos = tris.reshape(-1, 3)
        nrm = np.repeat(face_normals(tris), 3, axis=0)
        pv = push(pos, 34962); nv = push(nrm, 34962)
        accessors.append(dict(bufferView=pv, componentType=5126, count=len(pos), type="VEC3",
                              min=pos.min(0).tolist(), max=pos.max(0).tolist()))
        accessors.append(dict(bufferView=nv, componentType=5126, count=len(nrm), type="VEC3"))
        spec = MATERIALS[m]
        mats.append(dict(name=m, pbrMetallicRoughness=dict(
            baseColorFactor=list(spec["color"]) + [1.0], metallicFactor=spec["metal"],
            roughnessFactor=spec["rough"]), doubleSided=(m == "red")))
        prims.append(dict(attributes=dict(POSITION=2 * i, NORMAL=2 * i + 1), material=i))
    binary = b"".join(bin_chunks)
    gltf = dict(asset=dict(version="2.0", generator="Claude procedural knight"),
                scene=0, scenes=[dict(nodes=[0])], nodes=[dict(name="Knight", mesh=0)],
                meshes=[dict(name="Knight", primitives=prims)], materials=mats,
                accessors=accessors, bufferViews=views, buffers=[dict(byteLength=len(binary))])
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * ((-len(js)) % 4)
    total = 12 + 8 + len(js) + 8 + len(binary)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack("<II", len(binary), 0x004E4942)); f.write(binary)


if __name__ == "__main__":
    build()
    groups = gather()
    export_glb(groups, "knight.glb")
    data = {m: dict(color=MATERIALS[m]["color"], metal=MATERIALS[m]["metal"], rough=MATERIALS[m]["rough"],
                    pos=np.round(t.reshape(-1), 4).tolist()) for m, t in groups.items()}
    json.dump(data, open("knight.json", "w"), separators=(",", ":"))
    ntri = sum(len(t) for t in groups.values())
    allp = np.concatenate([t.reshape(-1, 3) for t in groups.values()])
    print("triangles:", ntri, "bounds:", allp.min(0).round(2), allp.max(0).round(2))
