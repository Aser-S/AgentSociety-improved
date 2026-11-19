"""Build a small synthetic grid city map (.pb) for AgentSociety v1 using mosstool.

No OSM / network access needed. Usage: python build_grid_map.py OUT.pb [N] [SPACING_M]
"""
import json
import sys
import geojson
import pyproj
from geojson import Feature, FeatureCollection, LineString, MultiPoint, Polygon
from mosstool.map.builder import Builder
from mosstool.type import Map
from mosstool.util.format_converter import dict2pb

out = sys.argv[1] if len(sys.argv) > 1 else "grid_map.pb"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 4          # junctions per side
S = float(sys.argv[3]) if len(sys.argv) > 3 else 400.0    # metres between junctions
LON0, LAT0 = 116.39, 39.90
PROJ = f"+proj=tmerc +lat_0={LAT0} +lon_0={LON0}"
to_ll = pyproj.Proj(PROJ)

def ll(x, y):
    lon, lat = to_ll(x, y, inverse=True)
    return (lon, lat)

feats, in_ways, out_ways = [], {}, {}
jid = lambda i, j: 2_000_000 + i * N + j
wid = [1_000_000]

def add_way(a, b):
    w = wid[0]; wid[0] += 1
    (i1, j1), (i2, j2) = a, b
    feats.append(Feature(id=w, geometry=LineString([ll(i1 * S, j1 * S), ll(i2 * S, j2 * S)]),
                         properties={"id": w, "lanes": 2, "highway": "secondary",
                                     "max_speed": 40 / 3.6, "name": f"road_{w}"}))
    out_ways.setdefault(jid(*a), []).append(w)
    in_ways.setdefault(jid(*b), []).append(w)

for i in range(N):
    for j in range(N):
        for di, dj in ((1, 0), (0, 1)):
            if i + di < N and j + dj < N:
                add_way((i, j), (i + di, j + dj))
                add_way((i + di, j + dj), (i, j))
for i in range(N):
    for j in range(N):
        k = jid(i, j)
        feats.append(Feature(id=k, geometry=MultiPoint([ll(i * S, j * S)]),
                             properties={"id": k, "in_ways": in_ways.get(k, []),
                                         "out_ways": out_ways.get(k, [])}))

# Buildings (AOIs): four per block, set back from the roads
aois, aid, m, b = [], 3_000_000, 40.0, 0.0
for i in range(N - 1):
    for j in range(N - 1):
        x0, y0, h = i * S + m, j * S + m, (S - 3 * m) / 2
        for dx in (0, h + m):
            for dy in (0, h + m):
                x, y = x0 + dx, y0 + dy
                ring = [ll(x, y), ll(x + h, y), ll(x + h, y + h), ll(x, y + h), ll(x, y)]
                aois.append(Feature(id=aid, geometry=Polygon([ring]),
                                    properties={"id": aid, "osm_tags": [{"building": "yes"}], "type": ""}))
                aid += 1

plain = lambda fs: json.loads(geojson.dumps(FeatureCollection(fs)))
builder = Builder(net=FeatureCollection(feats), aois=aois, pois=[], proj_str=PROJ)
m_dict = builder.build("grid_city")
pb = dict2pb(m_dict, Map())
with open(out, "wb") as f:
    f.write(pb.SerializeToString())
print(f"wrote {out}: {len(pb.lanes)} lanes, {len(pb.roads)} roads, "
      f"{len(pb.junctions)} junctions, {len(pb.aois)} aois")
