"""Build an expanded Oslo sandbox without modifying the source game checkout.

python3 tools/prepare_oslo.py /path/to/oslo/prototypes/town-rush /path/to/feed/prototypes/town-rush
"""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
source, feed_source = map(Path, sys.argv[1:3])
sandbox = ROOT / ".cache" / "town-rush"
sandbox.mkdir(parents=True, exist_ok=True)
for name in ("engine", "tools", "examples"):
    shutil.copytree(source / name, sandbox / name, dirs_exist_ok=True)
for name in ("data.js", "road-rules.js", "package.json"):
    shutil.copy2(source / name, sandbox / name)
town_dir = sandbox / "public/data/towns/oslo"
shutil.copytree(source / "public/data/towns/oslo", town_dir, dirs_exist_ok=True)
for name in ("feed.py", "match_stats.py"):
    if (feed_source / "engine" / name).exists():
        shutil.copy2(feed_source / "engine" / name, sandbox / "engine" / name)

# The 12-seat allowance belongs only to this offline preview.
engine = sandbox / "engine/simulation.py"
engine.write_text(engine.read_text().replace("len(players) <= 10", "len(players) <= 12")
                  .replace("1–10 distinct", "1–12 distinct"))
builder = sandbox / "tools/build-bot-map-v2.py"
builder.write_text(builder.read_text().replace("SHOPS = 10", "SHOPS = 12"))
spec = importlib.util.spec_from_file_location("map_builder", builder)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
distance = module.metres

town = json.loads((town_dir / "town.json").read_text())
# Stay inside both the saved driving-road and water/green snapshots.
west, south, east, north = 10.7165, 59.9015, 10.7865, 59.9405
area = [[west, south], [east, south], [east, north], [west, north]]
town["build"].update(area=area, max_customers=160, map_id="oslo-expanded-preview-v1")
town["play_area"]["polygon"] = area
all_addresses = json.loads((town_dir / "addresses-all.json").read_text())["addresses"]
pool = [a for a in all_addresses if west < a["coordinates"][0] < east
        and south < a["coordinates"][1] < north]
shops = town["build"]["shops"]
for target in ([10.739, 59.912], [10.777, 59.922]):
    candidates = [a for a in pool if all(distance(a["coordinates"], s["coordinates"]) > 350 for s in shops)]
    a = min(candidates, key=lambda a: distance(a["coordinates"], target))
    shops.append({k: a[k] for k in ("address", "coordinates")})
selected = []
candidates = [a for a in pool if all(distance(a["coordinates"], s["coordinates"]) >= 160 for s in shops)]
while candidates and len(selected) < 160:
    a = max(candidates, key=lambda a: (min((distance(a["coordinates"], b["coordinates"]) for b in selected),
                                         default=distance(a["coordinates"], [10.751, 59.921])), a["id"]))
    selected.append({k: a[k] for k in ("id", "address", "coordinates")})
    candidates = [b for b in candidates if distance(a["coordinates"], b["coordinates"]) >= 85]
addresses = json.loads((town_dir / "addresses.json").read_text())
addresses["addresses"] = selected
(town_dir / "addresses.json").write_text(json.dumps(addresses))
(town_dir / "town.json").write_text(json.dumps(town))
for command in (
    ["node", "tools/freeze-bot-map.mjs", "--town", "oslo"],
    [sys.executable, "tools/build-bot-map-v2.py", "--town", "oslo"],
    [sys.executable, "tools/build-town-game-map.py", "--town", "oslo"],
):
    subprocess.run(command, cwd=sandbox, check=True)
for name in ("game-map.json", "map.json", "town.json"):
    shutil.copy2(town_dir / name, ROOT / "data" / name)
print(f"Prepared isolated engine at {sandbox}; {len(selected)} real delivery addresses.")
