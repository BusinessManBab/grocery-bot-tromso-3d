"""Build the isolated Tromsø engine used to record the preview match.

    python3 tools/prepare_tromso.py /path/to/tromso/prototypes/town-rush \
        /path/to/feed/prototypes/town-rush

The town branch (town/tromso) has the Tromsø map and town folder but was cut before the
public feed existed, so feed.py comes from the branch that matches the live site. Nothing in
the source checkouts is modified: everything is copied into .cache/town-rush.
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source, feed_source = map(Path, sys.argv[1:3])
sandbox = ROOT / ".cache" / "town-rush"
sandbox.mkdir(parents=True, exist_ok=True)
for name in ("engine", "tools", "examples"):
    shutil.copytree(source / name, sandbox / name, dirs_exist_ok=True)
for name in ("data.js", "road-rules.js", "package.json"):
    shutil.copy2(source / name, sandbox / name)
shutil.copytree(source / "public/data/towns/tromso", sandbox / "public/data/towns/tromso", dirs_exist_ok=True)
shutil.copy2(feed_source / "engine" / "feed.py", sandbox / "engine" / "feed.py")

# The 12-seat allowance belongs only to this offline preview (the preview itself plays 10
# seats, one per Tromsø shop, so every player gets a distinct grocery store).
engine = sandbox / "engine/simulation.py"
engine.write_text(engine.read_text().replace("len(players) <= 10", "len(players) <= 12")
                  .replace("1–10 distinct", "1–12 distinct"))

# The map has ten shops: one per seat, so nobody shares a store.
map_data = json.loads((sandbox / "public/data/towns/tromso/map.json").read_text())
print(f"Prepared isolated Tromsø engine at {sandbox}; {len(map_data['shops'])} grocery shops.")
