# Grocery Bot 3D map preview: Tromsø

Tromsø, Norway, in 2D and 3D on the town's real terrain. Built from
[grocery-bot-3d-hills-preview](https://github.com/BusinessManBab/grocery-bot-3d-hills-preview) by swapping in
Tromsø's town data, following [OTHER-CITIES.md](OTHER-CITIES.md).

- Real terrain: the 3D map is draped over an elevation grid of Tromsø (`data/terrain.bin`, 649 × 763 samples every ~8 m, 0–668 m, relief ×1.0 because the fjord town is already steep). Roads, buildings, trees, shops, trucks (pitched on slopes) and trails follow the ground; the board edge shows the mountains in section, and the sea stays flat. The board covers a square-ish 5.7 × 6.8 km of Tromsøya, Tromsøysundet, the Tromsdalen shore and the Kvaløya coast.
- 10 AI players, one per grocery shop, 50 trucks and 88 real delivery addresses; all 88 homes matched a real OpenStreetMap building footprint.
- No trees on or next to water.
- Forest sampling covers the entire eligible landscape within a fixed 22,000-tree
  budget. It no longer stops at the southern corner when northern rows fill the
  budget. Roads, buildings, water and mapped open land retain their exclusions.
- Buildings have real-world detail without extra draw calls: windows, doors and pitched roofs in muted varied colours, built in workers from the baked `data/buildings.bin`. Delivery homes keep their own materials so orders still stand out.
- Shop window (bottom right): the v1 grocerybot.no store animation (Erik's `arena.js`, ported to `src/shop-iso.js`) showing the robots and trucks inside a shop as the match plays, switched by clicking any shop or a standings row; order card (left) when you click an order house, with its items grouped by department in the order a robot walks the shop. The replay is a simulated match with the user's rush-ai, recorded from the engine (`tools/simulate_match.py`).
- The shop is laid out like a real grocery store: dairy fridges at the back, cheese and eggs beside them, pantry and baking shelves in the middle, produce bins, a bakery rack and fruit nearest the entrance, each block under its own department sign. The layout is swapped into the recorded match before it is played, so robots really pick milk from the dairy fridges and bread from the rack.
- The trucks parked at the bays in the shop window are drawn with the same `truckArt(look)` from `src/looks.js` as the trucks driving that player's routes on the 2D and 3D map: same carriage, cab, visor, decal, colour and expression.
- Bridges: roads cross water on raised decks with railings and piers; trucks drive over them.
- The river flows: streaks drift downstream along each river (direction from a distance-to-outlet field over the water areas), faster where the river drops. The fjord is still.

## Landmarks

Tromsø's trademarks stand out in 3D (`src/landmarks.js`, data from `tools/landmarks.spec.json` via `tools/bake_landmarks.mjs`):

- **Ishavskatedralen** (Tromsdalen kirke, Jan Inge Hovig 1965): eleven aluminium-clad lamellas on each side, stepping down from the glass west front with its cross (facing the bridge and the town) to the triangular east wall with Victor Sparre's glass mosaic, glass in each step. Built on its real OpenStreetMap outline (a multipolygon the plain building data had left out, so the site used to be empty). Heights are the real 35 m divided by the map's 1.3 building lift, so the A-frame keeps its real proportions.
- **Tromsøbrua** (1960, concrete box-girder cantilever bridge, 1016 m, 58 spans, 38 m clearance): the bridge was too long for the generic bridge rule, so the road used to lie flat on the sound. Now the deck rises from each shore to a rounded crest over the shipping channel near the Tromsdalen side (where the bridge lights are mapped), with the box girder deepening over the 80 m main span, hanging walkways, railings and twin slender columns at each support. Roads and trucks drive on the same deck profile (`bridgeDeck()` in `src/landmarks.js`, used by `src/view3d.js`).
- **Polaria** (JAF arkitektkontor 1998): five white slabs like ice floes pushed up onto land, each tilted up towards the land and higher than the last, glass in the steps, the entrance side clad in larch. Each slab is the OSM outline cut into a strip.
- **Tromsø domkirke** (Grosch 1861, Norway's only Protestant wooden cathedral): ochre board-clad walls with pointed-arch windows, grey corner pilasters, dark roofs, and the west tower with its clock, belfry and tall copper-green spire.

The explore menu (bottom left) flies to each landmark, the centre and Fjellheisen. All landmarks together: 7 draw calls, about 6,800 triangles. Heights not published (Polaria's slabs, the cathedral tower) are estimated from photos.

## Loading and flicker

The 3D city uses the Oslo map's loading strategy (the shared engine from the Kongsberg map): buildings baked into `data/buildings.bin` and built in module workers nearest-first, trees baked into `data/trees.bin` (forest from `data/landcover.json`), delivery homes merged per material, a lighter tier on phones. All 11,017 buildings are on screen in about 3 s on a GTX 1070, at 60 fps.

Flicker came from surfaces in one plane: each wall two neighbours share is now kept on one side only, doors stand 25 cm off the wall, each building's roof sits a few centimetres apart from its neighbour's, and the near plane follows the camera's height.

Rebuild after changing data: `node tools/bake_landmarks.mjs`, `node tools/bake_buildings.mjs`, then `PLAYWRIGHT_MODULE=... node tools/bake_trees.cjs` (needs Chromium). The shop window, order card (by department) and the map's own trucks are this repo's own versions of `src/shop-iso.js` and `src/panels.js`; the relief (×1.0) is set in `src/world-build.js` and the camera tilt in `src/view3d.js`.

The data came from the `town/tromso` branch of `astar-as/grocery-bot` (10 shops, 88 delivery addresses,
real Tromsøbrua) and OpenStreetMap.

To make this for another town, follow [OTHER-CITIES.md](OTHER-CITIES.md) (data scripts in `tools/build_city.py`).
`tools/prepare_tromso.py` builds the isolated engine used to record the match.

Switch views with the 2D / 3D buttons (or V, or `?view=3d`).

Elevation: Mapzen Terrarium tiles (AWS Open Data). Map data © OpenStreetMap contributors (ODbL).
