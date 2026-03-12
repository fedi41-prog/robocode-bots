import math
import threading

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

def calculate_danger_factor(enemies, arena_width, arena_height,  x: float, y: float):
    res = 0

    if len(enemies) == 0:
        return 0

    for enemy in enemies.values():
        dist = math.dist((enemy.x, enemy.y), (x, y))

        r = 10 / (dist + 18)

        res += r

    return res


def calculate_danger_vector(enemies:dict[int, ScannedBotEvent], x, y, w, h):

    vx = 0
    vy = 0

    for enemy in enemies.values():

        dx = x - enemy.x
        dy = y - enemy.y

        dist = math.hypot(dx, dy) + 0.0001

        strength = enemy.energy / dist**1.5
        if dist < 50:
            strength += 10

        vx += dx / dist * strength
        vy += dy / dist * strength

    # wall repulsion
    wall_strength = 500

    vx += wall_strength / (x + 1) ** 2
    vx -= wall_strength / (w - x + 1) ** 2

    vy += wall_strength / (y + 1) ** 2
    vy -= wall_strength / (h - y + 1) ** 2

    return vx, vy

def normalize(vec):
    vx, vy = vec

    l = math.hypot(vx, vy)

    if l == 0:
        return 0,0

    return vx/l, vy/l

def dir_to_vector(angle_deg:float, length:float=1):
    rad = math.radians(angle_deg)

    x = math.sin(rad) * length
    y = math.cos(rad) * length

    return x, y
def vector_to_dir(vx, vy):
    return (math.degrees(math.atan2(vx, vy)) + 360) % 360

def normalize_angle(a):
    return a % 360

def angle_in_range(angle, start, end):
    angle = normalize_angle(angle)
    start = normalize_angle(start)
    end = normalize_angle(end)

    if start <= end:
        return start <= angle <= end
    else:
        # wrap around 360
        return angle >= start or angle <= end

def find_scan_range(angles):
    if not angles:
        return None

    angles = sorted(a % 360 for a in angles)

    max_gap = 0
    gap_start = 0

    for i in range(len(angles)):
        a = angles[i]
        b = angles[(i + 1) % len(angles)]

        gap = (b - a) % 360

        if gap > max_gap:
            max_gap = gap
            gap_start = a

    start = (gap_start + max_gap) % 360
    end = gap_start % 360

    return start, end


class DebugState:
    def __init__(self):
        self.aim_angle_range = None
        self.real_danger_vector = None
        self.danger_vector = None
        self.enemies = None
        self.gun_direction = None
        self.radar_direction = None
        self.direction = None
        self.y = None
        self.x = None
        self.arena_width = None
        self.arena_height = None

        self.data_loaded = False

    def set_config(self, arena_width, arena_height):

        self.arena_width = arena_width
        self.arena_height = arena_height

    def set(self,
            x,
            y,
            direction,
            radar_direction,
            gun_direction,
            enemies,
            danger_vector,
            real_danger_vector,
            aim_angle_range
            ):

        self.x = x
        self.y = y
        self.direction = direction
        self.radar_direction = radar_direction
        self.gun_direction = gun_direction

        self.enemies = enemies
        self.danger_vector = danger_vector
        self.real_danger_vector = real_danger_vector
        self.aim_angle_range = aim_angle_range
        self.data_loaded = True

    def __str__(self):
        return f"""
        {self.x}
        {self.y}
        {self.direction}
        {self.radar_direction}
        {self.gun_direction}
        {self.enemies}
        {self.danger_vector}
        {self.real_danger_vector}
        {self.aim_angle_range}
"""



if __name__ == "__main__":
    x, y = 9, 23
    w = 60
    i = pos_to_id(x, y, w)
    print(i)
    print(id_to_pos(i, w))