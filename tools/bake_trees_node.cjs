// CPU-only bake fallback: CANVAS_MODULE=/path/to/@napi-rs/canvas node tools/bake_trees_node.cjs
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { createCanvas, Path2D } = require(process.env.CANVAS_MODULE || '@napi-rs/canvas');
global.Path2D = Path2D;
global.document = { createElement: () => createCanvas(1, 1) };

(async () => {
  const root = path.resolve(__dirname, '..');
  const code = fs.readFileSync(path.join(root, 'src/forest.js'), 'utf8');
  const { plantForest, plantParks, packTrees } = await import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`);
  const read = file => JSON.parse(fs.readFileSync(path.join(root, 'data', file)));
  const town = read('game-map.json'), extra = read('buildings.json'), cover = read('landcover.json'), game = read('game.json');
  const origin = [(town.bounds[0] + town.bounds[2]) / 2, (town.bounds[1] + town.bounds[3]) / 2];
  const squash = Math.cos(origin[1] / 1e5 * Math.PI / 180);
  const wx = lon => (lon - origin[0]) * squash, wy = lat => -(lat - origin[1]);
  const shops = game.meta.players.map(p => [wx(p.shop[0]), wy(p.shop[1])]);
  const args = { town, buildings: extra.buildings, homes: extra.homes, cover, wx, wy, shops };
  const forest = plantForest(args), parks = plantParks(args);
  assert.equal(forest.length, 22000);
  assert.deepEqual(plantForest(args), forest, 'planting must be deterministic');
  // Regression: the old scan cap left the southernmost kilometre entirely bare.
  const southern = forest.filter(p => p[1] > 2200).length;
  assert.ok(southern > 100, 'southern landscape must receive trees');
  const source = crypto.createHash('sha256');
  for (const file of ['game-map.json', 'buildings.json', 'landcover.json', 'game.json']) source.update(fs.readFileSync(path.join(root, 'data', file)));
  fs.writeFileSync(path.join(root, 'data/trees.bin'), Buffer.from(packTrees({ forest, parks, source: source.digest('hex').slice(0, 16) })));
  console.log(JSON.stringify({ forest: forest.length, parks: parks.length, southern, minZ: Math.min(...forest.map(p => p[1])), maxZ: Math.max(...forest.map(p => p[1])) }));
})().catch(error => { console.error(error); process.exitCode = 1; });
