"""Height budget: every vertical layer of the house, ground floor to eaves, with its ruler. The layers must close against the
real house's facade (tools/house/brick_courses.py). Ceilings are to the ceiling PLANE: crown and beams are listed as drops
below it, never read as the ceiling. Floors are the full stack (finish, subfloor, joists, plaster), not a thin slab.
usage: uv run --with numpy --with pillow python -I tools/house/height_budget.py
"""
IN = 0.0254
COURSE_IN = (2.5, 2.75)
# (layer, low m, high m, ruler / source); low == high means one built value
LAYERS = [
    ("ground ceiling plane", 2.42, 2.44, "Marina 1125/1175 s, door jambs (ground_ceiling.py); no crown in either room, read to the plane"),
    ("ground floor stack", 0.28, 0.36, "AUTHORED: 1920s oak + subfloor + 2x10-2x12 full-size joists + plaster, 11-14 in; measure at the gallery fascia"),
    ("upstairs ceiling plane", 2.38, 2.50, "Marina door walls Oct 13: parents 2.42 to the crown + 0.08 crown; hall 2.29 (attic leg) excluded"),
]
DROPS = [   # below a ceiling plane: never a ceiling height
    ("upstairs crown (parents, Kevin)", 0.08, "Marina frames, Oct 13 ceiling reads"),
    ("kitchen beams", None, "UNMEASURED: read beam bottom and plane separately"),
    ("gallery edge / landing soffit", None, "UNMEASURED: its depth = floor stack + beam; the headroom check must use it"),
]
# Facade, in brick courses above the ground floor (French door foot), brick_courses.py edges and 5.79 px/course
FACADE = {"upstairs window head": 68.6, "upstairs window sill": 47.5, "cornice soffit": 70.3}
MARINA_UP_WINDOW = {"head": 2.15, "sill": 0.81}   # buzz_windows.py (Marina's set; the upstairs was built in a gym)
BUILT_F2F = 2.873                                 # current model: 17 risers x 0.169 (13 + 4 stair)


def main():
    g, s, u = LAYERS
    f2f = (g[1] + s[1], g[2] + s[2])
    print("layers (ceilings to the plane):")
    for name, lo, hi, src in LAYERS:
        print(f"  {name:<24} {lo:.2f}-{hi:.2f} m  {src}")
    for name, d, src in DROPS:
        print(f"  drop: {name:<30} {'%.2f m' % d if d else '  ?   '}  {src}")
    print(f"floor-to-floor from layers: {f2f[0]:.2f}-{f2f[1]:.2f} m; built {BUILT_F2F:.3f} m "
          f"({'inside' if f2f[0] <= BUILT_F2F <= f2f[1] else 'OUTSIDE'}); 17 risers -> {f2f[0] / 17 * 100:.1f}-{f2f[1] / 17 * 100:.1f} cm rise")
    fac = {k: (v * COURSE_IN[0] * IN, v * COURSE_IN[1] * IN) for k, v in FACADE.items()}
    for k in ("head", "sill"):
        lo, hi = fac[f"upstairs window {k}"]
        print(f"facade: window {k} {lo:.2f}-{hi:.2f} m above the ground floor, Marina's {k} {MARINA_UP_WINDOW[k]:.2f} m above "
              f"hers -> floor-to-floor {lo - MARINA_UP_WINDOW[k]:.2f}-{hi - MARINA_UP_WINDOW[k]:.2f} m if her windows line up")
    lo, hi = fac["cornice soffit"]
    need = f2f[0] + u[1]
    print(f"facade: cornice soffit {lo:.2f}-{hi:.2f} m; ground floor to upstairs ceiling plane needs >= {need:.2f} m, so the "
          f"upstairs ceiling sits >= {need - hi:.2f} m above the soffit (plate behind the frieze)")
    return f2f, fac


if __name__ == "__main__":
    f2f, fac = main()
    assert f2f[0] < f2f[1]
