import math
import numpy as np
from robocode_tank_royale.bot_api.events import ScannedBotEvent


def weighted_average(values, weights) -> float:
    if sum(weights) == 0 or len(values) < 0: return None
    return sum(w * g for w, g in zip(values, weights)) / sum(weights)

def angle_diff(a, b):
    d = (a - b + 180) % 360 - 180
    return abs(d)

def pos_to_id(x:int, y:int, w:int):
    return x + y * w

def id_to_pos(i:int, w:int):
    x = i % w
    y = i // w
    return x, y

#def calculate_danger_map(enemies, arena_width, arena_height, size: int = 10):
#    w, h = arena_width // size, arena_height // size
#
#    danger_map = [0] * (w * h)
#
#    for x in range(0, w):
#        for y in range(0, h):
#            i = pos_to_id(x, y, w)
#            danger_map[i] = calculate_danger_factor(enemies, arena_width, arena_height, x * size, y * size)
#
#    return normalize(danger_map)
#
#
#def calculate_danger_factor(enemies, arena_width, arena_height,  x: float, y: float):
#    res = 0
#
#    if len(enemies) == 0:
#        return 0
#
#    for enemy, _ in enemies.values():
#        dist = math.dist((enemy.x, enemy.y), (x, y))
#
#
#        r = 10 / (dist + 18)
#
#
#        res += r
#
#
#    wall_dist = min(min(x, arena_width-x), min(y, arena_height-y))
#
#    if wall_dist < 40:
#        return res + 0.2
#
#    return res
#
#import math



import math

def calculate_danger_vector(enemies, x, y, w, h):

    vx = 0
    vy = 0

    for enemy, _ in enemies.values():

        dx = x - enemy.x
        dy = y - enemy.y

        dist = math.hypot(dx, dy) + 0.0001

        strength = enemy.energy / dist**1.5
        if dist < 50:
            strength += 10

        vx += dx / dist * strength
        vy += dy / dist * strength

    # wall repulsion
    wall_strength = 5000

    vx += wall_strength / (x + 1) ** 2
    vx -= wall_strength / (w - x + 1) ** 2

    vy += wall_strength / (y + 1) ** 2
    vy -= wall_strength / (h - y + 1) ** 2

    return vx, vy


def project_enemy_movement(enemies : dict[int, tuple[ScannedBotEvent, dict]]):
    res = {}

    for idx, d in enemies.items():
        e, _ = d
        dx, dy = dir_to_vector(e.direction, e.speed)
        nx, ny = e.x + dx, e.y + dy
        res[idx] = (nx, ny)

    return res


def normalize(vec):
    vx, vy = vec

    l = math.hypot(vx, vy)

    if l == 0:
        return 0,0

    return vx/l, vy/l

# von ChatGPT
# ==========================================================
#def calculate_danger_map_optimized(enemies, arena_width, arena_height, size=10):
#    w = arena_width // size
#    h = arena_height // size
#
#    xs = np.arange(w) * size
#    ys = np.arange(h) * size
#
#    grid_x, grid_y = np.meshgrid(xs, ys)
#
#    danger = np.zeros_like(grid_x, dtype=float)
#
#    if not enemies:
#        return danger.flatten()
#
#    for enemy, _ in enemies.values():
#        dx = grid_x - enemy.x
#        dy = grid_y - enemy.y
#
#        dist = np.sqrt(dx * dx + dy * dy)
#
#        r = 10 / (dist + 18)
#
#        danger += r
#
#    danger = danger.flatten()
#
#    # normalize
#    mn = danger.min()
#    mx = danger.max()
#    danger = (danger - mn) / (mx - mn + 1e-9)
#
#    return list(danger)
#
#def normalize(values):
#    min_v = min(values)
#    max_v = max(values)
#
#    if max_v == min_v:
#        return [0.0 for _ in values]  # alle gleich
#
#    return [(v - min_v) / (max_v - min_v) for v in values]

def dir_to_vector(angle_deg:float, length:float=1):
    rad = math.radians(angle_deg)

    x = math.sin(rad) * length
    y = math.cos(rad) * length

    return x, y
def vector_to_dir(vx, vy):
    return (math.degrees(math.atan2(vx, vy)) + 360) % 360

def distance_point_to_line(line_point, line_angle_deg, target_point):
    """
    Berechnet den Abstand eines Punktes zu einer Geraden.

    :param line_point: Tuple (x0, y0) Punkt auf der Geraden
    :param line_angle_deg: Winkel der Geraden in Grad (Robocode-style)
    :param target_point: Tuple (x1, y1) Punkt, zu dem der Abstand berechnet wird
    :return: Abstand als float
    """
    x0, y0 = line_point
    x1, y1 = target_point

    # Robocode: 0° = nach oben, 90° = rechts
    # konvertieren zu Standard-Koordinaten (0° = rechts, counter-clockwise)
    theta_rad = math.radians(90 - line_angle_deg)

    # Richtungsvektor der Geraden
    dx = math.cos(theta_rad)
    dy = math.sin(theta_rad)

    # Abstand = |(P - A) x d| / |d|
    # Kreuzprodukt in 2D: (x1-x0, y1-y0) x (dx, dy) = (x1-x0)*dy - (y1-y0)*dx
    numerator = abs((x1 - x0) * dy - (y1 - y0) * dx)
    denominator = math.hypot(dx, dy)  # ||d||, hier =1, da normiert
    distance = numerator / denominator
    return distance




if __name__ == "__main__":

    x, y = 9, 23
    w = 60
    i = pos_to_id(x, y, w)
    print(i)

    print(id_to_pos(i, w))