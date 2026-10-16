"""Shared mesh building for the hifi_* Blender scripts (run inside Blender): parts written in spec coordinates (x, y up, z),
mapped to Blender (-x, z, y) with faces reversed (the map is a reflection), so glTF + glTFast land them at Unity (x, y, -z)."""
import math

import bpy

# ---------------------------------------------------------------- mesh building in spec coordinates
class Part:
    def __init__(self, name, mat):
        self.name, self.mat, self.v, self.f = name, mat, [], []

    def quad(self, a, b, c, d):            # counter-clockwise seen from outside (spec space)
        i = len(self.v); self.v += [a, b, c, d]; self.f.append((i, i + 1, i + 2, i + 3))

    def poly(self, pts):
        i = len(self.v); self.v += list(pts); self.f.append(tuple(range(i, i + len(pts))))

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
        self.poly(list(reversed(rings[0]))); self.poly(rings[-1])

    def sweep(self, path, prof):
        """A profile [(across, up)] swept along a 3D polyline (handrail); 'across' is horizontal, perpendicular to the path."""
        rings = []
        for i, p in enumerate(path):
            a, b = path[max(i - 1, 0)], path[min(i + 1, len(path) - 1)]
            t = [b[0] - a[0], b[1] - a[1], b[2] - a[2]]; L = math.sqrt(sum(c * c for c in t)); t = [c / L for c in t]
            side = [-t[2], 0.0, t[0]]; Ls = math.hypot(side[0], side[2]); side = [side[0] / Ls, 0, side[2] / Ls]
            up = [t[1] * side[2] - t[2] * side[1], t[2] * side[0] - t[0] * side[2], t[0] * side[1] - t[1] * side[0]]
            rings.append([tuple(p[j] + u * side[j] + w * up[j] for j in range(3)) for u, w in prof])
        n = len(prof)
        for a, b in zip(rings, rings[1:]):
            for k in range(n):
                k2 = (k + 1) % n
                self.quad(a[k], a[k2], b[k2], b[k])
        self.poly(list(reversed(rings[0]))); self.poly(rings[-1])

    def build(self, coll, mats):
        to_b = lambda p: (-p[0], p[2], p[1])                    # spec -> Blender (see module doc)
        me = bpy.data.meshes.new(self.name)
        me.from_pydata([to_b(p) for p in self.v], [], [tuple(reversed(f)) for f in self.f])
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
