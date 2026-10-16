"""Shared mesh building for the hifi_* Blender scripts (run inside Blender): parts written in spec coordinates (x, y up, z),
mapped to Blender (-x, z, y), so glTF + glTFast land them at Unity (x, y, -z). The map is a rotation (determinant +1), so
faces keep their winding: counter-clockwise from outside in spec space stays outward. (Until Oct 16 the faces were reversed
here on the belief that the map was a reflection; every closed part rendered inside-out and its far faces z-fought.)
Check: tools/house/glb_orientation.py."""
import math

import bpy

# ---------------------------------------------------------------- mesh building in spec coordinates
class Part:
    def __init__(self, name, mat):
        self.name, self.mat, self.v, self.f, self.uv = name, mat, [], [], {}

    def quad(self, a, b, c, d):            # counter-clockwise seen from outside (spec space)
        i = len(self.v); self.v += [a, b, c, d]; self.f.append((i, i + 1, i + 2, i + 3))

    def poly(self, pts):
        i = len(self.v); self.v += list(pts); self.f.append(tuple(range(i, i + len(pts))))

    def face(self, pts, toward, uvs=None):
        """A flat face oriented to look along 'toward' (spec space): no hand winding. Optional per-corner uvs follow the corners."""
        n = [0.0, 0.0, 0.0]
        for (ax, ay, az), (bx, by, bz) in zip(pts, pts[1:] + pts[:1]):   # Newell normal
            n[0] += (ay - by) * (az + bz); n[1] += (az - bz) * (ax + bx); n[2] += (ax - bx) * (ay + by)
        keep = sum(a * b for a, b in zip(n, toward)) >= 0
        self.poly(pts if keep else list(reversed(pts)))
        if uvs:
            self.uv[len(self.f) - 1] = list(uvs) if keep else list(reversed(uvs))

    def face_uv(self, pts, uvs, toward):
        self.face(pts, toward, uvs)

    def box(self, x0, x1, y0, y1, z0, z1):
        P = lambda x, y, z: (x, y, z)
        self.quad(P(x0, y1, z0), P(x0, y1, z1), P(x1, y1, z1), P(x1, y1, z0))   # top
        self.quad(P(x0, y0, z0), P(x1, y0, z0), P(x1, y0, z1), P(x0, y0, z1))   # bottom
        self.quad(P(x0, y0, z0), P(x0, y0, z1), P(x0, y1, z1), P(x0, y1, z0))   # -x
        self.quad(P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1))   # +x
        self.quad(P(x0, y0, z0), P(x0, y1, z0), P(x1, y1, z0), P(x1, y0, z0))   # -z
        self.quad(P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1))   # +z

    def lathe(self, cx, cz, y0, prof, n=20):
        """Turned part: prof = [(height above y0, radius)], bottom to top, about a vertical axis at (cx, cz)."""
        rings = []
        for h, r in prof:
            rings.append([(cx + r * math.cos(2 * math.pi * k / n), y0 + h, cz + r * math.sin(2 * math.pi * k / n)) for k in range(n)])
        for a, b in zip(rings, rings[1:]):
            for k in range(n):
                k2 = (k + 1) % n
                self.quad(a[k], b[k], b[k2], a[k2])
        self.face(rings[0], (0, -1, 0)); self.face(rings[-1], (0, 1, 0))

    def sweep(self, path, prof):
        """A profile [(across, up)] swept along a 3D polyline (handrail); 'across' is horizontal, perpendicular to the path, and 'up' is
        perpendicular to both and always points upward (for a path in a vertical plane across x: away from the arc's centre)."""
        rings = []
        for i, p in enumerate(path):
            a, b = path[max(i - 1, 0)], path[min(i + 1, len(path) - 1)]
            t = [b[0] - a[0], b[1] - a[1], b[2] - a[2]]; L = math.sqrt(sum(c * c for c in t)); t = [c / L for c in t]
            side = [-t[2], 0.0, t[0]]; Ls = math.hypot(side[0], side[2])
            side = [side[0] / Ls, 0, side[2] / Ls] if Ls > 1e-9 else [-1.0, 0.0, 0.0]   # a vertical path: any horizontal side
            up = [t[1] * side[2] - t[2] * side[1], t[2] * side[0] - t[0] * side[2], t[0] * side[1] - t[1] * side[0]]
            if up[1] < 0 or (abs(up[1]) < 1e-9 and up[0] + up[2] < 0):   # 'up' always points up (it flipped on paths running toward -x:
                side, up = [-c for c in side], [-c for c in up]          # a skirt board hung below its line; user note 09:48); both turn, so faces keep their winding
            rings.append([tuple(p[j] + u * side[j] + w * up[j] for j in range(3)) for u, w in prof])
        n = len(prof)
        for a, b in zip(rings, rings[1:]):
            for k in range(n):
                k2 = (k + 1) % n
                self.quad(a[k], a[k2], b[k2], b[k])
        back = [path[0][j] - path[1][j] for j in range(3)]; fwd = [path[-1][j] - path[-2][j] for j in range(3)]
        self.face(rings[0], back); self.face(rings[-1], fwd)

    def build(self, coll, mats):
        to_b = lambda p: (-p[0], p[2], p[1])                    # spec -> Blender (see module doc)
        me = bpy.data.meshes.new(self.name)
        me.from_pydata([to_b(p) for p in self.v], [], self.f)
        if self.uv:   # texture coordinates where given (a print's paper), zero elsewhere
            layer = me.uv_layers.new(name="UVMap")
            for fi, uvs in self.uv.items():
                for li, loop in enumerate(me.polygons[fi].loop_indices):
                    layer.data[loop].uv = uvs[li]
        me.update(); me.validate()
        ob = bpy.data.objects.new(self.name, me); coll.objects.link(ob)
        ob.data.materials.append(mats[self.mat])
        for poly in me.polygons:
            poly.use_smooth = False
        return ob


def material(name, rgb, rough, emit=None, strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]; bsdf.inputs["Base Color"].default_value = (*rgb, 1.0); bsdf.inputs["Roughness"].default_value = rough
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0); bsdf.inputs["Emission Strength"].default_value = strength
    return m
