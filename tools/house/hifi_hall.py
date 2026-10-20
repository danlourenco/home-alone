"""hifi_hall: the upstairs hall's generated pieces (Oct 16 2026, TRIAL; changes/2026-10-16-upstairs-hall.json), from spec/dressing/hall.json
and spec/geometry.json (upstairs). Spec metres, y above the upper floor. Film first (DEVIATIONS 1, 63).

- RUNNER: the fitted crimson runner (one outline, 1.2 cm proud of the floor, rounded edge)
- CROWN: a cove-and-ogee crown (8 cm drop, 7 cm projection) along every hall wall that reaches the ceiling (film 410, 2296), mitred
  at the corners (inside and outside), stopped square where the wall ends at the stair well
- SCONCES (4): oval brass backplate, swept arm, brass fitter, a frosted fluted tulip shade open at the top (3 mm glass), a candle bulb
- URN STANDS (3): turned dark-wood stand on cross feet carrying a fluted black urn (the poinsettias go in from hall_purchased.py)
- PICTURES: moulded mahogany or gilt frames mitred at the corners, a cream mat with a bevelled window, the art set back behind the mat
  (public-domain atlas spec/dressing/hall_art.png, hall_textures.py); the tapestry on a brass rod with finials
- CLOCK / BAROMETER: wooden plaque with two brass bezels and dials (invented faces in the atlas)
- TABLE DRESSING: brass globe on a turned stand with its meridian ring, brass candlesticks with red tapers, two easel-backed photographs
- BRASS POT for the floor poinsettia (ribbed, as the film's 410)

Artist pipeline (.claude/skills/artist-pipeline): curves are true revolves with segment counts from the chord error (<= 1 mm per metre of
radius: n >= pi / acos(1 - 0.001), so 72 around anything round), every hard edge bevelled (Bevel modifier, 2-4 mm by material, angle
limit 30 deg) with weighted normals; parts built with hifi_lib.Part.face (faces outward by construction). Not done here (the helpers
in hifi_lib / model_quality.py were not there yet): high-poly bakes (normal/AO/curvature maps) and LODs; the Unity materials are
map-driven world-space textures (cherry_veneer, dirty_carpet) and the shared brass. One LOD: every piece is small and hall-sized.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_hall.py
  -> unity/HomeAlone/Assets/Models/Foyer/HallDressing.glb (placed by SpecGreybox.Hall)
"""
import json
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/HallDressing.glb"
D = json.loads((ROOT / "spec/dressing/hall.json").read_text())
G = json.loads((ROOT / "spec/geometry.json").read_text())["upstairs"]
ATLAS = json.loads((ROOT / "spec/dressing/hall_art.json").read_text())["pictures"]
HALLS = ("hall_end", "hall_corridor", "hall_corridor_south", "main_stair_opening")   # the stair well too (film 2085: its crown runs round the damask walls and over the gallery arch; walk note 2026-10-19T20:57:39 "the casing/molding at the top stopping abruptly": it stopped where the corridor outline met the well)
NROUND = 72

parts = {}


def part(name, mat):
    if name not in parts:
        parts[name] = Part(name, mat)
    return parts[name]


def add(a, b, k=1.0):
    return tuple(x + k * y for x, y in zip(a, b))


def scale(a, k):
    return tuple(k * x for x in a)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


# ---------------------------------------------------------------- primitives
def revolve(p, origin, A, U, prof, n=NROUND, closed=False, flutes=0, famp=0.0, smooth=True):
    """prof [(h along A, r)]: a turned part about the axis through origin along A (unit); U a unit radial vector. closed=True: prof is a
    closed loop (a shell with thickness: no caps). flutes: radius modulated r * (1 + famp * cos(flutes * angle)) on segments marked."""
    V = cross(A, U)
    if smooth and not closed and len(prof) > 2:   # Chaikin x2: turned profiles become smooth curves, sharp corners get a small round
        for _ in range(2):
            q = [prof[0]]
            for (h0, r0), (h1, r1) in zip(prof, prof[1:]):
                q += [(0.75 * h0 + 0.25 * h1, 0.75 * r0 + 0.25 * r1), (0.25 * h0 + 0.75 * h1, 0.25 * r0 + 0.75 * r1)]
            q.append(prof[-1]); prof = q

    if n == NROUND:   # segments from the largest radius: chord error <= 0.5 mm (artist pipeline), at least 12
        rmax = max(r for _, r in prof) * (1 + famp)
        n = max(12, math.ceil(math.pi / math.acos(max(-1.0, 1 - 0.0005 / max(rmax, 1e-4)))))
        if flutes:
            n = max(n, flutes * 6)

    def pt(h, r, k):
        a = 2 * math.pi * k / n; rr = r * (1 + famp * math.cos(flutes * a)) if flutes else r
        return add(add(origin, A, h), add(scale(U, rr * math.cos(a)), scale(V, rr * math.sin(a))))
    m = len(prof); segs = m if closed else m - 1
    area = sum(prof[i][0] * prof[(i + 1) % m][1] - prof[(i + 1) % m][0] * prof[i][1] for i in range(m))
    for j in range(segs):
        (h0, r0), (h1, r1) = prof[j], prof[(j + 1) % m]
        nh, nr = -(r1 - r0), (h1 - h0)                      # left normal in (h, r)
        if closed and area > 0:
            nh, nr = -nh, -nr                                # a counter-clockwise loop: outward is the right normal
        for k in range(n):
            a = 2 * math.pi * (k + 0.5) / n
            radial = add(scale(U, math.cos(a)), scale(V, math.sin(a)))
            q = [pt(h0, r0, k), pt(h1, r1, k), pt(h1, r1, k + 1), pt(h0, r0, k + 1)]
            if r0 < 1e-6:
                q = [q[0], q[1], q[2]]
            elif r1 < 1e-6:
                q = [q[0], q[1], q[3]]
            p.face(q, add(scale(radial, nr), scale(A, nh)))
    if not closed:
        for (h, r), s in ((prof[0], -1), (prof[-1], 1)):
            if r > 1e-6:
                p.face([pt(h, r, k) for k in range(n)], scale(A, s))


def run(p, base, t, nvec, bvec, L, prof, k0, k1, caps=(False, False)):
    """a profile [(a along nvec, b along bvec)] (closed loop) swept straight along t for length L from base; the ends mitred: a profile
    point at a starts at t * (k0 * a) and ends at L + t * (k1 * a) (k = +1 inside corner, -1 outside corner, 0 square)"""
    m = len(prof)
    area = sum(prof[i][0] * prof[(i + 1) % m][1] - prof[(i + 1) % m][0] * prof[i][1] for i in range(m))
    S = [add(add(base, t, k0 * a), add(scale(nvec, a), scale(bvec, b))) for a, b in prof]
    E = [add(add(base, t, L + k1 * a), add(scale(nvec, a), scale(bvec, b))) for a, b in prof]
    for j in range(m):
        (a0, b0), (a1, b1) = prof[j], prof[(j + 1) % m]
        na, nb = -(b1 - b0), (a1 - a0)
        if area > 0:
            na, nb = -na, -nb
        p.face([S[j], S[(j + 1) % m], E[(j + 1) % m], E[j]], add(scale(nvec, na), scale(bvec, nb)))
    if caps[0]:
        p.face(S, scale(t, -1))
    if caps[1]:
        p.face(E, t)


def loop_frame(p, corners, inward_b, prof):
    """a closed rectangular loop of a profile (picture frame, mat): corners (4, in order around the loop) in 3D; prof [(a toward the
    loop's centre from its outer edge, b out of the wall along inward_b)]; mitred at every corner"""
    cx = scale(add(add(corners[0], corners[1]), add(corners[2], corners[3])), 0.25)
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        t = tuple(y - x for x, y in zip(a, b)); L = math.sqrt(sum(c * c for c in t)); t = scale(t, 1 / L)
        mid = scale(add(a, b), 0.5); toc = tuple(c - m for c, m in zip(cx, mid))
        nvec = add(toc, t, -sum(x * y for x, y in zip(toc, t))); nl = math.sqrt(sum(c * c for c in nvec)); nvec = scale(nvec, 1 / nl)
        run(p, a, t, nvec, inward_b, L, prof, 1, -1)


class Wall:
    """a wall from hall.json: P(s, y, d) = the point s along the wall, height y, d out from its face into the room"""
    def __init__(self, key):
        w = D["walls"][key]; self.ax, self.f, self.side = w["axis"], w["face"], w["room_side"]

    def P(self, s, y, d):
        return (self.f + self.side * d, y, s) if self.ax == "x" else (s, y, self.f + self.side * d)

    @property
    def n(self):   # into the room
        return (self.side, 0, 0) if self.ax == "x" else (0, 0, self.side)

    @property
    def t(self):   # along s
        return (0, 0, 1) if self.ax == "x" else (1, 0, 0)

    def u_flip(self):   # does +s run to the viewer's LEFT when facing the wall from the room?
        right = cross(scale(self.n, -1), (0, 1, 0))   # spec space is right-handed: looking along f = -n with y up, right = f x y
        return sum(a * b for a, b in zip(right, self.t)) < 0


# ---------------------------------------------------------------- runner
def runner():
    r = D["runner"]; pts = r["outline"]; y0, y1 = 0.001, 0.001 + r["thickness"] + 0.002   # top 1.3 cm: overlays >= 1 cm proud
    p = part("Runner", "HL_Runner")
    p.face([(x, y1, z) for x, z in pts], (0, 1, 0)); p.face([(x, y0, z) for x, z in pts], (0, -1, 0))
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))
    for (xa, za), (xb, zb) in zip(pts, pts[1:] + pts[:1]):
        e = (xb - xa, zb - za); nrm = (e[1], -e[0]) if area > 0 else (-e[1], e[0])
        p.face([(xa, y0, za), (xb, y0, zb), (xb, y1, zb), (xa, y1, za)], (nrm[0], 0, nrm[1]))


# ---------------------------------------------------------------- crown
CROWN = [(-0.003, 0.003), (-0.003, -0.080), (0.004, -0.080), (0.008, -0.076), (0.012, -0.071), (0.018, -0.068), (0.026, -0.061),
         (0.032, -0.052), (0.036, -0.044), (0.042, -0.036), (0.050, -0.030), (0.058, -0.024), (0.064, -0.016), (0.067, -0.010),
         (0.068, -0.006), (0.071, -0.004), (0.071, 0.003)]   # (out from the wall, up from the ceiling); hidden 3 mm into wall and ceiling


def wall_at(x, z, y):
    return any(w["x"][0] - 1e-4 <= x <= w["x"][1] + 1e-4 and w["z"][0] - 1e-4 <= z <= w["z"][1] + 1e-4 and w["y"][0] <= y <= w["y"][1] for w in G["walls"])


def crown():
    p = part("Crown", "HL_White")
    rooms = {r["name"]: r for r in G["rooms"]}
    for name in HALLS:
        rm = rooms[name]; c = rm["ceil"]; P2 = [tuple(q) for q in rm["poly"]]
        P2 = [q for i, q in enumerate(P2) if math.dist(q, P2[i - 1]) > 1e-4]
        P2 = [q for i, q in enumerate(P2) if abs((q[0] - P2[i - 1][0]) * (P2[(i + 1) % len(P2)][1] - q[1]) - (q[1] - P2[i - 1][1]) * (P2[(i + 1) % len(P2)][0] - q[0])) > 1e-6]   # drop collinear vertices: one run, no false mitre
        n = len(P2); sg = 1 if sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(P2, P2[1:] + P2[:1])) > 0 else -1

        def turn(i):   # > 0: the room's convex (inside) corner at vertex i
            a, b, cc = P2[i - 1], P2[i], P2[(i + 1) % n]
            d1 = (b[0] - a[0], b[1] - a[1]); d2 = (cc[0] - b[0], cc[1] - b[1]); return sg * (d1[0] * d2[1] - d1[1] * d2[0])
        for i in range(n):
            a, b = P2[i], P2[(i + 1) % n]; L = math.dist(a, b); t2 = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
            nin = (-sg * t2[1], sg * t2[0])                                   # into the room
            y = c - 0.04
            on = [wall_at(a[0] + t2[0] * s - nin[0] * 0.004, a[1] + t2[1] * s - nin[1] * 0.004, y) for s in [L * (k + 0.5) / 200 for k in range(200)]]
            k = 0
            while k < 200:   # each walled stretch of the edge
                if not on[k]:
                    k += 1; continue
                j = k
                while j < 200 and on[j]:
                    j += 1
                s0, s1 = L * k / 200, L * j / 200
                full0, full1 = k == 0, j == 200
                k0 = (1 if turn(i) > 0 else -1) if full0 and wall_end_turns(P2, i, sg, y) else 0
                k1 = (1 if turn((i + 1) % n) > 0 else -1) if full1 and wall_end_turns(P2, (i + 1) % n, sg, y, prev=True) else 0
                base = (a[0] + t2[0] * s0, c, a[1] + t2[1] * s0)
                run(p, base, (t2[0], 0, t2[1]), (nin[0], 0, nin[1]), (0, 1, 0), s1 - s0, CROWN, k0, -k1, caps=(k0 == 0, k1 == 0))
                print(f"  crown {name} edge {i}: {s1 - s0:.2f} m from ({base[0]:.2f}, {base[2]:.2f}), ends {k0:+d}/{k1:+d}")
                k = j


def wall_end_turns(P2, i, sg, y, prev=False):
    """the crown turns the corner at vertex i (the other edge at it also has wall there), else it stops square"""
    n = len(P2); a = P2[i]; o = P2[i - 1] if not prev else P2[(i + 1) % n]
    L = math.dist(a, o); t2 = ((o[0] - a[0]) / L, (o[1] - a[1]) / L); nin = (-t2[1], t2[0])
    for s in (0.02, 0.05):
        for sgn in (1, -1):
            if wall_at(a[0] + t2[0] * s + sgn * nin[0] * 0.004, a[1] + t2[1] * s + sgn * nin[1] * 0.004, y):
                return True
    return False


# ---------------------------------------------------------------- sconces
def sconce(wall, s, q):
    W = Wall(wall); brass = part("Brass", "HL_Brass"); glass = part("Shade", "HL_Shade"); bulb = part("Bulb", "HL_Bulb")
    gb, gt, rt = q["glass_bottom"], q["glass_top"], q["glass_top_dia"] / 2; pw, ph = q["plate"]
    yc = gb - 0.075; dc = 0.13                                           # plate centre below the shade (film 1333); shade axis 13 cm off the wall
    # oval backplate, 1.4 cm thick with a rounded front edge, 2 mm off the wall
    ring = [(s + pw / 2 * math.cos(2 * math.pi * k / NROUND), yc + ph / 2 * math.sin(2 * math.pi * k / NROUND)) for k in range(NROUND)]
    inner = [(s + (pw / 2 - 0.006) * math.cos(2 * math.pi * k / NROUND), yc + (ph / 2 - 0.006) * math.sin(2 * math.pi * k / NROUND)) for k in range(NROUND)]
    for k in range(NROUND):
        k2 = (k + 1) % NROUND
        brass.face([W.P(*ring[k], 0.002), W.P(*ring[k2], 0.002), W.P(*ring[k2], 0.011), W.P(*ring[k], 0.011)],
                   add(scale(W.t, ring[k][0] - s), (0, ring[k][1] - yc, 0)))
        brass.face([W.P(*ring[k], 0.011), W.P(*ring[k2], 0.011), W.P(*inner[k2], 0.016), W.P(*inner[k], 0.016)], W.n)
    brass.face([W.P(*v, 0.016) for v in inner], W.n); brass.face([W.P(*v, 0.002) for v in ring], scale(W.n, -1))
    # arm: a 1.1 cm rod from the plate out and up to the fitter (quarter bend), swept round section
    path = [W.P(s, yc, 0.014)] + [W.P(s, yc + 0.045 * (1 - math.cos(a)), 0.016 + (dc - 0.016) * math.sin(a)) for a in [math.pi / 2 * k / 12 for k in range(1, 13)]]
    path.append(W.P(s, gb - 0.02, dc))
    brass.sweep(path, [(0.0055 * math.cos(2 * math.pi * k / 16), 0.0055 * math.sin(2 * math.pi * k / 16)) for k in range(16)])
    axis_o = W.P(s, 0, dc)
    revolve(brass, (axis_o[0], gb - 0.02, axis_o[2]), (0, 1, 0), (1, 0, 0),
            [(0, 0.008), (0.006, 0.014), (0.018, 0.030), (0.024, 0.034), (0.026, 0.033), (0.026, 0.031), (0.020, 0.029), (0.008, 0.012), (0.004, 0.0)], closed=True)   # fitter cup (a 2 mm shell: the glass seats in it)
    # frosted fluted tulip, 3 mm wall, open at the top, its foot inside the cup's rim (2 mm above it: no part crosses the brass)
    outer = [(0.0, 0.027), (0.03, 0.040), (0.07, 0.054), (0.11, 0.064), (0.15, 0.071), (0.18, 0.075), (gt - gb, rt)]
    inner_p = [(h, r - 0.003) for h, r in reversed(outer)]
    shell = outer + [(gt - gb + 0.001, rt - 0.0015)] + inner_p + [(0.004, 0.0)]
    revolve(glass, (axis_o[0], gb + 0.008, axis_o[2]), (0, 1, 0), (1, 0, 0), shell, closed=True, flutes=16, famp=0.03)
    revolve(bulb, (axis_o[0], gb + 0.017, axis_o[2]), (0, 1, 0), (1, 0, 0),
            [(0, 0.0)] + [(0.04 + 0.03 * (1 - math.cos(a)), 0.014 * math.sin(a)) for a in [math.pi * k / 12 for k in range(1, 12)]] + [(0.10, 0.0)], n=24)


# ---------------------------------------------------------------- urn stands
def urn(wall, s, q):
    W = Wall(wall); wood = part("Wood", "HL_Wood"); black = part("Urn", "HL_Black"); soil = part("Soil", "HL_Soil")
    r_st = q["stand_dia"] / 2; d = 0.03 + r_st                              # 3 cm off the wall (clear of the cap rail)
    c = W.P(s, 0, d); cx, cz = c[0], c[2]
    for k in range(4):   # cross feet: four tapered arms with a bun at each tip
        a = math.pi / 4 + math.pi / 2 * k; ux, uz = math.cos(a), math.sin(a); vx, vz = -uz, ux
        L = r_st - 0.025; w0, w1 = 0.018, 0.012
        q4 = lambda l, w, y: (cx + ux * l + vx * w, y, cz + uz * l + vz * w)
        pts_b = [q4(0, -w0, 0.025), q4(L, -w1, 0.025), q4(L, w1, 0.025), q4(0, w0, 0.025)]
        pts_t = [q4(0, -w0, 0.060), q4(L, -w1, 0.045), q4(L, w1, 0.045), q4(0, w0, 0.060)]
        wood.face(pts_t, (0, 1, 0)); wood.face(pts_b, (0, -1, 0))
        for i, nv in enumerate([(vx * -1, 0, vz * -1), (ux, 0, uz), (vx, 0, vz), (-ux, 0, -uz)]):
            j = (i + 1) % 4; wood.face([pts_b[i], pts_b[j], pts_t[j], pts_t[i]], nv)
        revolve(wood, (cx + ux * (L - 0.005), 0.0, cz + uz * (L - 0.005)), (0, 1, 0), (1, 0, 0), [(0.0, 0.014), (0.012, 0.018), (0.026, 0.016), (0.03, 0.0)], n=36)
    col = [(0.04, 0.032), (0.07, 0.034), (0.08, 0.026), (0.12, 0.022), (0.17, 0.040), (0.21, 0.044), (0.25, 0.034), (0.29, 0.022),
           (0.31, 0.022), (0.33, 0.030), (0.345, 0.022), (0.37, 0.024), (0.385, 0.070), (0.40, 0.072), (0.40, 0.0)]
    revolve(wood, (cx, 0.0, cz), (0, 1, 0), (1, 0, 0), [(0.04, 0.0)] + col)
    h = q["height"]; rb = q["bowl_dia"] / 2
    revolve(black, (cx, 0.0, cz), (0, 1, 0), (1, 0, 0),
            [(0.402, 0.0), (0.402, 0.060), (0.412, 0.062), (0.420, 0.045), (0.435, 0.048), (0.47, 0.085), (0.52, 0.120), (0.57, 0.138),
             (h - 0.015, 0.146), (h - 0.008, rb), (h, rb), (h, rb - 0.008), (h - 0.012, rb - 0.010), (h - 0.03, 0.0)], flutes=24, famp=0.02)
    revolve(soil, (cx, h - 0.022, cz), (0, 1, 0), (1, 0, 0), [(0.0, 0.0), (0.0, rb - 0.012), (0.004, rb - 0.012), (0.004, 0.0)])
    return cx, cz


# ---------------------------------------------------------------- pictures
FRAME_PROF = {   # (a from the outer edge toward the centre, b out of the wall)
    "mahogany": [(0.0, 0.003), (0.0, 0.020), (0.004, 0.026), (0.010, 0.029), (0.018, 0.028), (0.026, 0.024), (0.031, 0.021), (0.035, 0.018), (0.035, 0.009), (0.028, 0.009), (0.028, 0.003)],
    "gilt": [(0.0, 0.003), (0.0, 0.016), (0.003, 0.022), (0.008, 0.026), (0.013, 0.024), (0.017, 0.027), (0.022, 0.025), (0.027, 0.020), (0.030, 0.017), (0.030, 0.009), (0.024, 0.009), (0.024, 0.003)],
}


def scaled(prof, w):
    w0 = max(a for a, b in prof); return [(a * w / w0, b) for a, b in prof]


def picture(p):
    W = Wall(p["wall"]); s0, s1 = p["s"]; y0, y1 = p["y"]; kind = p["frame"]
    uv = ATLAS[p["key"]]["uv"]; flip = W.u_flip()
    ua, ub = (uv[2], uv[0]) if flip else (uv[0], uv[2])
    art = part("Art", "HL_Art")
    if kind == "tapestry":
        cloth = part("Cloth", "HL_Art"); brass = part("Brass", "HL_Brass")
        corners = [W.P(s0, y0, 0.012), W.P(s1, y0, 0.012), W.P(s1, y1, 0.012), W.P(s0, y1, 0.012)]
        art.face(corners, W.n, [(ua, uv[1]), (ub, uv[1]), (ub, uv[3]), (ua, uv[3])])
        back = [W.P(s0, y0, 0.004), W.P(s1, y0, 0.004), W.P(s1, y1, 0.004), W.P(s0, y1, 0.004)]
        cloth.face(back, scale(W.n, -1))
        for a, b, nv in ((0, 1, (0, -1, 0)), (1, 2, W.t), (2, 3, (0, 1, 0)), (3, 0, scale(W.t, -1))):
            cloth.face([back[a], back[b], corners[b], corners[a]], nv)
        rod = [W.P(s0 - 0.04, y1 + 0.012, 0.03), W.P(s1 + 0.04, y1 + 0.012, 0.03)]
        brass.sweep(rod, [(0.007 * math.cos(2 * math.pi * k / 24), 0.007 * math.sin(2 * math.pi * k / 24)) for k in range(24)])
        for e, sg in ((s0 - 0.04, -1), (s1 + 0.04, 1)):
            o = W.P(e, y1 + 0.012, 0.03)
            revolve(brass, o, scale(W.t, sg), (0, 1, 0), [(0.0, 0.010), (0.010, 0.014), (0.022, 0.012), (0.034, 0.006), (0.040, 0.0)], n=36)
        for e in (s0 + 0.02, s1 - 0.02):   # brackets from the wall
            o0 = W.P(e, y1 + 0.012, 0.002)
            revolve(brass, o0, W.n, (0, 1, 0), [(0.0, 0.012), (0.004, 0.012), (0.006, 0.005), (0.028, 0.004), (0.028, 0.0)], n=24)
        return
    small = s1 - s0 < 0.2
    fw = 0.018 if small else (0.035 if kind == "mahogany" else 0.03)
    fp = part("FrameWood" if kind == "mahogany" else "Gilt", "HL_Wood" if kind == "mahogany" else "HL_Gilt")
    loop_frame(fp, [W.P(s0, y0, 0), W.P(s1, y0, 0), W.P(s1, y1, 0), W.P(s0, y1, 0)], W.n, scaled(FRAME_PROF[kind], fw))
    m = p.get("mat", 0.0); ia0, ia1, iy0, iy1 = s0 + fw, s1 - fw, y0 + fw, y1 - fw     # the frame's sight opening
    wa0, wa1, wy0, wy1 = ia0 + m, ia1 - m, iy0 + m, iy1 - m                              # the mat's window
    if m > 0.004:
        bev = min(0.003, m / 3)
        loop_frame(part("Mat", "HL_Mat"), [W.P(ia0 - 0.006, iy0 - 0.006, 0), W.P(ia1 + 0.006, iy0 - 0.006, 0), W.P(ia1 + 0.006, iy1 + 0.006, 0), W.P(ia0 - 0.006, iy1 + 0.006, 0)],
                   W.n, [(0.0, 0.0135), (0.0, 0.0165), (m + 0.006 - bev, 0.0165), (m + 0.006, 0.0135)])   # 1.35-1.65 cm out: >= 1 cm off the wall, under the frame lip (1.8)
    e = 0.0005   # the art fills the mat's window (no wider: nothing of it lies under the mat within 1 cm)
    art.face([W.P(wa0 - e, wy0 - e, 0.0115), W.P(wa1 + e, wy0 - e, 0.0115), W.P(wa1 + e, wy1 + e, 0.0115), W.P(wa0 - e, wy1 + e, 0.0115)],
             W.n, [(ua, uv[1]), (ub, uv[1]), (ub, uv[3]), (ua, uv[3])])


def clock_barometer():
    q = D["clock_barometer"]; W = Wall(q["wall"]); s, (y0, y1), w, dd = q["s"], q["y"], q["width"], q["dial"]
    wood = part("Wood", "HL_Wood"); brass = part("Brass", "HL_Brass"); art = part("Art", "HL_Art")
    # the plaque: a rounded-end board, 2.2 cm thick, 2 mm off the wall
    r = w / 2; ring = []
    for k in range(37):
        a = math.pi * k / 36; ring.append((s + r * math.cos(a), y1 - r + r * math.sin(a)))
    for k in range(37):
        a = math.pi + math.pi * k / 36; ring.append((s + r * math.cos(a), y0 + r + r * math.sin(a)))
    loop = [W.P(a, b, 0.002) for a, b in ring]; front = [W.P(a, b, 0.024) for a, b in ring]
    wood.face(front, W.n); wood.face(loop, scale(W.n, -1))
    for k in range(len(ring)):
        k2 = (k + 1) % len(ring); mid = ((ring[k][0] + ring[k2][0]) / 2 - s, (ring[k][1] + ring[k2][1]) / 2 - (y0 + y1) / 2)
        wood.face([loop[k], loop[k2], front[k2], front[k]], add(scale(W.t, mid[0]), (0, mid[1], 0)))
    for key, yc in (("clock", y1 - r), ("barometer", y0 + r)):
        o = W.P(s, yc, 0.024)
        revolve(brass, o, W.n, (0, 1, 0), [(0.0, dd / 2 + 0.012), (0.010, dd / 2 + 0.013), (0.020, dd / 2 + 0.010), (0.024, dd / 2 + 0.002),
                                          (0.022, dd / 2 - 0.002), (0.012, dd / 2 - 0.004), (0.006, dd / 2 - 0.004), (0.006, 0.0)])
        uv = ATLAS[key]["uv"]; n = NROUND; cu, cv, ru, rv = (uv[0] + uv[2]) / 2, (uv[1] + uv[3]) / 2, (uv[2] - uv[0]) / 2, (uv[3] - uv[1]) / 2
        fl = -1 if W.u_flip() else 1; rd = dd / 2 - 0.004
        pts = [W.P(s + rd * math.cos(2 * math.pi * k / n), yc + rd * math.sin(2 * math.pi * k / n), 0.041) for k in range(n)]   # 1.1 cm proud of the bezel's back disk (d 0.030), 7 mm behind its lip
        art.face(pts, W.n, [(cu + fl * ru * math.cos(2 * math.pi * k / n), cv + rv * math.sin(2 * math.pi * k / n)) for k in range(n)])


def table_dressing():
    td = D["table_dressing"]; C = D["consoles"]; brass = part("Brass", "HL_Brass"); wax = part("Candle", "HL_Candle")
    def on(cons, s, d=None):
        c = C[cons]; W = Wall(c["wall"]); return W, W.P(s, c["top"], 0.03 + (c["depth"] / 2 if d is None else d))
    g = td["globe"]; W, o = on(g["console"], g["s"], 0.03 + 0.13); R = g["dia"] / 2
    revolve(brass, o, (0, 1, 0), (1, 0, 0), [(0.0, 0.055), (0.008, 0.058), (0.016, 0.050), (0.022, 0.024), (0.06, 0.012), (0.075, 0.018),
                                            (0.085, 0.010), (0.125, 0.008), (0.125, 0.0)])   # the spindle runs 5 mm into the globe
    cy = o[1] + 0.12 + R
    revolve(brass, (o[0], cy - R, o[2]), (0, 1, 0), (1, 0, 0), [(0.0, 0.0)] + [(R * (1 - math.cos(a)), R * math.sin(a)) for a in [math.pi * k / 36 for k in range(1, 36)]] + [(2 * R, 0.0)])
    tilt = math.radians(23.5); A = (math.sin(tilt) * W.t[0], math.cos(tilt), math.sin(tilt) * W.t[2])     # the meridian ring's plane holds the tilted axis
    U = W.n
    path = [add((o[0], cy, o[2]), add(scale(A, (R + 0.009) * math.cos(2 * math.pi * k / 96)), scale(cross(A, U), (R + 0.009) * math.sin(2 * math.pi * k / 96)))) for k in range(97)]
    brass.sweep(path[:-1] + [path[0]], [(0.004, 0.003), (-0.004, 0.003), (-0.004, -0.003), (0.004, -0.003)])
    for cn, (sa, sb) in [(c["console"], c["s"]) for c in td["candles"]]:
        for s in (sa, sb):
            W, o = on(cn, s, 0.03 + 0.08)
            revolve(brass, o, (0, 1, 0), (1, 0, 0), [(0.0, 0.045), (0.006, 0.047), (0.014, 0.040), (0.020, 0.018), (0.05, 0.010), (0.06, 0.016), (0.07, 0.009),
                                                    (0.15, 0.011), (0.17, 0.016), (0.19, 0.012), (0.205, 0.020), (0.215, 0.020), (0.215, 0.0)])
            revolve(wax, (o[0], o[1] + 0.205, o[2]), (0, 1, 0), (1, 0, 0), [(0.0, 0.0), (0.0, 0.0115), (td["candle_h"] - 0.02, 0.010), (td["candle_h"] - 0.005, 0.006), (td["candle_h"], 0.0)], n=48)
    for i, ph in enumerate(td["photos"]):   # easel-backed photograph frames, leaning back 12 degrees
        W, o = on("parents", ph["s"], 0.03 + 0.08); w, h = ph["w"], ph["h"]; lean = math.radians(12)
        up = add(scale((0, 1, 0), math.cos(lean)), scale(W.n, -math.sin(lean))); fwd = add(scale(W.n, math.cos(lean)), scale((0, 1, 0), math.sin(lean)))
        corner = lambda a, b, dd: add(add(o, W.t, a), add(scale(up, b), scale(fwd, dd)))
        gp = part("Gilt", "HL_Gilt")
        loop_frame(gp, [corner(-w / 2, 0, 0), corner(w / 2, 0, 0), corner(w / 2, h, 0), corner(-w / 2, h, 0)], fwd,
                   [(0.0, 0.0), (0.0, 0.010), (0.006, 0.014), (0.015, 0.010), (0.015, 0.004), (0.012, 0.0)])
        uv = ATLAS[f"photo{i + 1}"]["uv"]; fl = W.u_flip(); ua, ub = (uv[2], uv[0]) if fl else (uv[0], uv[2])
        part("Art", "HL_Art").face([corner(-w / 2 + 0.013, 0.013, 0.006), corner(w / 2 - 0.013, 0.013, 0.006), corner(w / 2 - 0.013, h - 0.013, 0.006), corner(-w / 2 + 0.013, h - 0.013, 0.006)],
                                   fwd, [(ua, uv[1]), (ub, uv[1]), (ub, uv[3]), (ua, uv[3])])
        st = [corner(-0.006, h * 0.6, 0.0), corner(0.006, h * 0.6, 0.0), add(o, add(scale(W.n, -0.07), scale(W.t, 0.006))), add(o, add(scale(W.n, -0.07), scale(W.t, -0.006)))]
        part("FrameWood", "HL_Wood").face(st, scale(W.n, -1))


def floor_pot():
    q = D["floor_pot"]; cx, cz = q["at"]; r, h = q["dia"] / 2, q["height"]
    prof = [(0.0, 0.0), (0.0, r * 0.78), (0.01, r * 0.80), (h * 0.85, r * 0.98), (h * 0.92, r), (h, r), (h, r - 0.006), (h * 0.9, r - 0.012), (h * 0.9, 0.0)]
    revolve(part("Brass", "HL_Brass"), (cx, 0.0, cz), (0, 1, 0), (1, 0, 0), prof, flutes=28, famp=0.025)
    revolve(part("Soil", "HL_Soil"), (cx, h * 0.9 + 0.008, cz), (0, 1, 0), (1, 0, 0), [(0.0, 0.0), (0.0, r - 0.014), (0.004, r - 0.014), (0.004, 0.0)])


runner(); crown()
for q in D["sconces"]["at"]:
    sconce(q["wall"], q["s"], D["sconces"])
for q in D["urns"]["at"]:
    urn(q["wall"], q["s"], D["urns"])
for p in D["pictures"]:
    picture(p)
clock_barometer(); table_dressing(); floor_pot()

# ---------------------------------------------------------------- export (bevels + weighted normals: the artist pipeline by hand)
bpy.ops.wm.read_factory_settings(use_empty=True)


def tex_material(name, img_path, rough):
    m = material(name, (1, 1, 1), rough)
    nt = m.node_tree; t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(str(img_path)); t.image.pack()
    nt.links.new(t.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"]); return m


M = {"HL_Runner": material("HL_Runner", (0.23, 0.01, 0.05), 0.95), "HL_White": material("HL_White", (0.85, 0.85, 0.83), 0.5),
     "HL_Brass": material("HL_Brass", (0.75, 0.56, 0.25), 0.3), "HL_Shade": material("HL_Shade", (0.93, 0.90, 0.84), 0.4),
     "HL_Bulb": material("HL_Bulb", (1.0, 0.92, 0.8), 0.3), "HL_Wood": material("HL_Wood", (0.10, 0.035, 0.022), 0.45),
     "HL_Black": material("HL_Black", (0.03, 0.015, 0.015), 0.25), "HL_Soil": material("HL_Soil", (0.06, 0.04, 0.03), 0.95),
     "HL_Gilt": material("HL_Gilt", (0.72, 0.55, 0.25), 0.35), "HL_Mat": material("HL_Mat", (0.82, 0.78, 0.68), 0.9),
     "HL_Candle": material("HL_Candle", (0.55, 0.03, 0.04), 0.5), "HL_Art": tex_material("HL_Art", ROOT / "spec/dressing/hall_art.png", 0.6)}
BEVEL = {"HL_Wood": 0.003, "HL_Brass": 0.0015, "HL_White": 0.002, "HL_Black": 0.002, "HL_Gilt": 0.0015, "HL_Runner": 0.004, "HL_Mat": 0.0005}
coll = bpy.context.scene.collection
root = bpy.data.objects.new("HallDressing_HiFi", None); coll.objects.link(root)
root["lod_reason"] = "single LOD: small hall pieces seen within a few metres; the hall is short (~8 m) so a far LOD is never shown"
stats = {}
import hifi_pipeline as hp   # noqa: E402  (weld, smooth-by-angle, weighted normals, modifier apply)
for p in parts.values():
    if not p.f:
        continue
    ob = hp.to_object(p, M[p.mat], coll, hard_deg=30.0, weld=1e-5); ob.parent = root
    if p.mat in BEVEL:
        bv = ob.modifiers.new("Bevel", "BEVEL"); bv.width = BEVEL[p.mat]; bv.segments = 3; bv.limit_method = "ANGLE"; bv.angle_limit = math.radians(30)
        wn = ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL"); wn.keep_sharp = True; wn.mode = "FACE_AREA"
        hp.apply_modifiers(ob)
    stats[p.name] = len(ob.data.polygons)
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True, export_extras=True)
print("wrote", OUT, stats)
