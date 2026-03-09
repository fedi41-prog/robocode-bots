import queue


def compute_loop(compute_queue: queue.Queue[dict], result_queue: queue.Queue[dict]):
    print("compute loop starting...")
    while True:
        state = compute_queue.get()
        print(state)

        arena_width = state["arena_width"]
        arena_height = state["arena_height"]

        dm = calculate_danger_map(arena_width, arena_height)

        result = {
            "danger_map": dm
        }
        print("danger map updated")

        result_queue.put(result)


def calculate_danger_map(enemies, arena_width, arena_height, size: int = 10):
    w, h = arena_width // size, arena_height // size

    danger_map = [0] * (w * h)

    for x in range(0, w):
        for y in range(0, h):
            i = pos_to_id(x, y, w)
            danger_map[i] = calculate_danger_factor(enemies, x * size, y * size)

    return danger_map


def calculate_danger_factor(enemies, x: float, y: float):
    res = 0

    for enemy, _ in enemies.values():
        dist = math.dist((enemy.x, enemy.y), (x, y))
        d = (10000 - dist) ** 2
        res += d

    return res / 100000000