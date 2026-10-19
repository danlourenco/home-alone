"""OSM -> spec frame for the neighbourhood (same registration as changes/2026-10-19-front-drive.json): door node (-7.8,-7.7) -> spec (10.37, 9.716),
facade direction from the footprint's two front corners (-12.3,-3.2),(-6.2,-9.7); spec +x = out of the front (toward Lincoln)."""
import math
LAT0, LON0 = 42.1097985, -87.7336193
K = math.cos(math.radians(LAT0))
def osm(lat, lon): return ((lon - LON0) * 111320 * K, (lat - LAT0) * 110540)
_a, _b = (-12.3, -3.2), (-6.2, -9.7)
_d = math.hypot(_b[0]-_a[0], _b[1]-_a[1]); _t = ((_b[0]-_a[0])/_d, (_b[1]-_a[1])/_d)   # along facade
_n = (-_t[1], -_t[0]) if False else (_t[1]*-1, _t[0])                                   # candidate normal
if _n[0] > 0: _n = (-_n[0], -_n[1])          # outward = toward SW (negative east)
SZ = 1.0                                     # spec z = 9.716 + SZ * along-facade (sign set by check below)
def spec(lat, lon, sz=None):
    x, y = osm(lat, lon); dx, dy = x + 7.8, y + 7.7
    return (10.37 + dx*_n[0] + dy*_n[1], 9.716 + (SZ if sz is None else sz) * (dx*_t[0] + dy*_t[1]))
