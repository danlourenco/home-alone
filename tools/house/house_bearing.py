"""house_bearing: the compass bearing the house's front faces, from OpenStreetMap (user, Oct 16: "doesn't the house face south ...
verify"). Saved data: art/home_alone/references/site/osm-671-lincoln.json (Overpass, Oct 16 2026: building way 218159249 "The Home
Alone House", 671 Lincoln Ave, and the ways within 60 m). Fetch again with:
  curl -s --data-urlencode 'data=[out:json];(way(around:15,42.1097985,-87.7336193)["building"];way(around:60,42.1097985,-87.7336193)["highway"];);out geom;' https://overpass.kumi.systems/api/interpreter

The front is the building side facing Lincoln Avenue: its outward normal is perpendicular to the street, toward it. Checks: the
building's long sides are parallel to the street (within 2 deg), and three Wikimedia Commons photos of the front (2015-05-11
06:38-06:41, positions from their EXIF; their compass headings are unreliable) were all taken on the street side.

  python3 tools/house/house_bearing.py      -> front faces ~227 deg (SW)
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = json.loads((ROOT / "art/home_alone/references/site/osm-671-lincoln.json").read_text())
LAT0 = 42.1097985
K = math.cos(math.radians(LAT0))
PHOTOS = [(42.109558, -87.733847), (42.109764, -87.734117), (42.109597, -87.733789)]   # Commons, camera positions


def xy(lat, lon):
    return ((lon + 87.7336193) * 111320 * K, (lat - LAT0) * 110540)   # metres east, north of the house's OSM node


def bearing(a, b):
    return math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360


way = {e["id"]: e for e in D["elements"]}
house = [xy(p["lat"], p["lon"]) for p in way[218159249]["geometry"]]
street = [xy(p["lat"], p["lon"]) for p in way[248616140]["geometry"]]   # Lincoln Avenue
# the street's bearing: its longest straight segment past the house
s = max(zip(street, street[1:]), key=lambda q: math.dist(*q))
sb = bearing(*s) % 180
# the house's long sides
edges = [(bearing(a, b) % 180, math.dist(a, b)) for a, b in zip(house, house[1:])]
long_axis = max(edges, key=lambda e: e[1])[0]
# the front normal: perpendicular to the street, from the house's centroid toward the street
cx, cy = sum(p[0] for p in house) / len(house), sum(p[1] for p in house) / len(house)
(ax, ay), (bx, by) = s
t = ((cx - ax) * (bx - ax) + (cy - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2)
foot = (ax + t * (bx - ax), ay + t * (by - ay))
front = bearing((cx, cy), foot)
print(f"Lincoln Ave bearing {sb:.1f} deg; house long axis {long_axis:.1f} deg; street {math.dist((cx, cy), foot):.1f} m from the centroid")
print(f"front faces {front:.1f} deg")
for lat, lon in PHOTOS:
    p = xy(lat, lon)
    print(f"  photo at {bearing((cx, cy), p):.0f} deg from the house, {math.dist((cx, cy), p):.0f} m")
assert abs((long_axis - sb + 90) % 180 - 90) < 2, "the house's long sides should run with the street"
assert all(abs((bearing((cx, cy), xy(*q)) - front + 180) % 360 - 180) < 60 for q in PHOTOS), "the front photos were taken on the street side"
