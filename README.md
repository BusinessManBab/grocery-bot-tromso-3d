# Grocery Bot 3D map preview: Tromsø

Tromsø, Norway, in 2D and 3D on the town's real terrain. Built from
[grocery-bot-3d-hills-preview](https://github.com/BusinessManBab/grocery-bot-3d-hills-preview) by swapping in
Tromsø's town data, following [OTHER-CITIES.md](OTHER-CITIES.md).

- Real terrain: the 3D map is draped over an elevation grid of Tromsø (`data/terrain.bin`, 649 × 763 samples every ~8 m, 0–668 m, relief ×1.0 because the fjord town is already steep). Roads, buildings, trees, shops, trucks (pitched on slopes) and trails follow the ground; the board edge shows the mountains in section, and the sea stays flat. The board covers a square-ish 5.7 × 6.8 km of Tromsøya, Tromsøysundet, the Tromsdalen shore and the Kvaløya coast.
- 10 AI players, one per grocery shop, 50 trucks and 88 real delivery addresses; all 88 homes matched a real OpenStreetMap building footprint.
- No trees on or next to water.
- Buildings have real-world detail without extra draw calls: the whole context town is one merged mesh with a shared window facade texture (a bay per 3.4 m, a storey per 3.2 m), muted varied wall and roof colours as vertex colours, and pitched gable roofs on small rectangular houses. Delivery homes get the same roofs and windows but keep their own materials so orders still stand out. About 498k building vertices in all.
- Shop window (bottom right): the v1 grocerybot.no store animation (Erik's `arena.js`, ported to `src/shop-iso.js`) showing the robots and trucks inside a shop as the match plays, switched by clicking any shop or a standings row; order card (left) when you click an order house, with its items grouped by department in the order a robot walks the shop. The replay is a simulated match with the user's rush-ai, recorded from the engine (`tools/simulate_match.py`).
- The shop is laid out like a real grocery store: dairy fridges at the back, cheese and eggs beside them, pantry and baking shelves in the middle, produce bins, a bakery rack and fruit nearest the entrance, each block under its own department sign. The layout is swapped into the recorded match before it is played, so robots really pick milk from the dairy fridges and bread from the rack.
- The trucks parked at the bays in the shop window are drawn with the same `truckArt(look)` from `src/looks.js` as the trucks driving that player's routes on the 2D and 3D map: same carriage, cab, visor, decal, colour and expression.
- Bridges: roads cross water on raised decks with railings and piers; trucks drive over them.
- The river flows: streaks drift downstream along each river (direction from a distance-to-outlet field over the water areas), faster where the river drops. The fjord is still.

The data came from the `town/tromso` branch of `astar-as/grocery-bot` (10 shops, 88 delivery addresses,
real Tromsøbrua) and OpenStreetMap.

To make this for another town, follow [OTHER-CITIES.md](OTHER-CITIES.md) (data scripts in `tools/build_city.py`).
`tools/prepare_tromso.py` builds the isolated engine used to record the match.

Switch views with the 2D / 3D buttons (or V, or `?view=3d`).

Elevation: Mapzen Terrarium tiles (AWS Open Data). Map data © OpenStreetMap contributors (ODbL).
