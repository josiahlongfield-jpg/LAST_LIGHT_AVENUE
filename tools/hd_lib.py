"""High-detail procedural modelling toolkit: smooth lofts, superquadrics, bevelled
extrusions, tubes, auto-smoothed normals, world-scale UVs, generated textures and
glTF (GLB) export with embedded PNG textures."""
import io, json, math, struct
import numpy as np
from PIL import Image, ImageFilter

TAU = 2 * math.pi

# ------------------------------------------------------------------ small math
def norm(v):
    v = np.asarray(v, float); n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.where(n == 0, 1, n)

def rx(a):
    c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def ry(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def rz(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

def look_frame(f, up=(0, 1, 0)):
    """Rotation whose local +Z = f and local +Y close to `up`."""
    f = norm(f); x = np.cross(up, f)
    if np.linalg.norm(x) < 1e-6:
        x = np.cross((1, 0, 0), f)
    x = norm(x); y = np.cross(f, x)
    return np.column_stack([x, y, f])

def align(a, b):
    """Smallest rotation taking direction a onto b."""
    a, b = norm(a), norm(b); v = np.cross(a, b); s = np.linalg.norm(v); c = float(a @ b)
    if s < 1e-9:
        return np.eye(3) if c > 0 else rx(math.pi)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)

def spow(w, e):
    return np.sign(w) * np.abs(w) ** e

# ------------------------------------------------------------------ geometry container
class Geo:
    """Vertices P (N,3), UVs (N,2), triangle indices F (M,3)."""
    def __init__(self, P, UV, F):
        self.P = np.asarray(P, float); self.UV = np.asarray(UV, float); self.F = np.asarray(F, np.int64)
    def xform(self, R=None, t=(0, 0, 0), s=None):
        P = self.P.copy()
        if s is not None:
            P = P * np.asarray(s, float)
        if R is not None:
            P = P @ np.asarray(R).T
        return Geo(P + np.asarray(t, float), self.UV.copy(), self.F.copy())
    def flip(self):
        return Geo(self.P, self.UV, self.F[:, ::-1])
    @staticmethod
    def merge(gs):
        P, UV, F, o = [], [], [], 0
        for g in gs:
            P.append(g.P); UV.append(g.UV); F.append(g.F + o); o += len(g.P)
        return Geo(np.concatenate(P), np.concatenate(UV), np.concatenate(F))

def grid_faces(rows, cols):
    """Faces for a rows x cols vertex grid (row-major), quads split in two."""
    r, c = np.meshgrid(np.arange(rows - 1), np.arange(cols - 1), indexing="ij")
    a = r * cols + c; b = a + 1; d = a + cols; e = d + 1
    return np.concatenate([np.stack([a, d, b], -1).reshape(-1, 3), np.stack([b, d, e], -1).reshape(-1, 3)])

# ------------------------------------------------------------------ primitives
def loft(rings, cap0=False, cap1=False, uv_scale=1.0, closed=True):
    """Skin a list of rings (each (n,3), same n). Closed rings get a duplicated seam column."""
    R = [np.asarray(r, float) for r in rings]
    n = len(R[0])
    if closed:
        R = [np.vstack([r, r[:1]]) for r in R]
    rows, cols = len(R), len(R[0])
    P = np.stack(R).reshape(-1, 3)
    # u: arc length around the average ring; v: distance between ring centres
    avg = np.mean(np.stack(R), axis=0)
    seg = np.linalg.norm(np.diff(avg, axis=0), axis=1)
    u = np.concatenate([[0], np.cumsum(seg)])
    cen = np.array([r[:n].mean(0) for r in R])
    v = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(cen, axis=0), axis=1))])
    UV = np.stack(np.meshgrid(v, u, indexing="ij")[::-1], -1).reshape(-1, 2) * uv_scale
    F = grid_faces(rows, cols)
    gs = [Geo(P, UV, F)]
    for k, want in ((0, cap0), (rows - 1, cap1)):
        if not want:
            continue
        ring = R[k][:n]; c = ring.mean(0)
        Pc = np.vstack([ring, c]); m = n
        Fc = np.array([[i, (i + 1) % n, m] for i in range(n)])
        if k == 0:
            Fc = Fc[:, ::-1]
        UVc = np.vstack([(ring - c)[:, [0, 2]] * uv_scale, [[0, 0]]])
        gs.append(Geo(Pc, UVc, Fc))
    g = Geo.merge(gs)
    return g

def superellipse(n, a, b, e=2.0, phase=0.0):
    t = np.linspace(0, TAU, n, endpoint=False) + phase
    return np.stack([a * spow(np.cos(t), 2 / e), b * spow(np.sin(t), 2 / e)], -1)

def place_ring(pts2d, center, xaxis, yaxis):
    pts2d = np.asarray(pts2d, float)
    return np.asarray(center, float) + pts2d[:, :1] * np.asarray(xaxis, float) + pts2d[:, 1:2] * np.asarray(yaxis, float)

def path_frames(path, up=(0, 0, 1)):
    """Parallel-transport frames along a polyline: returns tangents T, normals N, binormals B."""
    path = np.asarray(path, float); k = len(path)
    T = np.zeros_like(path)
    T[1:-1] = path[2:] - path[:-2]; T[0] = path[1] - path[0]; T[-1] = path[-1] - path[-2]
    T = norm(T)
    N = np.zeros_like(path); B = np.zeros_like(path)
    n0 = np.cross(T[0], up)
    if np.linalg.norm(n0) < 1e-6:
        n0 = np.cross(T[0], (1, 0, 0))
    N[0] = norm(n0); B[0] = np.cross(T[0], N[0])
    for i in range(1, k):
        Rm = align(T[i - 1], T[i]); N[i] = norm(Rm @ N[i - 1]); B[i] = np.cross(T[i], N[i])
    return T, N, B

def sweep(path, profile, n=16, up=(0, 0, 1), cap0=False, cap1=False, uv_scale=1.0, twist=0.0):
    """Sweep a 2D profile along a path. profile(t, n) -> (n,2) points in (N, B) plane."""
    path = np.asarray(path, float)
    T, N, B = path_frames(path, up)
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
    rings = []
    for i, p in enumerate(path):
        t = L[i] / L[-1] if L[-1] > 0 else 0
        pts = profile(t, n)
        a = twist * t
        if a:
            c, s = math.cos(a), math.sin(a); pts = pts @ np.array([[c, s], [-s, c]])
        rings.append(place_ring(pts, p, B[i], N[i]))
    return loft(rings, cap0, cap1, uv_scale)

def tube(path, r, n=8, cap=True, uv_scale=1.0, up=(0, 0, 1)):
    rr = r if callable(r) else (lambda t: r)
    return sweep(path, lambda t, n: superellipse(n, rr(t), rr(t)), n, up, cap, cap, uv_scale)

def bezier(pts, k=24):
    """Evaluate a Bezier curve with any number of control points (de Casteljau)."""
    P = np.asarray(pts, float); out = []
    for t in np.linspace(0, 1, k):
        Q = P.copy()
        while len(Q) > 1:
            Q = Q[:-1] * (1 - t) + Q[1:] * t
        out.append(Q[0])
    return np.array(out)

def catmull(pts, k=8):
    """Catmull-Rom through points, k samples per span."""
    P = np.asarray(pts, float); P = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, k, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return np.array(out)

def superquadric(a, b, c, e1=1.0, e2=1.0, nu=24, nv=16, uv_scale=1.0):
    """Superellipsoid (rounded box at small e). a,b,c are x,y,z radii."""
    th = np.linspace(-math.pi / 2, math.pi / 2, nv)
    ph = np.linspace(-math.pi, math.pi, nu + 1)
    TH, PH = np.meshgrid(th, ph, indexing="ij")
    ct, st = spow(np.cos(TH), e1), spow(np.sin(TH), e1)
    X = a * ct * spow(np.cos(PH), e2); Y = b * st; Z = c * ct * spow(np.sin(PH), e2)
    P = np.stack([X, Y, Z], -1).reshape(-1, 3)
    U = (PH + math.pi) / TAU * (2 * (a + c)); V = (TH + math.pi / 2) / math.pi * (2 * b)
    UV = np.stack([U, V], -1).reshape(-1, 2) * uv_scale
    F = grid_faces(nv, nu + 1)
    return Geo(P, UV, F)

def sphere(r, nu=24, nv=16, uv_scale=1.0):
    return superquadric(r, r, r, 1, 1, nu, nv, uv_scale)

def offset_poly(poly, d):
    """Inset a 2D polygon (CCW) by d using mitred vertex normals."""
    P = np.asarray(poly, float); n = len(P)
    prev, nxt = np.roll(P, 1, 0), np.roll(P, -1, 0)
    e1 = norm(P - prev); e2 = norm(nxt - P)
    n1 = np.stack([-e1[:, 1], e1[:, 0]], -1); n2 = np.stack([-e2[:, 1], e2[:, 0]], -1)
    m = norm(n1 + n2); cos = np.clip((m * n1).sum(1), 0.3, 1)
    return P + m * (d / cos)[:, None]

def triangulate(poly):
    """Ear clipping for a simple CCW polygon."""
    P = np.asarray(poly, float); idx = list(range(len(P))); tris = []
    def area2(a, b, c):
        return (P[b][0] - P[a][0]) * (P[c][1] - P[a][1]) - (P[c][0] - P[a][0]) * (P[b][1] - P[a][1])
    def inside(p, a, b, c):
        return area2(a, b, p) >= 0 and area2(b, c, p) >= 0 and area2(c, a, p) >= 0
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1; done = False
        for k in range(len(idx)):
            a, b, c = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            if area2(a, b, c) <= 1e-12:
                continue
            if any(inside(p, a, b, c) for p in idx if p not in (a, b, c) and
                   (P[p] != P[a]).any() and (P[p] != P[b]).any() and (P[p] != P[c]).any()):
                continue
            tris.append((a, b, c)); idx.pop(k); done = True; break
        if not done:
            break
    if len(idx) == 3:
        tris.append(tuple(idx))
    return np.array(tris)

def poly_area(poly):
    P = np.asarray(poly); return 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])

def extrude(poly, depth, bevel=0.0, steps=3, uv_scale=1.0, back_bevel=True):
    """Extrude a 2D outline (XY) along Z (centred), with rounded bevels on the faces."""
    poly = np.asarray(poly, float)
    if poly_area(poly) < 0:
        poly = poly[::-1]
    rings, zs = [], []
    d2 = depth / 2
    if bevel > 0:
        angs = np.linspace(0, math.pi / 2, steps + 1)
        back = angs if back_bevel else [math.pi / 2]
        for a in back:
            rings.append(offset_poly(poly, bevel * (1 - math.sin(a)))); zs.append(-(d2 - bevel * (1 - math.cos(a))) if back_bevel else -d2)
        for a in angs[::-1]:
            rings.append(offset_poly(poly, bevel * (1 - math.sin(a)))); zs.append(d2 - bevel * (1 - math.cos(a)))
    else:
        rings = [poly, poly]; zs = [-d2, d2]
    rings3 = [np.column_stack([r, np.full(len(r), z)]) for r, z in zip(rings, zs)]
    side = loft(rings3, uv_scale=uv_scale).flip()
    T = triangulate(rings[-1])
    caps = []
    for r3, flip in ((rings3[0], True), (rings3[-1], False)):
        F = T[:, ::-1] if flip else T
        caps.append(Geo(r3, r3[:, :2] * uv_scale, F))
    return Geo.merge([side] + caps)

def rounded_rect(w, h, r, k=4):
    """CCW rounded rectangle outline centred at origin."""
    pts = []
    for cx, cy, a0 in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180)):
        for a in np.linspace(a0, a0 + 90, k + 1):
            pts.append((cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))))
    return np.array(pts)

# ------------------------------------------------------------------ normals
def compute_normals(P, F, angle=None, weld=1e-5):
    """Per-corner normals. angle=None -> fully smooth (welded by position);
    otherwise auto-smooth: only faces within `angle` degrees are averaged."""
    fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    fnn = norm(fn)
    key = np.round(P / weld).astype(np.int64)
    _, cid = np.unique(key, axis=0, return_inverse=True)
    cid = cid.reshape(-1)
    corner_c = cid[F].reshape(-1)
    corner_f = np.repeat(np.arange(len(F)), 3)
    if angle is None:
        acc = np.zeros((cid.max() + 1, 3)); np.add.at(acc, corner_c, fn[corner_f])
        return norm(acc[corner_c]).reshape(-1, 3, 3)
    cosT = math.cos(math.radians(angle))
    order = np.argsort(corner_c, kind="stable")
    sc = corner_c[order]
    bounds = np.flatnonzero(np.diff(sc)) + 1
    out = np.zeros((len(corner_c), 3))
    for grp in np.split(order, bounds):
        fs = corner_f[grp]
        Nn = fnn[fs]; Nw = fn[fs]
        M = (Nn @ Nn.T) >= cosT
        out[grp] = norm(M.astype(float) @ Nw)
    return out.reshape(-1, 3, 3)

def finalize(geo, angle=None):
    """Return (P, N, UV, F) re-indexed so vertices share only where normals agree."""
    P, UV, F = geo.P, geo.UV, geo.F
    keep = np.linalg.norm(np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]]), axis=1) > 1e-14
    F = F[keep]
    CN = compute_normals(P, F, angle)
    vid = F.reshape(-1); nq = np.round(CN.reshape(-1, 3) * 64).astype(np.int64)
    key = np.column_stack([vid, nq])
    uniq, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    first = np.zeros(len(uniq), np.int64); first[inv[::-1]] = np.arange(len(inv))[::-1]
    Pn = P[uniq[:, 0]]; UVn = UV[uniq[:, 0]]
    Nn = norm(CN.reshape(-1, 3)[first])
    return Pn, Nn, UVn, inv.reshape(-1, 3)

# ------------------------------------------------------------------ model & export
class Model:
    def __init__(self):
        self.parts = []      # (material, Geo, smooth_angle)
        self.materials = {}  # name -> dict(color, metal, rough, tex, normal)
        self.images = {}     # name -> PIL image
    def mat(self, name, color, metal=0.0, rough=0.8, tex=None, normal=None, double=False, alpha=1.0):
        self.materials[name] = dict(color=color, metal=metal, rough=rough, tex=tex, normal=normal, double=double, alpha=alpha)
    def add(self, mat, geo, angle=None, R=None, t=(0, 0, 0), s=None):
        if R is not None or s is not None or any(t):
            geo = geo.xform(R, t, s)
        self.parts.append((mat, geo, angle))
        return geo
    def build(self):
        groups = {}
        for mat, geo, ang in self.parts:
            P, N, UV, F = finalize(geo, ang)
            groups.setdefault(mat, []).append((P, N, UV, F))
        out = {}
        for mat, lst in groups.items():
            o = 0; Ps, Ns, UVs, Fs = [], [], [], []
            for P, N, UV, F in lst:
                Ps.append(P); Ns.append(N); UVs.append(UV); Fs.append(F + o); o += len(P)
            out[mat] = (np.concatenate(Ps), np.concatenate(Ns), np.concatenate(UVs), np.concatenate(Fs))
        return out

    def export_glb(self, path, built=None):
        built = built or self.build()
        bins, views, accs, prims, mats, texs, imgs = [], [], [], [], [], [], []
        off = 0
        def push(b, target=None):
            nonlocal off
            pad = (-len(b)) % 4; bins.append(b + b"\0" * pad)
            v = dict(buffer=0, byteOffset=off, byteLength=len(b))
            if target: v["target"] = target
            views.append(v); off += len(b) + pad; return len(views) - 1
        img_index = {}
        def image(name):
            if name in img_index: return img_index[name]
            buf = io.BytesIO(); self.images[name].save(buf, "PNG", optimize=True)
            bv = push(buf.getvalue()); imgs.append(dict(bufferView=bv, mimeType="image/png", name=name))
            texs.append(dict(source=len(imgs) - 1, sampler=0)); img_index[name] = len(texs) - 1
            return img_index[name]
        for mi, (mname, (P, N, UV, F)) in enumerate(built.items()):
            spec = self.materials[mname]
            a0 = len(accs)
            for arr, typ in ((P, "VEC3"), (N, "VEC3"), (UV, "VEC2")):
                bv = push(arr.astype(np.float32).tobytes(), 34962)
                acc = dict(bufferView=bv, componentType=5126, count=len(arr), type=typ)
                if typ == "VEC3" and arr is P:
                    acc["min"] = P.min(0).tolist(); acc["max"] = P.max(0).tolist()
                accs.append(acc)
            bv = push(F.astype(np.uint32).tobytes(), 34963)
            accs.append(dict(bufferView=bv, componentType=5125, count=F.size, type="SCALAR"))
            pbr = dict(baseColorFactor=list(spec["color"]) + [spec.get("alpha", 1.0)], metallicFactor=spec["metal"], roughnessFactor=spec["rough"])
            m = dict(name=mname, pbrMetallicRoughness=pbr, doubleSided=bool(spec.get("double")))
            if spec.get("alpha", 1.0) < 1.0: m["alphaMode"] = "BLEND"
            if spec["tex"]: pbr["baseColorTexture"] = dict(index=image(spec["tex"]))
            if spec["normal"]: m["normalTexture"] = dict(index=image(spec["normal"]), scale=1.0)
            mats.append(m)
            prims.append(dict(attributes=dict(POSITION=a0, NORMAL=a0 + 1, TEXCOORD_0=a0 + 2), indices=a0 + 3, material=mi))
        binary = b"".join(bins)
        gltf = dict(asset=dict(version="2.0", generator="Claude procedural marine HD"),
                    scene=0, scenes=[dict(nodes=[0])], nodes=[dict(name="Marine", mesh=0)],
                    meshes=[dict(name="Marine", primitives=prims)], materials=mats, accessors=accs,
                    bufferViews=views, buffers=[dict(byteLength=len(binary))],
                    samplers=[dict(magFilter=9729, minFilter=9987, wrapS=10497, wrapT=10497)])
        if imgs: gltf["images"] = imgs; gltf["textures"] = texs
        js = json.dumps(gltf, separators=(",", ":")).encode(); js += b" " * ((-len(js)) % 4)
        with open(path, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(binary)))
            f.write(struct.pack("<II", len(js), 0x4E4F534A)); f.write(js)
            f.write(struct.pack("<II", len(binary), 0x004E4942)); f.write(binary)
        return built

# ------------------------------------------------------------------ textures
rng = np.random.default_rng(11)

def value_noise(n, cells, seed=0):
    r = np.random.default_rng(seed); g = r.random((cells + 1, cells + 1)); g[-1] = g[0]; g[:, -1] = g[:, 0]
    x = np.linspace(0, cells, n, endpoint=False); i = x.astype(int); f = x - i; f = f * f * (3 - 2 * f)
    a = g[i][:, i]; b = g[i][:, i + 1]; c = g[i + 1][:, i]; d = g[i + 1][:, i + 1]
    fx = f[None, :]; fy = f[:, None]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

def fbm(n, oct=5, base=4, seed=0):
    out = np.zeros((n, n)); amp = 1; tot = 0
    for o in range(oct):
        out += value_noise(n, base * 2 ** o, seed + o) * amp; tot += amp; amp *= 0.5
    return out / tot

def to_img(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

def normal_from_height(h, strength=2.0):
    gy, gx = np.gradient(h)
    n = np.dstack([-gx * strength, -gy * strength, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return to_img(n * 0.5 + 0.5)

def digital_camo(n=512, cell=8, seed=3):
    """Pixelated 4-colour desert camo (tileable)."""
    cols = np.array([[0.78, 0.69, 0.53], [0.66, 0.55, 0.40], [0.50, 0.40, 0.29], [0.36, 0.29, 0.22]])
    m = n // cell
    a = fbm(m, 4, 3, seed); b = fbm(m, 4, 5, seed + 9)
    idx = np.zeros((m, m), int)
    idx[a > 0.47] = 1; idx[(a > 0.55) & (b > 0.45)] = 2; idx[(b > 0.62)] = 3; idx[(a < 0.36) & (b > 0.5)] = 2
    img = cols[idx].repeat(cell, 0).repeat(cell, 1)
    weave = (np.indices((n, n)).sum(0) % 2) * 0.03 - 0.015
    img = img * (1 + weave[..., None] + (fbm(n, 3, 32, seed + 5)[..., None] - 0.5) * 0.12)
    return to_img(img)

def weave_height(n=256, period=4):
    y, x = np.indices((n, n))
    h = 0.5 + 0.25 * np.sin(x / period * TAU) * np.sign(np.sin(y / (2 * period) * TAU)) + 0.25 * np.sin(y / period * TAU) * np.sign(np.cos(x / (2 * period) * TAU))
    return h * 0.8 + fbm(n, 3, 16, 7) * 0.2

def nylon(n=256, color=(0.47, 0.38, 0.26), seed=1):
    h = weave_height(n, 3)
    img = np.asarray(color)[None, None] * (0.86 + 0.18 * h[..., None] + (fbm(n, 4, 8, seed)[..., None] - 0.5) * 0.15)
    return to_img(img)

def molle_height(n=256):
    y = np.indices((n, n))[0]
    rows = ((y // 32) % 1 == 0) & ((y % 32) < 20)
    h = np.where(rows, 0.75, 0.25).astype(float)
    h = np.array(Image.fromarray((h * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))) / 255
    return h * 0.8 + weave_height(n, 3) * 0.2

def skin(n=256, seed=4):
    base = np.array([0.74, 0.55, 0.42])
    img = base[None, None] * (0.92 + 0.12 * fbm(n, 5, 6, seed)[..., None])
    img[..., 0] *= 1 + (fbm(n, 3, 3, seed + 3) - 0.5) * 0.12
    return to_img(img)

def leather(n=256, color=(0.62, 0.50, 0.35), seed=6):
    h = fbm(n, 6, 16, seed)
    img = np.asarray(color)[None, None] * (0.8 + 0.35 * h[..., None])
    return to_img(img), h

def metal_tex(n=256, color=(0.10, 0.10, 0.11), seed=8):
    h = fbm(n, 5, 24, seed)
    img = np.asarray(color)[None, None] * (0.85 + 0.3 * h[..., None])
    return to_img(img), h

def tread_height(n=256):
    y, x = np.indices((n, n))
    lugs = ((x // 32 + y // 32) % 2 == 0) & ((x % 32) > 4) & ((y % 32) > 4)
    return np.where(lugs, 0.85, 0.2).astype(float)
