#!/bin/bash
# On the GPU box: box-town.sh TOWN PORT  -- expects /w/TOWN/site.tgz (the repo working tree, no .git)
# Extracts to /w/TOWN/site, bakes trees (BAKE=1), serves it on PORT, runs /w/city.mjs into /w/TOWN/out.
set -e
T=$1; P=$2; cd /w/$T
rm -rf site && mkdir site && tar xzf site.tgz -C site
cd site
if [ "${BAKE:-1}" = 1 ]; then PLAYWRIGHT_MODULE=/w/node_modules/playwright node tools/bake_trees.cjs; fi
[ -f /w/$T/server.pid ] && kill "$(cat /w/$T/server.pid)" 2>/dev/null || true
setsid nohup python3 -m http.server $P </dev/null >/dev/null 2>&1 & echo $! > /w/$T/server.pid
sleep 1
rm -rf /w/$T/out && mkdir -p /w/$T/out
cd /w && timeout 600 node city.mjs http://127.0.0.1:$P/ /w/$T/out 2>&1 | tail -30
