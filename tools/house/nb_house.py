"""nb_house: the neighbourhood's period style kit (Oct 20 2026; RESUME section 2, step 2). Builds a house from its manifest entry
(spec/neighborhood.json, parcels[].kit) in headless Blender: 1910s-30s North Shore Foursquare / Colonial Revival / Tudor / shingle
pieces, every size in metres from the entry (footprint, plate and ridge heights, the film's window layout); only profiles are authored.

Pieces (LOD0 = Tier 2 hero, walkable street faces; artist-pipeline standard: chamfered edges 3-12 mm, real depth everywhere):
  walls      cladding (clapboard | shingle | brick | stucco) on metric UVs, openings cut as cells (no booleans), 12-15 cm reveals,
             corner boards, water table, frieze board under the eave (wood claddings), foundation band
  windows    casing + drip cap + projecting sill, sashes with stiles/rails/meeting rail, muntins (6/6, 1/1, 9/1, diamond lattice,
             French doors, panel door with lights, picture), glass set back in the sash, louvred shutters (optional)
  roofs      hip | gable_x | gable_z with real thickness: fascia, soffit, gutters, downspouts; hip / gable / shed dormers
  porch      piers + lattice skirt, deck with nosing, square columns (plinth, shaft, capital), beam, beadboard ceiling, low hip roof,
             railings (top rail, bottom rail, balusters at 0.11 m), steps with newels and the film's iron handrail
  chimney    brick stack, corbel band, cap, flue
  xmas       C7 bulb strings (eave, porch eave, rails, window casings) -> <lot>_xmas.json (Unity: SpecGreybox.Bulbs; Blender renders)
LOD1 = the Tier 3 stand-in (~1/10 the triangles): plain massing, roof planes, windows as framed cards, porch as boxes.
Also per lot: <lot>_NightGlow (lit windows, night only) and <lot>_Collider (boxes the player collides with: walls, porch, steps).

Materials are SHARED kit materials named NB_<set>_<colour> (set from Assets/Textures/Neighborhood/kit_textures.json, colour from
the manifest's kit_palette): every house uses the same few materials (Unity: SpecGreybox.Neighborhood remaps them to HDRP Lit).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/nb_house.py -- [lot_B0 lot_A-1 ...]   (default: every kit)
  -> unity/HomeAlone/Assets/Models/Neighborhood/<lot>.glb (+ _xmas.json), art/home_alone/references/neighborhood/build_stats.json
"""
import json
import math
import random
import zlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAN = json.loads((ROOT / "spec/neighborhood.json").read_text())
import os
OUT = Path(os.environ["NB_OUT"]) if os.environ.get("NB_OUT") else ROOT / "unity/HomeAlone/Assets/Models/Neighborhood"   # NB_OUT: staging (one builder)
PAL = MAN.get("kit_palette", {})


# ---------------------------------------------------------------- geometry in spec coordinates (x, y up, z)
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a):
    L = math.sqrt(dot(a, a)); return (a[0] / L, a[1] / L, a[2] / L) if L > 1e-12 else (0.0, 1.0, 0.0)
UP = (0.0, 1.0, 0.0)


class Geo:
    """Faces per material, metric UVs from each face's own plane (u along its horizontal tangent, v up the face; floors: x, z)."""
    def __init__(self):
        self.m = {}

    def face(self, mat, pts, toward, uv=None):
        n = [0.0, 0.0, 0.0]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            n[0] += (a[1] - b[1]) * (a[2] + b[2]); n[1] += (a[2] - b[2]) * (a[0] + b[0]); n[2] += (a[0] - b[0]) * (a[1] + b[1])
        if dot(n, toward) < 0:
            pts = list(reversed(pts)); n = [-c for c in n]
            if uv is not None: uv = list(reversed(uv))
        nn = norm(n)
        if uv is not None: pass   # explicit UVs (a lit window's room card), kept with their corners
        elif abs(nn[1]) > 0.97: uv = [(p[0], p[2]) for p in pts]
        else:
            t = norm(cross(UP, nn)); s = norm(cross(nn, t))
            uv = [(dot(p, t), dot(p, s)) for p in pts]
        self.m.setdefault(mat, []).append((list(pts), uv))

    def quad(self, mat, a, b, c, d, toward): self.face(mat, [a, b, c, d], toward)

    def obox(self, mat, c, ax, ay, az, hx, hy, hz, ch=0.0):
        """Oriented box: centre c, unit axes ax/ay/az, half sizes; ch = chamfer on all 12 edges (convex: faces oriented from the centre)."""
        ch = min(ch, 0.45 * min(hx, hy, hz)); H = (hx, hy, hz); A = (ax, ay, az)
        def P(s, k):   # the corner s's point on the face perpendicular to axis k
            q = c
            for j in range(3):
                d = s[j] * (H[j] if j == k else H[j] - ch); q = add(q, mul(A[j], d))
            return q
        S = [(sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
        def fc(pts): self.face(mat, pts, sub(mul(add(add(pts[0], pts[1]), pts[2]), 1 / 3), c))
        for k in range(3):
            i, j = [a for a in range(3) if a != k]
            for sg in (-1, 1):
                ring = []
                for si, sj in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    s = [0, 0, 0]; s[k] = sg; s[i] = si; s[j] = sj; ring.append(P(s, k))
                fc(ring)
        if ch <= 1e-5: return
        for k in range(3):
            i, j = [a for a in range(3) if a != k]
            for si in (-1, 1):
                for sj in (-1, 1):
                    s0 = [0, 0, 0]; s0[i] = si; s0[j] = sj; s0[k] = -1; s1 = list(s0); s1[k] = 1
                    fc([P(s0, i), P(s0, j), P(s1, j), P(s1, i)])
        for s in S: fc([P(s, 0), P(s, 1), P(s, 2)])

    def box(self, mat, x0, x1, y0, y1, z0, z1, ch=0.0):
        self.obox(mat, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (1, 0, 0), UP, (0, 0, 1), abs(x1 - x0) / 2, abs(y1 - y0) / 2, abs(z1 - z0) / 2, ch)

    def bar(self, mat, a, b, w, h, ch=0.0, up=UP):
        """A square-ish bar from a to b (w across, h up), e.g. a muntin, rail or handrail."""
        d = sub(b, a); L = math.sqrt(dot(d, d)); ax = norm(d); az = norm(cross(ax, up)); ay = cross(az, ax)
        self.obox(mat, mul(add(a, b), 0.5), ax, ay, az, L / 2, h / 2, w / 2, ch)

    def tris(self):
        return sum(len(p) - 2 for fl in self.m.values() for p, _ in fl)


class Face:
    """A wall face of a block: u = the absolute spec coordinate along it (z on x faces, x on z faces), y up, d = out of the wall."""
    def __init__(self, blk, side):
        self.side = side; x0, x1 = blk["x"]; z0, z1 = blk["z"]
        if side == "-x": self.p0, self.t, self.n, self.span = (x0, 0, 0), (0, 0, 1), (-1, 0, 0), (z0, z1)
        elif side == "+x": self.p0, self.t, self.n, self.span = (x1, 0, 0), (0, 0, 1), (1, 0, 0), (z0, z1)
        elif side == "-z": self.p0, self.t, self.n, self.span = (0, 0, z0), (1, 0, 0), (0, 0, -1), (x0, x1)
        else: self.p0, self.t, self.n, self.span = (0, 0, z1), (1, 0, 0), (0, 0, 1), (x0, x1)

    def P(self, u, y, d=0.0):
        return add(add(add(self.p0, mul(self.t, u)), (0, y, 0)), mul(self.n, d))

    def box(self, g, mat, u0, u1, y0, y1, d0, d1, ch=0.0):
        c = self.P((u0 + u1) / 2, (y0 + y1) / 2, (d0 + d1) / 2)
        g.obox(mat, c, self.t, UP, self.n, abs(u1 - u0) / 2, abs(y1 - y0) / 2, abs(d1 - d0) / 2, ch)


class OFace(Face):
    """An arbitrary vertical face (a turret side): centre point p0 on the face at y 0, unit tangent t, outward normal n, span (-hw, hw)."""
    def __init__(self, p0, t, n, hw, side="-x"):
        self.p0, self.t, self.n, self.span, self.side = p0, t, n, (-hw, hw), side


def matname(kind, colour): return f"NB_{kind}_{colour}"


# ---------------------------------------------------------------- the kit
class House:
    def __init__(self, lot, kit, lod):
        self.lot, self.k, self.lod = lot, kit, lod
        self.g = Geo(); self.glow = Geo(); self.col = []; self.bulbs = []
        P = kit["palette"]
        self.M = {
            "wall": matname(kit.get("cladding", "clapboard"), P["wall"]), "trim": matname("paint", P.get("trim", "white")),
            "sash": matname("paint", P.get("sash", P.get("trim", "white"))), "roof": matname(kit.get("roof_mat", "roof_asphalt"), P.get("roof", "slate")),
            "found": matname(kit.get("foundation_mat", "concrete"), P.get("found", "stone")), "glass": "NB_Glass", "glow": "NB_GlassLit",
            "door": matname("paint", P.get("door", "darkgreen")), "shutter": matname("paint", P.get("shutter", "black")),
            "brick": matname("brick", P.get("brick", "red")), "porchfloor": matname("paint", P.get("porch_floor", "porchgrey")),
            "metal": matname("paint", P.get("gutter", P.get("trim", "white"))), "iron": matname("paint", "black"),
            "lattice": matname("paint", P.get("lattice", P.get("trim", "white"))), "cap": matname("concrete", "stone"),
            "shrub": matname("paint", "darkgreen"),
        }
        self.wood = kit.get("cladding", "clapboard") in ("clapboard", "shingle")
        self.rng = random.Random(zlib.crc32(lot.encode()))

    # ---- walls with openings
    def openings(self, bi, side):
        return [w for w in self.k.get("windows", []) if w.get("block", 0) == bi and w["face"] == side]

    def wall(self, bi, blk, side, y0, y1, holes, mat=None, d=0.0, f=None):
        """The face from y0 to y1 as cells around the openings [(u0, u1, v0, v1)]."""
        f = f or Face(blk, side); mat = mat or self.M["wall"]
        us = sorted({f.span[0], f.span[1], *[c for h in holes for c in h[:2]]}); vs = sorted({y0, y1, *[c for h in holes for c in h[2:] if y0 < c < y1]})
        us = [u for u in us if f.span[0] <= u <= f.span[1]]
        for a, b in zip(us, us[1:]):
            for c, e in zip(vs, vs[1:]):
                um, vm = (a + b) / 2, (c + e) / 2
                if any(h[0] < um < h[1] and h[2] < vm < h[3] for h in holes): continue
                self.g.quad(mat, f.P(a, c, d), f.P(b, c, d), f.P(b, e, d), f.P(a, e, d), f.n)

    def gable_wall(self, blk, side, y0, apex, mat=None):
        f = Face(blk, side); a, b = f.span
        self.g.face(mat or self.M["wall"], [f.P(a, y0), f.P(b, y0), f.P((a + b) / 2, apex)], f.n)

    # ---- one window / door opening on a face (LOD0: full joinery; LOD1: a framed card)
    def window(self, blk, w, idx):
        f = w.get("_face") or Face(blk, w["face"]); u, wd, h, s = w["at"], w["w"], w["h"], w["sill"]; typ = w.get("type", "dh66")
        u0, u1, v0, v1 = u - wd / 2, u + wd / 2, s, s + h; T = self.M["trim"]; S = self.M["sash"]
        lit = idx in self.k.get("lit", {}).get("windows", [])
        room = w.get("room", zlib.crc32(f"{self.lot}{idx}".encode()) % 4); WU = (u0, u1, v0, v1)
        if self.lod == 1:
            f.box(self.g, T, u0 - 0.10, u1 + 0.10, v0 - 0.06, v1 + 0.12, 0.0, 0.02)
            self.g.quad(self.M["glass"], f.P(u0, v0, 0.025), f.P(u1, v0, 0.025), f.P(u1, v1, 0.025), f.P(u0, v1, 0.025), f.n)
            if lit: self.card(f, u0, u1, v0, v1, 0.028, WU, room)
            return
        R = w.get("reveal", 0.14 if self.k.get("cladding") in ("brick", "stucco") else 0.12)
        # reveal (jambs, head, stool) into the wall, painted
        for (a, b, c, e, tw) in ((u0, u0, v0, v1, f.t), (u1, u1, v0, v1, mul(f.t, -1))):
            self.g.quad(T, f.P(a, c, 0), f.P(a, e, 0), f.P(a, e, -R), f.P(a, c, -R), tw)
        self.g.quad(T, f.P(u0, v1, 0), f.P(u1, v1, 0), f.P(u1, v1, -R), f.P(u0, v1, -R), (0, -1, 0))
        self.g.quad(T, f.P(u0, v0, 0), f.P(u1, v0, 0), f.P(u1, v0, -R), f.P(u0, v0, -R), UP)
        # casing (brick/stucco: a brick soldier head + stone sill instead), sill, drip cap
        if self.wood or w.get("casing"):
            cw = 0.10; f.box(self.g, T, u0 - cw, u0, v0, v1 + 0.0, 0.0, 0.024, 0.004); f.box(self.g, T, u1, u1 + cw, v0, v1, 0.0, 0.024, 0.004)
            f.box(self.g, T, u0 - cw - 0.01, u1 + cw + 0.01, v1, v1 + 0.15, 0.0, 0.026, 0.004)
            f.box(self.g, T, u0 - cw - 0.03, u1 + cw + 0.03, v1 + 0.15, v1 + 0.18, 0.0, 0.05, 0.006)
        else:
            f.box(self.g, self.M["brick"], u0 - 0.05, u1 + 0.05, v1, v1 + 0.22, -0.002, 0.012, 0.003)
        if typ == "opening":   # an open porch mouth (recessed entry): reveal + columns only
            pass
        elif typ != "door" and typ != "french":
            f.box(self.g, T if self.wood else self.M["cap"], u0 - 0.13, u1 + 0.13, v0 - 0.05, v0 + 0.0, -0.04, 0.06, 0.006)
        D = -R + 0.03  # sash plane (glass a little behind the sash face)
        G = self.M["glass"]
        def pane(a, b, c, e, dd):
            self.g.quad(G, f.P(a, c, dd), f.P(b, c, dd), f.P(b, e, dd), f.P(a, e, dd), f.n)
            if lit: self.card(f, a, b, c, e, dd + 0.003, WU, room)
        def frame(a, b, c, e, dd, st=0.05, rl=0.05, bottom=None, mat=S):
            bottom = rl if bottom is None else bottom
            f.box(self.g, mat, a, a + st, c, e, dd - 0.02, dd + 0.02, 0.004); f.box(self.g, mat, b - st, b, c, e, dd - 0.02, dd + 0.02, 0.004)
            f.box(self.g, mat, a + st, b - st, e - rl, e, dd - 0.02, dd + 0.02, 0.004); f.box(self.g, mat, a + st, b - st, c, c + bottom, dd - 0.02, dd + 0.02, 0.004)
            return a + st, b - st, c + bottom, e - rl
        def muntins(a, b, c, e, cols, rows, dd):
            for i in range(1, cols):
                x = a + (b - a) * i / cols; f.box(self.g, S, x - 0.011, x + 0.011, c, e, dd - 0.012, dd + 0.012, 0.003)
            for j in range(1, rows):
                y = c + (e - c) * j / rows; f.box(self.g, S, a, b, y - 0.011, y + 0.011, dd - 0.012, dd + 0.012, 0.003)
        def diamond(a, b, c, e, dd, n=3):
            # leaded diamond lattice: bars at +-45 deg through the light, clipped to it (thin, dark lead)
            wd_, ht = b - a, e - c; step = wd_ / n
            for sgn in (1, -1):
                k = -ht
                while k < wd_ + ht:
                    pts = []
                    for (x, y) in ((k, 0), (k + sgn * ht, ht)) if sgn > 0 else ((k, 0), (k - ht, ht)):
                        pts.append((x, y))
                    (xa, ya), (xb, yb) = pts
                    # clip the segment to [0, wd_] x [0, ht]
                    def clip(xa, ya, xb, yb):
                        t0, t1 = 0.0, 1.0; dx, dy = xb - xa, yb - ya
                        for p, q in ((-dx, xa), (dx, wd_ - xa), (-dy, ya), (dy, ht - ya)):
                            if abs(p) < 1e-9:
                                if q < 0: return None
                                continue
                            r = q / p
                            if p < 0: t0 = max(t0, r)
                            else: t1 = min(t1, r)
                        return None if t0 >= t1 else (xa + t0 * dx, ya + t0 * dy, xa + t1 * dx, ya + t1 * dy)
                    cl = clip(xa, ya, xb, yb)
                    if cl and math.hypot(cl[2] - cl[0], cl[3] - cl[1]) > 0.03:
                        self.g.bar(S if not w.get("lead") else self.M["iron"], f.P(a + cl[0], c + cl[1], dd), f.P(a + cl[2], c + cl[3], dd), 0.012, 0.012, 0.0, up=f.n)
                    k += step
        if typ in ("dh66", "dh11", "dh91", "dh_diamond", "dh44", "dh61"):
            mid = v0 + h * 0.5
            top = {"dh66": (3, 2), "dh11": (1, 1), "dh91": (3, 3), "dh_diamond": (0, 0), "dh44": (2, 2), "dh61": (3, 2)}[typ]
            bot = {"dh66": (3, 2), "dh11": (1, 1), "dh91": (1, 1), "dh_diamond": (1, 1), "dh44": (2, 2), "dh61": (1, 1)}[typ]
            a, b, c, e = frame(u0, u1, mid - 0.02, v1, D - 0.045, rl=0.05, bottom=0.035)        # upper sash (outer track)
            pane(a, b, c, e, D - 0.055)
            if typ == "dh_diamond": diamond(a, b, c, e, D - 0.05)
            else: muntins(a, b, c, e, *top, D - 0.045)
            a, b, c, e = frame(u0, u1, v0, mid + 0.02, D, rl=0.035, bottom=0.07)               # lower sash
            pane(a, b, c, e, D - 0.01); muntins(a, b, c, e, *bot, D)
        elif typ in ("casement_diamond", "casement"):
            n = w.get("leaves", 1)
            for i in range(n):
                a0 = u0 + (u1 - u0) * i / n; a1 = u0 + (u1 - u0) * (i + 1) / n
                a, b, c, e = frame(a0, a1, v0, v1, D, st=0.045, rl=0.045)
                pane(a, b, c, e, D - 0.01)
                diamond(a, b, c, e, D, n=2) if typ == "casement_diamond" else None
        elif typ == "french":
            for i in range(2):
                a0 = u0 + (u1 - u0) * i / 2; a1 = u0 + (u1 - u0) * (i + 1) / 2
                a, b, c, e = frame(a0, a1, v0, v1, D, st=0.06, rl=0.07, bottom=0.18)
                pane(a, b, c, e, D - 0.01); muntins(a, b, c, e, 2, 5, D)
        elif typ == "picture_diamond":
            a, b, c, e = frame(u0, u1, v0, v1, D, st=0.06, rl=0.06); pane(a, b, c, e, D - 0.01); diamond(a, b, c, e, D, n=5)
        elif typ == "opening":
            pass
        elif typ == "door":
            Dm = self.M["door"]; a, b, c, e = frame(u0, u1, v0, v1, D, st=0.11, rl=0.11, bottom=0.22, mat=Dm)
            gl = c + (e - c) * 0.45; f.box(self.g, Dm, a, b, c, gl, D - 0.015, D + 0.005, 0.004)       # lower panel
            f.box(self.g, Dm, a, b, gl - 0.06, gl, D - 0.02, D + 0.02, 0.004)                             # lock rail
            pane(a, b, gl, e, D - 0.01); muntins(a, b, gl, e, 1, 3, D)
            f.box(self.g, self.M["metal"], b - 0.09, b - 0.06, c + 0.9, c + 0.97, D, D + 0.05, 0.005)     # knob
        else:
            raise ValueError(f"{self.lot}: window type {typ}")
        if w.get("shutters"):
            sw = wd / 2 + 0.02
            for a in ((u0 - 0.10 - sw, u0 - 0.10), (u1 + 0.10, u1 + 0.10 + sw)):
                Sh = self.M["shutter"]
                f.box(self.g, Sh, a[0], a[0] + 0.05, v0, v1 + 0.02, 0.02, 0.055, 0.004); f.box(self.g, Sh, a[1] - 0.05, a[1], v0, v1 + 0.02, 0.02, 0.055, 0.004)
                f.box(self.g, Sh, a[0] + 0.05, a[1] - 0.05, v1 - 0.06, v1 + 0.02, 0.02, 0.055, 0.004); f.box(self.g, Sh, a[0] + 0.05, a[1] - 0.05, v0, v0 + 0.08, 0.02, 0.055, 0.004)
                f.box(self.g, Sh, a[0] + 0.05, a[1] - 0.05, (v0 + v1) / 2 - 0.03, (v0 + v1) / 2 + 0.03, 0.02, 0.055, 0.004)
                y = v0 + 0.10
                while y < v1 - 0.08:
                    if abs(y - (v0 + v1) / 2) > 0.05:
                        g0 = f.P(a[0] + 0.05, y, 0.03); g1 = f.P(a[1] - 0.05, y, 0.03)
                        self.g.obox(Sh, mul(add(g0, g1), 0.5), f.t, norm(add(UP, mul(f.n, 0.8))), norm(sub(f.n, mul(UP, 0.8))), (a[1] - a[0] - 0.1) / 2, 0.022, 0.004)
                    y += 0.045
        if w.get("xmas"): self.string([f.P(u0 - 0.12, v0, 0.03), f.P(u0 - 0.12, v1 + 0.16, 0.03), f.P(u1 + 0.12, v1 + 0.16, 0.03), f.P(u1 + 0.12, v0, 0.03)], 0.17, 0.0)
        if w.get("hood") == "eyebrow":   # Shingle Style: a shingled eyebrow arch over the head, 0.3 m deep (Marley's house, upper windows)
            rx, ry, n_ = wd / 2 + 0.22, 0.32, 8; yb = v1 + 0.16
            pts = [f.P(u + rx * math.cos(math.pi * i / n_), yb + ry * math.sin(math.pi * i / n_), 0.16) for i in range(n_ + 1)]
            for a, b in zip(pts, pts[1:]): self.g.bar(self.M["roof"], a, b, 0.07, 0.32, 0.01, up=f.n)
        for c in range(w.get("columns", 0)):   # a recessed entry's round columns standing in the opening's front plane
            cu = u0 + 0.18 + (wd - 0.36) * c / max(1, w["columns"] - 1); n_ = 10; r = 0.12
            for i in range(n_):
                a0, a1 = 2 * math.pi * i / n_, 2 * math.pi * (i + 1) / n_
                P = lambda a, y: f.P(cu + r * math.cos(a), y, -0.2 + r * math.sin(a))
                self.g.quad(self.M["iron"], P(a0, v0), P(a1, v0), P(a1, v1), P(a0, v1), sub(P((a0 + a1) / 2, v0), f.P(cu, v0, -0.2)))

    def card(self, f, a, b, c, e, dd, U, k):
        """A lit pane (a..b, c..e at depth dd) of the window U = (u0, u1, v0, v1) on face f, textured with quadrant k of the room-card
        atlas (nb_textures.room_cards: 0 sheers + drapes, 1 lamp + open drapes, 2 shade half down, 3 tree behind blinds) spanning the whole
        window, so the muntins and sashes cross one picture. Blender UVs (origin bottom-left; image row 0 = the atlas top)."""
        u0, u1, v0, v1 = U; flip = f.side in ("+x", "-z"); col, row = k % 2, k // 2   # flip: s runs left to right as seen from outside
        def st(u, v):
            s_ = (u - u0) / (u1 - u0); s_ = 1 - s_ if flip else s_
            return (col * 0.5 + 0.5 * min(1, max(0, s_)), 1 - (row + 1) * 0.5 + 0.5 * min(1, max(0, (v - v0) / (v1 - v0))))
        self.glow.face(self.M["glow"], [f.P(a, c, dd), f.P(b, c, dd), f.P(b, e, dd), f.P(a, e, dd)], f.n, [st(a, c), st(b, c), st(b, e), st(a, e)])

    # ---- Christmas strings: C7 bulbs every `step` m, sagging between clips every 0.4 m
    def string(self, pts, step=0.2, sag=0.025):
        for a, b in zip(pts, pts[1:]):
            L = math.sqrt(dot(sub(b, a), sub(b, a))); n = max(1, int(L / step))
            for i in range(n):
                t = (i + 0.5) / n; p = add(a, mul(sub(b, a), t)); clip = ((i * step) % 0.4) / 0.4
                p = add(p, (0, -sag * 4 * clip * (1 - clip), 0))
                self.bulbs.append([round(p[0], 3), round(p[1], 3), round(p[2], 3), self.rng.randrange(5)])

    def swag(self, a, b, loops=2, depth=0.22, step=0.15):
        """A string draped in `loops` hanging loops from a to b (porch rails, film 11581: dense swags on the rails)."""
        L = math.sqrt(dot(sub(b, a), sub(b, a))); n = max(2, int(L / step))
        for i in range(n):
            t = (i + 0.5) / n; p = add(a, mul(sub(b, a), t)); p = add(p, (0, -depth * abs(math.sin(math.pi * loops * t)), 0))
            self.bulbs.append([round(p[0], 3), round(p[1], 3), round(p[2], 3), self.rng.randrange(5)])

    def xmas_extra(self):
        """kit['xmas']: free strings (pts polylines), swags, lit foundation shrubs {x, z, rx, rz, h, bulbs} (LOD0 only)."""
        X = self.k.get("xmas", {})
        for s_ in X.get("strings", []):
            self.string([tuple(p) for p in s_["pts"]], s_.get("step", 0.2), s_.get("sag", 0.025))
        for s_ in X.get("swags", []): self.swag(tuple(s_["a"]), tuple(s_["b"]), s_.get("loops", 2), s_.get("depth", 0.22))
        for sh in X.get("shrubs", []):
            x, z, rx, rz, h = sh["x"], sh["z"], sh["rx"], sh["rz"], sh["h"]; nu, nv = 10, 5; M = self.M["shrub"]
            ring = lambda j: [(x + rx * math.sin(math.pi * j / nv) * math.cos(2 * math.pi * i / nu) * (0.9 + 0.1 * self.rng.random()), h * (1 - math.cos(math.pi * j / nv)) / 2 * 1.0,
                               z + rz * math.sin(math.pi * j / nv) * math.sin(2 * math.pi * i / nu)) for i in range(nu)]
            rs = [ring(j) for j in range(nv + 1)]
            for j in range(nv):
                for i in range(nu):
                    a, b, c, d = rs[j][i], rs[j][(i + 1) % nu], rs[j + 1][(i + 1) % nu], rs[j + 1][i]
                    self.g.face(M, [a, c, d] if j == 0 else [a, b, c] if j == nv - 1 else [a, b, c, d], sub(mul(add(a, c), 0.5), (x, h / 2, z)))
            for _ in range(sh.get("bulbs", 40)):   # on the shell's upper 85 %
                th = math.acos(1 - 2 * self.rng.uniform(0.0, 0.92)); ph = self.rng.uniform(0, 2 * math.pi)
                p = (x + 1.03 * rx * math.sin(th) * math.cos(ph), h / 2 + 1.03 * h / 2 * math.cos(th), z + 1.03 * rz * math.sin(th) * math.sin(ph))
                self.bulbs.append([round(p[0], 3), round(p[1], 3), round(p[2], 3), self.rng.randrange(5)])

    # ---- roofs (thickness, fascia, soffit, gutter, downspouts)
    def roof(self, blk, bi):
        x0, x1 = blk["x"]; z0, z1 = blk["z"]; o = blk.get("overhang", 0.5); typ = blk.get("roof", "hip"); p = math.radians(blk.get("pitch", 35))
        plate = blk["plate"]; he = plate - o * math.tan(p) if blk.get("eave") is None else blk["eave"]
        X0, X1, Z0, Z1 = x0 - o, x1 + o, z0 - o, z1 + o; R = self.M["roof"]; T = self.M["trim"]; W, D = X1 - X0, Z1 - Z0
        fh = 0.20 if self.lod == 0 else 0.0
        cx, cz = (X0 + X1) / 2, (Z0 + Z1) / 2
        fl = blk.get("flare", 0.0) if typ == "hip" else 0.0
        if fl:   # Shingle Style flared eave: a shallow kick (14 deg) over the outer `fl` m, the main pitch above it
            hk = he + fl * math.tan(math.radians(14)); k0, k1, k2, k3 = (X0 + fl, hk, Z0 + fl), (X1 - fl, hk, Z0 + fl), (X1 - fl, hk, Z1 - fl), (X0 + fl, hk, Z1 - fl)
            self.g.face(R, [(X0, he, Z0), (X1, he, Z0), k1, k0], (0, 1, -1)); self.g.face(R, [(X1, he, Z0), (X1, he, Z1), k2, k1], (1, 1, 0))
            self.g.face(R, [(X1, he, Z1), (X0, he, Z1), k3, k2], (0, 1, 1)); self.g.face(R, [(X0, he, Z1), (X0, he, Z0), k0, k3], (-1, 1, 0))
        if typ == "hip":
            he0, X0_, X1_, Z0_, Z1_ = he, X0, X1, Z0, Z1
            if fl: he, X0, X1, Z0, Z1 = hk, X0 + fl, X1 - fl, Z0 + fl, Z1 - fl; W, D = X1 - X0, Z1 - Z0; cx, cz = (X0 + X1) / 2, (Z0 + Z1) / 2
            s = min(W, D) / 2; rh = he + s * math.tan(p); blk["_ridge"] = rh
            if W >= D: ra, rb = (X0 + s, rh, cz), (X1 - s, rh, cz)
            else: ra, rb = (cx, rh, Z0 + s), (cx, rh, Z1 - s)
            c00, c10, c11, c01 = (X0, he, Z0), (X1, he, Z0), (X1, he, Z1), (X0, he, Z1)
            if W >= D:
                self.g.face(R, [c00, c10, rb, ra], (0, 1, -1)); self.g.face(R, [c01, c11, rb, ra], (0, 1, 1))
                self.g.face(R, [c00, c01, ra], (-1, 1, 0)); self.g.face(R, [c10, c11, rb], (1, 1, 0))
            else:
                self.g.face(R, [c00, c01, rb, ra], (-1, 1, 0)); self.g.face(R, [c10, c11, rb, ra], (1, 1, 0))
                self.g.face(R, [c00, c10, ra], (0, 1, -1)); self.g.face(R, [c01, c11, rb], (0, 1, 1))
            eaves = [(c00, c10, (0, 0, -1)), (c10, c11, (1, 0, 0)), (c11, c01, (0, 0, 1)), (c01, c00, (-1, 0, 0))]
            if self.lod == 0:   # hip and ridge caps
                for a, b in ((c00, ra), (c01, ra), (c10, rb), (c11, rb), (ra, rb)):
                    if a != b: self.g.bar(R, add(a, (0, 0.02, 0)), add(b, (0, 0.02, 0)), 0.16, 0.035, 0.008)
            if fl:   # fascia, soffit and gutters stay at the flared outer edge
                he, X0, X1, Z0, Z1 = he0, X0_, X1_, Z0_, Z1_
                c00, c10, c11, c01 = (X0, he, Z0), (X1, he, Z0), (X1, he, Z1), (X0, he, Z1)
                eaves = [(c00, c10, (0, 0, -1)), (c10, c11, (1, 0, 0)), (c11, c01, (0, 0, 1)), (c01, c00, (-1, 0, 0))]
        else:   # gable: ridge along x (gable_x: gable ends face +-z?) -> gable_x = ridge parallel to x (gable walls on the x faces)
            along_x = typ == "gable_x"
            s = (D if along_x else W) / 2; rh = he + s * math.tan(p); blk["_ridge"] = rh
            if along_x:
                ra, rb = (X0, rh, cz), (X1, rh, cz)
                self.g.face(R, [(X0, he, Z0), (X1, he, Z0), rb, ra], (0, 1, -1)); self.g.face(R, [(X0, he, Z1), (X1, he, Z1), rb, ra], (0, 1, 1))
                eaves = [((X0, he, Z0), (X1, he, Z0), (0, 0, -1)), ((X1, he, Z1), (X0, he, Z1), (0, 0, 1))]
                apex = plate + (z1 - z0) / 2 * math.tan(p)
                for side in ("-x", "+x"): self.gable_wall(blk, side, plate - 0.001, apex + 0.0)
                rakes = [((X0, he, Z0), ra, (X0, he, Z1)), ((X1, he, Z0), rb, (X1, he, Z1))]
            else:
                ra, rb = (cx, rh, Z0), (cx, rh, Z1)
                self.g.face(R, [(X0, he, Z0), (X0, he, Z1), rb, ra], (-1, 1, 0)); self.g.face(R, [(X1, he, Z0), (X1, he, Z1), rb, ra], (1, 1, 0))
                eaves = [((X0, he, Z1), (X0, he, Z0), (-1, 0, 0)), ((X1, he, Z0), (X1, he, Z1), (1, 0, 0))]
                apex = plate + (x1 - x0) / 2 * math.tan(p)
                for side in ("-z", "+z"): self.gable_wall(blk, side, plate - 0.001, apex)
                rakes = [((X0, he, Z0), ra, (X1, he, Z0)), ((X0, he, Z1), rb, (X1, he, Z1))]
            if self.lod == 0:
                self.g.bar(R, add(ra, (0, 0.02, 0)), add(rb, (0, 0.02, 0)), 0.16, 0.035, 0.008)
                for a, top, b in rakes:   # rake boards (barge boards) under the roof edge
                    for q in (a, b):
                        self.g.bar(T, add(q, (0, -0.10, 0)), add(top, (0, -0.10, 0)), 0.04, 0.2, 0.006)
            # the roof's underside over the gable overhang (soffit of the rake): close it
            for a, top, b in rakes:
                self.g.face(T, [add(a, (0, -fh, 0)), add(top, (0, -fh, 0)), add(b, (0, -fh, 0))], (0, -1, 0))
        # fascia, soffit, gutters along the eaves
        wall = {(0, 0, -1): z0, (1, 0, 0): x1, (0, 0, 1): z1, (-1, 0, 0): x0}
        for a, b, n in eaves:
            if fh: self.g.quad(T, a, b, add(b, (0, -fh, 0)), add(a, (0, -fh, 0)), n)
            # soffit: from the fascia back to the wall line
            wl = wall[n]
            a2 = (wl if n[0] else a[0], a[1] - fh, wl if n[2] else a[2]); b2 = (wl if n[0] else b[0], b[1] - fh, wl if n[2] else b[2])
            # inset the soffit's ends to the wall corners
            if n[0]: a2 = (a2[0], a2[1], min(max(a2[2], z0), z1)); b2 = (b2[0], b2[1], min(max(b2[2], z0), z1))
            else: a2 = (min(max(a2[0], x0), x1), a2[1], a2[2]); b2 = (min(max(b2[0], x0), x1), b2[1], b2[2])
            self.g.quad(T, add(a, (0, -fh, 0)), add(b, (0, -fh, 0)), b2, a2, (0, -1, 0))
            if self.lod == 0:
                gut = mul(n, 0.07); G = self.M["metal"]
                self.g.bar(G, add(add(a, gut), (0, -0.08, 0)), add(add(b, gut), (0, -0.08, 0)), 0.13, 0.12, 0.012)
            if blk.get("xmas_eave") and n in [tuple(v) for v in blk["xmas_eave"]]:
                self.string([add(add(a, mul(n, 0.15)), (0, -0.20, 0)), add(add(b, mul(n, 0.15)), (0, -0.20, 0))])
        if self.lod == 0 and blk.get("downspouts", True):
            for (x, z, gx) in ((x0 - 0.06, z0 + 0.14, X0 + 0.07), (x1 + 0.06, z1 - 0.14, X1 - 0.07)):   # down the wall corner, a goose-neck back to the gutter
                self.g.box(self.M["metal"], x - 0.04, x + 0.04, 0.05, he - 0.55, z - 0.04, z + 0.04, 0.01)
                self.g.bar(self.M["metal"], (x, he - 0.58, z), (gx, he - 0.16, z), 0.08, 0.08, 0.01)
        return he

    def dormer(self, blk, d):
        """A dormer on face d['face'] of block blk: front wall (cladding + windows), cheeks, its own hip/gable/shed roof."""
        f = Face(blk, d["face"]); u, w = d["at"], d["w"]; set_ = d.get("setback", 0.9); p = math.radians(d.get("pitch", blk.get("pitch", 35)))
        plate = blk["plate"]; y0 = plate - 0.2; y1 = plate + d.get("h", 1.5); back = d.get("depth", 2.6); o = d.get("overhang", 0.3)
        u0, u1 = u - w / 2, u + w / 2; dd = -set_   # dormer front plane, d measured outward from the wall
        M = self.M["wall"]; T = self.M["trim"]; R = self.M["roof"]
        holes = []
        for wi in d.get("windows", []):
            holes.append((u + wi["off"] - wi["w"] / 2, u + wi["off"] + wi["w"] / 2, y0 + wi["sill"], y0 + wi["sill"] + wi["h"]))
        # front wall (as a mini face at depth -setback)
        us = sorted({u0, u1, *[c for h in holes for c in h[:2]]}); vs = sorted({y0, y1, *[c for h in holes for c in h[2:]]})
        for a, b in zip(us, us[1:]):
            for c, e in zip(vs, vs[1:]):
                if any(h[0] < (a + b) / 2 < h[1] and h[2] < (c + e) / 2 < h[3] for h in holes): continue
                self.g.quad(M, f.P(a, c, dd), f.P(b, c, dd), f.P(b, e, dd), f.P(a, e, dd), f.n)
        for a in (u0, u1):   # cheeks back into the roof
            tw = mul(f.t, -1 if a == u0 else 1)
            self.g.quad(M, f.P(a, y0, dd), f.P(a, y1, dd), f.P(a, y1, dd - back), f.P(a, y0, dd - back), tw)
            if self.lod == 0 and self.wood: f.box(self.g, T, a - 0.05 if a == u0 else a - 0.05, a + 0.05, y0, y1, dd - 0.0, dd + 0.025, 0.004)
        # its windows: reuse the window builder on a temporary face shifted to the dormer plane
        for wi in d.get("windows", []):
            fake = dict(blk); ww = {"face": d["face"], "at": u + wi["off"], "w": wi["w"], "h": wi["h"], "sill": y0 + wi["sill"], "type": wi.get("type", "dh11"), "xmas": False}
            sh = mul(f.n, dd)
            g0 = self.g; tmp = Geo(); self.g = tmp; gl0 = self.glow; tmpg = Geo(); self.glow = tmpg
            self.window(blk, ww, -1)
            self.g = g0; self.glow = gl0
            for mat, fl in tmp.m.items():
                for pts, uv in fl: self.g.m.setdefault(mat, []).append(([add(q, sh) for q in pts], uv))
        # roof: hip dormer (front hip + two sides running back), or gable
        Y = y1; F0 = f.P(u0 - o, Y - o * math.tan(p), dd + o); F1 = f.P(u1 + o, Y - o * math.tan(p), dd + o)
        rise = (w / 2 + o) * math.tan(p); top = Y - o * math.tan(p) + rise
        B0 = f.P(u0 - o, Y - o * math.tan(p), dd - back); B1 = f.P(u1 + o, Y - o * math.tan(p), dd - back)
        if d.get("roof", "hip") == "hip":
            A = f.P(u, top, dd + o - (w / 2 + o)); Bk = f.P(u, top, dd - back)
            self.g.face(R, [F0, F1, A], add(f.n, UP)); self.g.face(R, [F0, A, Bk, B0], add(mul(f.t, -1), UP)); self.g.face(R, [F1, B1, Bk, A], add(f.t, UP))
        else:
            A = f.P(u, top, dd + o); Bk = f.P(u, top, dd - back)
            self.g.face(R, [F0, A, Bk, B0], add(mul(f.t, -1), UP)); self.g.face(R, [F1, B1, Bk, A], add(f.t, UP))
            self.g.face(M, [f.P(u0, Y, dd), f.P(u1, Y, dd), f.P(u, top - 0.02, dd)], f.n)
        # fascia + soffit of the dormer roof
        fh = 0.12
        self.g.quad(T, F0, F1, add(F1, (0, -fh, 0)), add(F0, (0, -fh, 0)), f.n)
        self.g.quad(T, add(F0, (0, -fh, 0)), add(F1, (0, -fh, 0)), f.P(u1, Y - o * math.tan(p) - fh, dd), f.P(u0, Y - o * math.tan(p) - fh, dd), (0, -1, 0))

    def porch(self, pc):
        x0, x1 = pc["x"]; z0, z1 = pc["z"]; fl = pc["floor"]; edge = pc["edge"]; o = pc.get("overhang", 0.3); p = math.radians(pc.get("pitch", 14))
        front = pc.get("front", "-x"); T = self.M["trim"]; R = self.M["roof"]; lod0 = self.lod == 0
        assert front == "-x", "porches are built facing -x (lot side B); flip the kit for side A"
        # deck with nosing, piers + lattice skirt
        self.g.box(self.M["porchfloor"], x0 - 0.03, x1, fl - 0.05, fl, z0 - 0.03, z1 + 0.03, 0.008 if lod0 else 0)
        self.g.box(T, x0 - 0.035, x1, fl - 0.25, fl - 0.05, z0 - 0.035, z1 + 0.035, 0.006 if lod0 else 0)
        cols = pc["columns"]; side_cols = pc.get("side_columns", [])
        for z in cols:
            self.g.box(self.M["brick"] if pc.get("piers") == "brick" else T, x0 + 0.02, x0 + 0.42, 0, fl - 0.25, z - 0.2, z + 0.2, 0.01 if lod0 else 0)
        self.g.box(self.M["lattice"], x0 + 0.08, x1, 0.0, fl - 0.25, z0 + 0.06, z1 - 0.06, 0)   # lattice skirt (recessed)
        sh = 0.13; top = edge - 0.30
        allcols = [(x0 + 0.22, z) for z in cols] + [(x, z) for x, z in side_cols]
        for x, z in allcols:
            if lod0:
                self.g.box(T, x - 0.17, x + 0.17, fl, fl + 0.22, z - 0.17, z + 0.17, 0.012)            # plinth
                self.g.box(T, x - 0.19, x + 0.19, fl + 0.22, fl + 0.26, z - 0.19, z + 0.19, 0.008)
                self.g.box(T, x - sh, x + sh, fl + 0.26, top - 0.16, z - sh, z + sh, 0.012)          # shaft
                self.g.box(T, x - 0.16, x + 0.16, top - 0.16, top - 0.10, z - 0.16, z + 0.16, 0.008)   # capital
                self.g.box(T, x - 0.19, x + 0.19, top - 0.10, top, z - 0.19, z + 0.19, 0.008)
            else:
                self.g.box(T, x - sh, x + sh, fl, top, z - sh, z + sh)
        # beam (frieze) round the porch, ceiling
        xb = x0 + 0.22
        self.g.box(T, xb - 0.12, xb + 0.12, top, edge - 0.02, z0 + 0.05, z1 - 0.05, 0.006 if lod0 else 0)
        for z in (z0 + 0.05, z1 - 0.05):
            self.g.box(T, xb - 0.12, x1, top, edge - 0.02, z - 0.12, z + 0.12, 0.006 if lod0 else 0)
        self.g.quad(T, (x0 - o, edge - 0.18, z0 - o), (x1, edge - 0.18, z0 - o), (x1, edge - 0.18, z1 + o), (x0 - o, edge - 0.18, z1 + o), (0, -1, 0))
        # low hip roof against the house wall (x1): front plane + hipped ends
        X0, Z0, Z1 = x0 - o, z0 - o, z1 + o; run = x1 - X0; rh = edge + run * math.tan(p)
        a, b = (X0, edge, Z0), (X0, edge, Z1); c_, d_ = (x1, rh, Z1 - run), (x1, rh, Z0 + run)
        self.g.face(R, [a, b, c_, d_], (-1, 2, 0)); self.g.face(R, [a, d_, (x1, edge, Z0)], (0, 1, -1)); self.g.face(R, [b, (x1, edge, Z1), c_], (0, 1, 1))
        fh = 0.18
        for e0, e1, n in ((a, b, (-1, 0, 0)), (a, (x1, edge, Z0), (0, 0, -1)), (b, (x1, edge, Z1), (0, 0, 1))):
            self.g.quad(T, e0, e1, add(e1, (0, -fh, 0)), add(e0, (0, -fh, 0)), n)
            if lod0: self.g.bar(self.M["metal"], add(add(e0, mul(n, 0.07)), (0, -0.08, 0)), add(add(e1, mul(n, 0.07)), (0, -0.08, 0)), 0.12, 0.11, 0.01)
        if pc.get("xmas_eave"):
            self.string([add(a, (-0.12, -0.2, 0)), add(b, (-0.12, -0.2, 0))])
            if pc["xmas_eave"] == "wrap":   # film 11581: the string turns the porch roof's right (+z) corner and runs back along its side
                self.string([add(b, (-0.12, -0.2, 0.12)), add((x1, edge, Z1), (0, -0.2, 0.12))])
        # railings between columns, skipping the steps' bay; side railings
        st = pc.get("steps"); rh_ = fl + pc.get("rail", 0.80)
        runs = []
        zs = sorted(cols)
        for za, zb in zip(zs, zs[1:]):
            if st and za < st["at"] < zb: continue
            runs.append(((xb, za + 0.17), (xb, zb - 0.17)))
        for z in (zs[0], zs[-1]):
            if pc.get("side_rails", True): runs.append(((xb + 0.17, z), (x1 - 0.05, z)))
        for (ax, az), (bx, bz) in runs:
            A0, B0 = (ax, rh_, az), (bx, rh_, bz)
            if lod0:
                self.g.bar(T, add(A0, (0, -0.02, 0)), add(B0, (0, -0.02, 0)), 0.09, 0.06, 0.008)      # top rail
                self.g.bar(T, (ax, fl + 0.09, az), (bx, fl + 0.09, bz), 0.07, 0.05, 0.006)          # bottom rail
                L = math.hypot(bx - ax, bz - az); n = max(1, int(L / 0.11))
                for i in range(1, n):
                    t = i / n; xx, zz = ax + (bx - ax) * t, az + (bz - az) * t
                    self.g.box(T, xx - 0.022, xx + 0.022, fl + 0.115, rh_ - 0.05, zz - 0.022, zz + 0.022, 0.004)
            else:
                self.g.bar(T, (ax, (fl + rh_) / 2, az), (bx, (fl + rh_) / 2, bz), 0.05, rh_ - fl, 0)
            if pc.get("xmas_rail"):
                self.string([add(A0, (-0.04, 0.03, 0)), add(B0, (-0.04, 0.03, 0))], 0.15, 0.04)
                if pc.get("xmas_rail") == "swag":   # film 11581: the rails carry dense draped loops below the top rail
                    L_ = math.hypot(bx - ax, bz - az); self.swag(add(A0, (-0.06, -0.04, 0)), add(B0, (-0.06, -0.04, 0)), max(1, round(L_ / 0.9)), 0.30)
        if st:   # steps: n risers from grade to the floor, newels both sides, the film's black iron handrail down the middle
            n = st.get("risers", 5); rz0, rz1 = st["at"] - st["w"] / 2, st["at"] + st["w"] / 2; tr = 0.29
            for i in range(n):
                y = fl * (n - i - 1) / n; xs = x0 - tr * (i + 1)
                self.g.box(self.M["cap"], xs, x0, y, fl * (n - i) / n, rz0, rz1, 0.01 if lod0 else 0)
            if lod0:
                for z in (rz0 - 0.12, rz1 + 0.12):
                    self.g.box(T, x0 - tr * n - 0.12, x0 - tr * n + 0.18, 0, rh_ + 0.12, z - 0.15, z + 0.15, 0.012)   # newel
                    self.g.box(T, x0 - tr * n - 0.15, x0 - tr * n + 0.21, rh_ + 0.12, rh_ + 0.18, z - 0.18, z + 0.18, 0.01)
                    self.g.bar(T, (x0 - tr * n + 0.18, rh_ - 0.05, z), (xb, fl + pc.get("rail", 0.8) - 0.02, z), 0.08, 0.06, 0.008)
                if st.get("iron"):
                    zc = st["at"]
                    self.g.bar(self.M["iron"], (x0 - tr * n + 0.1, 0.9, zc), (x0 - 0.05, fl + 0.88, zc), 0.035, 0.035, 0.004)
                    for i in range(0, n + 1, 2):
                        xx = x0 - tr * (n - i) + 0.1; yy = fl * i / n
                        self.g.box(self.M["iron"], xx - 0.012, xx + 0.012, yy, yy + 0.9, zc - 0.012, zc + 0.012, 0.002)
            self.col.append(("box", x0 - tr * n, x0, 0, fl, rz0, rz1))
        self.col.append(("box", x0 - 0.03, x1, 0, fl, z0, z1))
        if pc.get("lamp"):   # a wall lantern beside the door (film 11556: right of the door at the column), lit at night
            lx, lz = pc["lamp"]
            self.g.box(self.M["iron"], lx - 0.09, lx, edge - 1.1, edge - 0.75, lz - 0.08, lz + 0.08, 0.004)
            self.glow.box(self.M["glow"], lx - 0.085, lx - 0.005, edge - 1.06, edge - 0.79, lz - 0.07, lz + 0.07)

    def turret(self, t):
        """Shingle Style turret (Marley's house): an octagon of radius r (to the face middles) from the foundation to `plate`, its windows
        [{k: face 0-7 (0 = +x, counter-clockwise seen from above toward +z), sill, h, w, type}], a flared octagonal cone to `peak`, a finial."""
        cx, cz, r, plate, peak = t["x"], t["z"], t["r"], t["plate"], t["peak"]; fh = self.k.get("foundation_h", 0.6); lod0 = self.lod == 0
        ro = r / math.cos(math.pi / 8); hw = r * math.tan(math.pi / 8)
        for k in range(8):
            a = k * math.pi / 4; n = (math.cos(a), 0.0, math.sin(a)); tg = (-math.sin(a), 0.0, math.cos(a))
            f = OFace((cx + r * n[0], 0.0, cz + r * n[2]), tg, n, hw)
            ws = [dict(w, face="t", at=0.0, _face=f) for w in t.get("windows", []) if w["k"] == k]
            holes = [(-w["w"] / 2, w["w"] / 2, w["sill"], w["sill"] + w["h"]) for w in ws]
            self.wall(-1, None, None, fh, plate, holes, f=f)
            f.box(self.g, self.M["found"], -hw - 0.02, hw + 0.02, -0.3, fh, -0.02, 0.04)
            if lod0: f.box(self.g, self.M["trim"], -hw, hw, plate - 0.25, plate, 0.0, 0.03, 0.004)
            for w in ws: self.window(None, w, self.k["windows"].index(w["_src"]) if w.get("_src") in self.k.get("windows", []) else -1)
        o, fl = t.get("overhang", 0.45), t.get("flare", 0.45); pr = lambda rr, y: [(cx + rr * math.cos((k + 0.5) * math.pi / 4), y, cz + rr * math.sin((k + 0.5) * math.pi / 4)) for k in range(8)]
        he = plate - 0.05; outer = pr(ro + o, he); kink = pr(ro + o - fl, he + fl * math.tan(math.radians(16))); top = (cx, peak, cz); R_ = self.M["roof"]
        for k in range(8):
            a, b = outer[k], outer[(k + 1) % 8]; c, d = kink[(k + 1) % 8], kink[k]; mid = mul(add(a, b), 0.5); out = (mid[0] - cx, 0.4, mid[2] - cz)
            self.g.face(R_, [a, b, c, d], out); self.g.face(R_, [d, c, top], (out[0], 0.6, out[2]))
            self.g.face(self.M["trim"], [a, b, add(b, (0, -0.15, 0)), add(a, (0, -0.15, 0))], (out[0], 0, out[2]))
            wa, wb = pr(ro, he - 0.15)[k], pr(ro, he - 0.15)[(k + 1) % 8]
            self.g.face(self.M["trim"], [add(a, (0, -0.15, 0)), add(b, (0, -0.15, 0)), wb, wa], (0, -1, 0))
        if lod0: self.g.bar(self.M["metal"], (cx, peak - 0.05, cz), (cx, peak + 0.7, cz), 0.05, 0.05, 0.005, up=(1, 0, 0))   # finial
        self.col.append(("box", cx - r, cx + r, 0, plate, cz - r, cz + r))

    def chimney(self, c):
        x, z, w, d, top = c["x"], c["z"], c["w"], c["d"], c["top"]; B = self.M["brick"]; lod0 = self.lod == 0
        y0 = c.get("from", 3.0)
        self.g.box(B, x - w / 2, x + w / 2, y0, top - 0.25, z - d / 2, z + d / 2, 0.006 if lod0 else 0)
        if lod0:
            self.g.box(B, x - w / 2 - 0.05, x + w / 2 + 0.05, top - 0.25, top - 0.12, z - d / 2 - 0.05, z + d / 2 + 0.05, 0.006)
            self.g.box(self.M["cap"], x - w / 2 - 0.07, x + w / 2 + 0.07, top - 0.12, top - 0.04, z - d / 2 - 0.07, z + d / 2 + 0.07, 0.008)
            self.g.box(self.M["iron"], x - 0.11, x + 0.11, top - 0.04, top + 0.12, z - 0.11, z + 0.11, 0.004)
        else:
            self.g.box(self.M["cap"], x - w / 2 - 0.05, x + w / 2 + 0.05, top - 0.25, top - 0.1, z - d / 2 - 0.05, z + d / 2 + 0.05)

    def build(self):
        k = self.k; fh = k.get("foundation_h", 0.6); lod0 = self.lod == 0
        for bi, blk in enumerate(k["blocks"]):
            x0, x1 = blk["x"]; z0, z1 = blk["z"]; plate = blk["plate"]
            self.g.box(self.M["found"], x0 - 0.04, x1 + 0.04, -0.3, fh, z0 - 0.04, z1 + 0.04, 0.01 if lod0 else 0)   # foundation, proud of the cladding
            for side in ("-x", "+x", "-z", "+z"):
                ws = self.openings(bi, side)
                if blk.get("hidden_faces") and side in blk["hidden_faces"]: continue
                holes = [(w["at"] - w["w"] / 2, w["at"] + w["w"] / 2, w["sill"], w["sill"] + w["h"]) for w in ws]
                self.wall(bi, blk, side, fh, plate, holes)
                f = Face(blk, side)
                if lod0 and self.wood:   # water table, frieze
                    f.box(self.g, self.M["trim"], f.span[0] - 0.03, f.span[1] + 0.03, fh, fh + 0.16, 0.0, 0.03, 0.006)
                    f.box(self.g, self.M["trim"], f.span[0] - 0.03, f.span[1] + 0.03, plate - 0.28, plate, 0.0, 0.025, 0.004)
                for w in ws: self.window(blk, w, k["windows"].index(w))
            if lod0 and self.wood:   # corner boards
                for x, z, sx, sz in ((x0, z0, -1, -1), (x1, z0, 1, -1), (x1, z1, 1, 1), (x0, z1, -1, 1)):
                    self.g.box(self.M["trim"], min(x, x + sx * 0.03), max(x, x + sx * 0.03), fh, plate, min(z, z - sz * 0.11), max(z, z - sz * 0.11), 0.004)
                    self.g.box(self.M["trim"], min(x, x - sx * 0.11), max(x, x - sx * 0.11), fh, plate, min(z, z + sz * 0.03), max(z, z + sz * 0.03), 0.004)
            self.roof(blk, bi)
            self.col.append(("box", x0, x1, 0, blk.get("collider_top", plate), z0, z1))   # collider_top: an open porch block is walkable on its floor
        for d in k.get("dormers", []): self.dormer(k["blocks"][d.get("block", 0)], d)
        if k.get("porch"): self.porch(k["porch"])
        for c in k.get("chimneys", []): self.chimney(c)
        for t in k.get("turrets", []): self.turret(t)
        for st in k.get("steps", []):   # free-standing stone steps: n risers up to `top`, climbing toward -x (side A) or +x (side B)
            n_ = st["n"]; x0, x1 = st["x"]; sg = st.get("climb", -1)
            for i in range(n_):
                y = st["top"] * (i + 1) / n_; L = (x1 - x0) * (n_ - i) / n_
                if sg < 0: self.g.box(self.M["cap"], x0, x0 + L, 0, y, st["z"][0], st["z"][1], 0.01 if lod0 else 0)
            for i in range(n_):   # one collider per tread (a single box was a 0.9 m wall to the walker)
                y = st["top"] * (i + 1) / n_; L = (x1 - x0) * (n_ - i) / n_
                self.col.append(("box", x0, x0 + L, 0, y, st["z"][0], st["z"][1]))
        if lod0: self.xmas_extra()
        for g in k.get("garages", []):   # outbuildings: a plain block with an overhead door on its street face
            blk = {"x": g["x"], "z": g["z"], "plate": g["plate"], "roof": g.get("roof", "hip"), "pitch": g.get("pitch", 30), "overhang": 0.3}
            self.g.box(self.M["found"], g["x"][0] - 0.03, g["x"][1] + 0.03, -0.2, 0.15, g["z"][0] - 0.03, g["z"][1] + 0.03)
            f = Face(blk, g.get("door_face", "-x")); dz = g.get("door", [(f.span[0] + f.span[1]) / 2, 2.6])
            holes = [(dz[0] - dz[1] / 2, dz[0] + dz[1] / 2, 0.15, 2.25)]
            for side in ("-x", "+x", "-z", "+z"): self.wall(0, blk, side, 0.15, g["plate"], holes if side == f.side else [])
            f.box(self.g, self.M["trim"], holes[0][0], holes[0][1], 0.15, 2.25, -0.10, -0.06, 0)
            if lod0:
                for i in range(1, 4): f.box(self.g, self.M["trim"], holes[0][0], holes[0][1], 0.15 + 0.525 * i - 0.01, 0.15 + 0.525 * i + 0.01, -0.06, -0.045, 0.004)
            self.roof(blk, -1); self.col.append(("box", g["x"][0], g["x"][1], 0, g["plate"], g["z"][0], g["z"][1]))
        return self


# ---------------------------------------------------------------- Tier 3: an auto kit from the county footprint + lidar
def obb(poly):
    """Minimum-area rectangle of a polygon (spec x, z): (x0, x1, z0, z1, yaw_deg) in the rectangle's own frame."""
    best = None
    for (ax, az), (bx, bz) in zip(poly, poly[1:] + poly[:1]):
        L = math.hypot(bx - ax, bz - az)
        if L < 0.5: continue
        c, s = (bx - ax) / L, (bz - az) / L
        us = [x * c + z * s for x, z in poly]; vs = [-x * s + z * c for x, z in poly]
        A = (max(us) - min(us)) * (max(vs) - min(vs))
        if best is None or A < best[0]: best = (A, min(us), max(us), min(vs), max(vs), math.degrees(math.atan2(s, c)))
    return best[1:]


# ---------------------------------------------------------------- Blender
def to_blender(objs_geo, name, coll, smooth=True):
    import bpy, bmesh
    mats = list(objs_geo.m.keys())
    verts, faces, uvs, fm = [], [], [], []
    for mi, mat in enumerate(mats):
        for pts, uv in objs_geo.m[mat]:
            i = len(verts); verts += [(-p[0], p[2], p[1]) for p in pts]; faces.append(tuple(range(i, i + len(pts)))); uvs.append(uv); fm.append(mi)
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces)
    layer = me.uv_layers.new(name="UVMap")
    for fi, poly in enumerate(me.polygons):
        poly.material_index = fm[fi]
        for li, loop in enumerate(poly.loop_indices): layer.data[loop].uv = uvs[fi][li]
    for mat in mats:
        m = bpy.data.materials.get(mat)
        if m is None:   # a plain material carrying the kit colour (the GLB's preview); Unity and nb_render replace it by name
            m = bpy.data.materials.new(mat); k = mat[3:]; col = next((PAL[c] for c in PAL if k.endswith("_" + c)), [0.6, 0.6, 0.6]); m.diffuse_color = (*col, 1.0)
        me.materials.append(m)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(me); bm.free()
    me.validate(); me.update()
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
    if smooth:
        me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(30))
        wn = ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL"); wn.keep_sharp = True; wn.mode = "FACE_AREA"
        bpy.context.view_layer.objects.active = ob
        for o in bpy.context.view_layer.objects: o.select_set(o == ob)
        bpy.ops.object.modifier_apply(modifier=wn.name)
    return ob


def kit_for(e):
    if e.get("kit"): return e["kit"]
    if e["tier"] == 3 and e.get("kit_auto"): return e["kit_auto"]
    return None


def export_lot(e):
    import bpy
    kit = kit_for(e)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    coll = bpy.context.scene.collection
    h0 = House(e["id"], kit, 0).build() if e["tier"] <= 2 else None
    h1 = House(e["id"], kit, 1).build()
    yaw = math.radians(kit.get("yaw_deg", 0.0))
    if yaw:   # Tier 3 kits are built in their footprint rectangle's frame: turn them into spec (rotation about y: windings kept)
        c, s_ = math.cos(yaw), math.sin(yaw); R = lambda p: (p[0] * c - p[2] * s_, p[1], p[0] * s_ + p[2] * c)
        for h in (h0, h1):
            if not h: continue
            for gg in (h.g, h.glow):
                for mat in gg.m: gg.m[mat] = [([R(q) for q in pts], uv) for pts, uv in gg.m[mat]]
            h.col = []; h.bulbs = [[round(c * b[0] - s_ * b[2], 3), b[1], round(s_ * b[0] + c * b[2], 3), b[3]] for b in h.bulbs]
    objs = []
    if h0: objs.append(to_blender(h0.g, f"{e['id']}_LOD0", coll))
    objs.append(to_blender(h1.g, f"{e['id']}_LOD1", coll))
    glow = (h0 or h1).glow
    if glow.m: objs.append(to_blender(glow, f"{e['id']}_NightGlow", coll, smooth=False))
    cg = Geo()
    if not (h0 or h1).col: cg.box("NB_Collider", 0, 0.01, -5, -4.99, 0, 0.01)
    for _, x0, x1, y0, y1, z0, z1 in (h0 or h1).col: cg.box("NB_Collider", x0, x1, y0, y1, z0, z1)
    objs.append(to_blender(cg, f"{e['id']}_Collider", coll, smooth=False))
    root = bpy.data.objects.new(f"{e['id']}_Root", None); coll.objects.link(root)
    root["lot"] = e["id"]; root["tier"] = e["tier"]; root["confidence"] = e.get("confidence", "low")
    for o in objs: o.parent = root
    bpy.context.view_layer.update()   # objects linked after the last operator are not in view_layer.objects until an update (Tier 3 GLBs lost all but LOD1)
    for o in coll.objects: o.select_set(True)
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / f"{e['id']}.glb"), export_format="GLB", export_yup=True, export_apply=True, use_selection=True,
                              export_extras=True, export_materials="EXPORT")
    hb = h0 or h1   # step 3: the backdrop (LOD1-only) houses carry eave strings too
    if hb.bulbs:
        (OUT / f"{e['id']}_xmas.json").write_text(json.dumps({"lot": e["id"], "frame": "spec x, y over the lot grade, z; colour 0 red 1 green 2 amber 3 blue 4 white", "bulbs": hb.bulbs}))
    elif (OUT / f"{e['id']}_xmas.json").exists(): (OUT / f"{e['id']}_xmas.json").unlink()
    mats = sorted(set((h0 or h1).g.m) | set(h1.g.m))
    st = {"tier": e["tier"], "lod0_tris": h0.g.tris() if h0 else 0, "lod1_tris": h1.g.tris(), "glow_tris": glow.tris(), "bulbs": len(hb.bulbs), "materials": mats}
    if h0: st["lod1_ratio"] = round(st["lod1_tris"] / max(1, st["lod0_tris"]), 3)
    return st


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    lots = [e for e in MAN["parcels"] if kit_for(e) and (not args or e["id"] in args)]
    stats_p = ROOT / "art/home_alone/references/neighborhood/build_stats.json"
    stats = json.loads(stats_p.read_text()) if stats_p.exists() else {}
    for e in lots:
        stats[e["id"]] = export_lot(e); print("nb_house", e["id"], stats[e["id"]])
    stats_p.write_text(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
