"""Check that the Tromsø map, terrain, public feed and shop recording agree."""
import json
import struct
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
load = lambda name: json.loads((DATA / name).read_text())
town, graph, game, shop, relief, buildings = map(load, (
    "game-map.json", "map.json", "game.json", "shop.json", "terrain.json", "buildings.json"))
assert town["town"] == "tromso"
assert graph["id"] == "tromso-bot-v2"
assert len(graph["shops"]) == len(game["meta"]["players"]) == shop["seats"] == 10
assert len({s["node"] for s in graph["shops"]}) == 10
assert len({p["look"]["color"] for p in game["meta"]["players"]}) == 10
assert len(graph["addresses"]) == len(town["homes"]) == len(buildings["homes"]) == 88
point = lambda xy: tuple(round(v * 1e5) for v in xy)
assert {point(a["coordinates"]) for a in graph["addresses"]} == {tuple(p) for p in town["homes"]}
assert {tuple(h["p"]) for h in buildings["homes"]} == {tuple(p) for p in town["homes"]}
assert [point(s["coordinates"]) for s in graph["shops"]] == [tuple(p["shop"]) for p in game["meta"]["players"]]
assert game["finished"] and len(game["frames"]) == game["meta"]["ticks"] + 1 == shop["ticks"]
assert (DATA / "shop.bin").stat().st_size == shop["seats"] * shop["ticks"] * shop["frameBytes"]
assert (DATA / "terrain.bin").stat().st_size == relief["rows"] * relief["cols"] * 2
x0, y0, x1, y1 = town["bounds"]
for p in [*town["homes"], *(p["shop"] for p in game["meta"]["players"])]:
    assert x0 <= p[0] <= x1 and y0 <= p[1] <= y1, p
delivered = [0] * 10
for order in shop["orders"].values():
    if order["deliveredAt"] is not None:
        delivered[order["history"][-1][2]] += 1
assert all(n > 0 for n in delivered), delivered
assert all(len(frame["p"]) == 10 and all(len(p[4]) == 15 for p in frame["p"]) for frame in game["frames"])
print(f"PASS: 10 active AIs, 50 trucks, 88 matching homes, {shop['ticks']} synchronized frames.")
print("Delivered per AI:", delivered)
print("Terrain:", relief)

trees = (DATA / "trees.bin").read_bytes()
size = struct.unpack_from("<I", trees)[0]
header = json.loads(trees[4:4 + size])
offset = (4 + size + 3) // 4 * 4
forest = list(struct.iter_unpack("<hh", trees[offset:offset + header["forest"] * 4]))
assert header["forest"] <= 22000, "Forest must stay within the rendering budget"
assert sum(z / 4 > 2200 for x, z in forest) > 100, "Southern corner lost its vegetation"
print(f"PASS: {len(forest)} forest trees cover the full map, including the southern edge.")
