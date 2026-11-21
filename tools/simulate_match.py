"""Play a 10-seat Tromsø Town Rush match with the real engine and export the preview.

    python3 tools/simulate_match.py ENGINE_DIR RUSH_AI_DIR OUT_DIR [seed]

ENGINE_DIR: the isolated multi-town engine prepared by tools/prepare_tromso.py.
Seats: three rush-ai instances (in-process, same interface as the CLI) and seven ReferenceBots,
one per grocery shop on the Tromsø map.

The shop floor is laid out by department (dairy fridges at the back, produce bins, a bakery
rack, pantry shelves) instead of the engine's round-robin deal. That is a presentation and
replay change only: the engine itself is untouched, the layout is swapped in before
create_match, and the same layout is written to shop.json so the shop window draws exactly
what the robots pick from.

Outputs:
  game.json   the public feed (engine.feed.from_replay, exactly what /api/games serves) + looks
  shop.json   the shop floor layout (with each cell's department and fixture), rules, and every
              order's items/address/timeline
  shop.bin    per tick, per seat: 20 robots x [x, y, action, item1, item2, item3] and
              5 trucks x [items loaded, items needed] for the orders queued on that truck
"""
import json
import os
import sys

ENGINE, RUSH, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SEED = int(sys.argv[4]) if len(sys.argv) > 4 else 7
sys.path.insert(0, ENGINE)
sys.path.insert(1, RUSH)

from engine.bots import ReferenceBot                     # noqa: E402
from engine.feed import from_replay                        # noqa: E402
from engine.replay import Recorder                         # noqa: E402
from engine.shop import make_shop as engine_make_shop      # noqa: E402
from engine import simulation                              # noqa: E402
from engine.simulation import create_match, match_start, observe, step   # noqa: E402
import ai as rush                                          # noqa: E402  (rush-ai/ai.py)

TOWN = 'tromso'
MATCH_ID = 'TROMSO-10-AI'

# ---- a realistic shop: groceries where they belong -----------------------------------------
# The engine's make_shop deals products round-robin across the shelf cells. This table keeps
# the exact same 23 x 12 floor plan (columns x = 3, 7, 11, 15, 19; blocks y = 3-5 and y = 7-8)
# but gives every cell a product that belongs to its department. Dairy is at the back, away
# from the entrance (21, 10); produce bins and the bakery rack sit nearest the entrance.
LAYOUT = {
    (3, 3): ('milk', 'fridge', 'Dairy'), (3, 4): ('milk', 'fridge', 'Dairy'), (3, 5): ('yogurt', 'fridge', 'Dairy'),
    (3, 7): ('cream', 'fridge', 'Dairy'), (3, 8): ('butter', 'fridge', 'Dairy'),
    (7, 3): ('cheese', 'fridge', 'Cheese & eggs'), (7, 4): ('eggs', 'fridge', 'Cheese & eggs'), (7, 5): ('juice', 'fridge', 'Cheese & eggs'),
    (7, 7): ('cereal', 'shelf', 'Breakfast'), (7, 8): ('oats', 'shelf', 'Breakfast'),
    (11, 3): ('pasta', 'shelf', 'Pantry'), (11, 4): ('rice', 'shelf', 'Pantry'), (11, 5): ('pasta', 'shelf', 'Pantry'),
    (11, 7): ('flour', 'shelf', 'Baking'), (11, 8): ('sugar', 'shelf', 'Baking'),
    (15, 3): ('lettuce', 'bin', 'Vegetables'), (15, 4): ('tomatoes', 'bin', 'Vegetables'), (15, 5): ('peppers', 'bin', 'Vegetables'),
    (15, 7): ('bread', 'rack', 'Bakery'), (15, 8): ('bread', 'rack', 'Bakery'),
    (19, 3): ('apples', 'bin', 'Fruit'), (19, 4): ('bananas', 'bin', 'Fruit'), (19, 5): ('bananas', 'bin', 'Fruit'),
    (19, 7): ('carrots', 'bin', 'Vegetables'), (19, 8): ('onions', 'bin', 'Vegetables'),
}
# One sign per block of shelving, hung over the aisle end of its column.
DEPARTMENTS = [
    {'name': 'Dairy', 'x': 3, 'y0': 3, 'y1': 8, 'fixture': 'fridge'},
    {'name': 'Cheese & eggs', 'x': 7, 'y0': 3, 'y1': 5, 'fixture': 'fridge'},
    {'name': 'Breakfast', 'x': 7, 'y0': 7, 'y1': 8, 'fixture': 'shelf'},
    {'name': 'Pantry', 'x': 11, 'y0': 3, 'y1': 5, 'fixture': 'shelf'},
    {'name': 'Baking', 'x': 11, 'y0': 7, 'y1': 8, 'fixture': 'shelf'},
    {'name': 'Vegetables', 'x': 15, 'y0': 3, 'y1': 5, 'fixture': 'bin'},
    {'name': 'Bakery', 'x': 15, 'y0': 7, 'y1': 8, 'fixture': 'rack'},
    {'name': 'Fruit', 'x': 19, 'y0': 3, 'y1': 5, 'fixture': 'bin'},
    {'name': 'Vegetables', 'x': 19, 'y0': 7, 'y1': 8, 'fixture': 'bin'},
]


def realistic_shop(rules):
    shop = engine_make_shop(rules)
    products = rules['products']
    order = []
    for item in shop['items']:
        cell = tuple(item['position'])
        product, fixture, dept = LAYOUT.get(cell, (None, None, None))
        if product not in products:
            product = None
        order.append((item, cell, product, fixture, dept))
    counts = {}
    for _, _, product, _, _ in order:
        if product:
            counts[product] = counts.get(product, 0) + 1
    # If a difficulty uses fewer products, fill the spare cells with the least-used ones.
    spare = [p for p in products if p not in counts]
    for i, (item, cell, product, fixture, dept) in enumerate(order):
        if product:
            continue
        product = spare.pop(0) if spare else min(products, key=lambda p: counts.get(p, 0))
        counts[product] = counts.get(product, 0) + 1
        dept, fixture = {
            'fridge': ('Dairy', 'fridge'), 'rack': ('Bakery', 'rack'), 'bin': ('Vegetables', 'bin'),
        }.get(LAYOUT.get(cell, (None, None, None))[1], ('Pantry', 'shelf'))
        order[i] = (item, cell, product, fixture, dept)
    shop['items'] = [{'id': f'item_{i}', 'type': product, 'position': list(cell),
                      'fixture': fixture, 'department': dept}
                     for i, (item, cell, product, fixture, dept) in enumerate(order)]
    shop['departments'] = DEPARTMENTS
    return shop


simulation.make_shop = realistic_shop

LOOKS = {
    'Kale Storm': {'shape': 'box', 'color': 'plum', 'eyes': 'visor', 'carriage': 'canvas', 'head': 'high', 'visor': 'tint', 'decal': 'dots'},
    'Oat Runner': {'shape': 'bean', 'color': 'red', 'eyes': 'dots', 'carriage': 'box', 'head': 'flat', 'visor': 'none', 'decal': 'stripe'},
    'Rush AI': {'shape': 'round', 'color': 'lemon', 'eyes': 'sleepy', 'carriage': 'cooler', 'head': 'nose', 'visor': 'tint', 'decal': 'band'},
    'Cheddar Dash': {'shape': 'bean', 'color': 'oat', 'eyes': 'happy', 'carriage': 'box', 'head': 'nose', 'visor': 'shade', 'decal': 'stripe'},
    'Plum Pusher': {'shape': 'dome', 'color': 'ink', 'eyes': 'wink', 'carriage': 'flatbed', 'head': 'slant', 'visor': 'lights', 'decal': 'plain'},
}
# ids sort into seat (and shop) order
NAMES = ['Kale Storm', 'Oat Runner', 'Rush AI', 'Cheddar Dash', 'Plum Pusher',
         'Milk Rocket', 'Pasta Pilot', 'Yogurt Yeti', 'Turbo Turnip', 'Rye Rider']
COLOURS = ['plum', 'red', 'lemon', 'oat', 'ink', 'milk', 'leaf', 'carrot', 'teal', 'rose']
for i, name in enumerate(NAMES):
    LOOKS[name] = {**list(LOOKS.values())[i % 5], 'color': COLOURS[i]}
SEATS = [(f'p{i + 1:02}', name, 'rush' if i in (2, 5, 8) else ReferenceBot)
         for i, name in enumerate(NAMES)]
ACTIONS = {'wait': 0, 'move_up': 1, 'move_down': 1, 'move_left': 1, 'move_right': 1, 'pick_up': 2, 'load': 3, 'drop_off': 3}

state = create_match(seed=SEED, difficulty='medium', players=[{'id': i, 'name': n} for i, n, _ in SEATS],
                     match_id=MATCH_ID, town=TOWN)
bots = {}
for pid, _, kind in SEATS:
    start = match_start(state, pid)
    bots[pid] = rush.make_bot(start) if kind == 'rush' else kind(start)
products = state['rules']['products']
order_seat = {pid: i for i, (pid, _, _) in enumerate(SEATS)}
frames = bytearray()
history = {}          # order id -> [[tick, status, seat]]
truck_loads = [[[] for _ in range(5)] for _ in SEATS]   # seat -> truck -> [[tick, item indexes, loaded "0101"]] on change


def load_of(truck):
    """The items queued on a docked truck, in order, and which of them robots have loaded."""
    items, done = [], ''
    for oid in truck['queue']:
        order = state['orders'].get(oid)
        if not order:
            continue
        left = list(order['items_delivered'])
        for item in order['items_required']:
            items.append(products.index(item))
            done += '1' if item in left else '0'
            if item in left:
                left.remove(item)
    return items, done


def capture():
    for pid, _, _ in SEATS:
        player = state['players'][pid]
        for bot in player['bots']:
            inv = [products.index(t) + 1 for t in bot['inventory']][:3]
            frames.extend([bot['position'][0], bot['position'][1], ACTIONS.get(bot['last_action'], 0), *(inv + [0] * (3 - len(inv)))])
        for t, truck in enumerate(player['trucks']):
            items, done = load_of(truck)
            log = truck_loads[order_seat[pid]][t]
            if not log or log[-1][1] != items or log[-1][2] != done:
                log.append([state['tick'], items, done])
            queued = [state['orders'][o] for o in truck['queue'] if o in state['orders']]
            loaded = sum(len(o['items_delivered']) for o in queued)
            needed = sum(len(o['items_required']) for o in queued)
            frames.extend([min(255, loaded), min(255, needed)])
    for oid, o in state['orders'].items():
        now = [state['tick'], o['status'], order_seat.get(o['by'], -1)]
        h = history.setdefault(oid, [])
        if not h or h[-1][1:] != now[1:]:
            h.append(now)


recorder = Recorder(state)
capture()
while not state['finished']:
    actions = {}
    for pid, bot in bots.items():
        try:
            actions[pid] = bot.actions(observe(state, pid))
        except Exception as error:      # a bot bug must not stop the recording
            print(f"tick {state['tick']} {pid}: {error!r}", file=sys.stderr)
            actions[pid] = []
    state = step(state, actions)
    recorder.append(actions, state)
    capture()
    if state['tick'] % 100 == 0:
        print('tick', state['tick'], {p['name']: p['score'] for p in state['players'].values()}, flush=True)

feed = from_replay(recorder.data).since(0)
for player in feed['meta']['players']:
    player['look'] = {**LOOKS[player['name']], 'name': 'Grocery Bot'}
feed['meta']['you'] = next(i for i, (_, name, _) in enumerate(SEATS) if name == 'Rush AI')   # whose shop opens as "Your shop"
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, 'game.json'), 'w') as f:
    json.dump(feed, f, separators=(',', ':'))

rules = state['rules']
orders = {}
for oid, o in state['orders'].items():
    orders[oid] = {
        'items': o['items_required'], 'address': o['address'].get('address') or o['address'].get('id'),
        'placed': o['released_tick'], 'expires': o['expires_tick'], 'deadline': o.get('deadline_tick'),
        'firstLoad': o.get('first_load_tick'), 'ready': o.get('ready_at_tick'),
        'deliveredAt': round(o['delivered_at'] / rules['tick_seconds'], 2) if o.get('delivered_at') is not None else None,
        'satisfaction': o.get('satisfaction'), 'points': o.get('points'), 'reward': o['reward'], 'rushBonus': o.get('rush_bonus'),
        'lateSeconds': o.get('late_seconds'), 'history': history.get(oid, []),
    }
shop = state['shop']
with open(os.path.join(OUT, 'shop.json'), 'w') as f:
    json.dump({'seed': SEED, 'grid': shop['grid'],
               'items': [[i['position'][0], i['position'][1], products.index(i['type']), i['fixture'], i['department']] for i in shop['items']],
               'departments': shop['departments'],
               'bays': [b['bay'] for b in shop['bays']], 'loadCells': [b['load_cells'] for b in shop['bays']], 'spawn': shop['spawn'],
               'products': products, 'botsPerPlayer': rules['bots_per_player'], 'trucksPerPlayer': rules['trucks_per_player'],
               'botCapacity': rules['bot_capacity'], 'tickSeconds': rules['tick_seconds'], 'lateStepTicks': rules['late_step_ticks'],
               'lateStepPercent': rules['late_step_percent'], 'seats': len(SEATS), 'frameBytes': rules['bots_per_player'] * 6 + rules['trucks_per_player'] * 2,
               'ticks': state['tick'] + 1, 'truckLoads': truck_loads, 'orders': orders}, f, separators=(',', ':'))
with open(os.path.join(OUT, 'shop.bin'), 'wb') as f:
    f.write(bytes(frames))
print('final', {p['name']: (p['score'], p['delivered']) for p in state['players'].values()}, 'bin', len(frames))
