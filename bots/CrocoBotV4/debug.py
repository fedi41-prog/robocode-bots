from time import sleep


import pygame

from bots.CrocoBotV3.util import dir_to_vector
from bots.CrocoBotV4.util import DebugState


def blue_red_gradient(x, gamma=2.0):
    x = max(0, min(1, x))      # clamp
    x = x ** gamma             # nicht-lineare Skalierung

    r = int(255 * x)
    g = 0
    b = int(255 * (1 - x))

    return (r, g, b)

def heatmap_color(x):
    x = max(0, min(1, x))

    colors = [
        (0, 0, 255),    # blau
        (0, 255, 255),  # cyan
        (0, 255, 0),    # grün
        (255, 255, 0),  # gelb
        (255, 0, 0)     # rot
    ]

    n = len(colors) - 1
    pos = x * n
    i = int(pos)
    t = pos - i

    if i >= n:
        return colors[-1]

    c1 = colors[i]
    c2 = colors[i + 1]

    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)

    return (r, g, b)

def to_pg_pos(p, h):
    return p[0], h-p[1]

def render_loop(debug_state:DebugState):
    print("render thread starting...")

    while not debug_state.data_loaded:
        sleep(0.1)

    arena_width = debug_state.arena_width
    arena_height = debug_state.arena_height

    pygame.init()
    screen = pygame.display.set_mode((arena_width, arena_height))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        enemies = debug_state.enemies
        danger_vector = debug_state.danger_vector

        radar_dir = debug_state.radar_direction
        gun_dir = debug_state.gun_direction
        bot_dir = debug_state.direction
        pos = (debug_state.x, debug_state.y)
        aim_range = debug_state.aim_angle_range


        pg_pos = to_pg_pos(pos, arena_height)

        screen.fill((0,0,0))

        for idx, e in enemies.items():


            x, y = to_pg_pos((e.x, e.y), arena_height)

            color = (255, 0, 0)

            pygame.draw.circle(screen, color, (x, y), 5)
            pygame.draw.circle(screen, color, (x, y), 18, 1)
            dx, dy = dir_to_vector(e.direction+90, 18)
            pygame.draw.line(screen, color, (x, y), (x+dx, y+dy), 2)
        # BOT
        pygame.draw.circle(screen, (255, 255, 255), pg_pos, 10)
        pygame.draw.circle(screen, (255, 255, 255), pg_pos, 18, 1)
        # RADAR
        xr, yr = dir_to_vector(radar_dir + 90, 2000)
        pygame.draw.line(screen, (255, 255, 255), pg_pos, (pg_pos[0] + xr, pg_pos[1] + yr), 3)
        # DIRECTION
        xd, yd = dir_to_vector(bot_dir + 90, 50)
        pygame.draw.line(screen, (0, 255, 0), pg_pos, (pg_pos[0] + xd, pg_pos[1] + yd), 3)
        # GUN
        xg, yg = dir_to_vector(gun_dir + 90, 40)
        pygame.draw.line(screen, (255, 255, 0), pg_pos, (pg_pos[0] + xg, pg_pos[1] + yg), 3)
        # AIM RANGE
        if aim_range is not None:
            xa1, ya1 = dir_to_vector(aim_range[0] + 90, 200)
            xa2, ya2 = dir_to_vector(aim_range[1] + 90, 200)
            pygame.draw.line(screen, (0, 255, 255), pg_pos, (pg_pos[0] + xa1, pg_pos[1] + ya1), 4)
            pygame.draw.line(screen, (0, 255, 255), pg_pos, (pg_pos[0] + xa2, pg_pos[1] + ya2), 3)
        # DANGER VECTOR
        if danger_vector is not None:
            pygame.draw.line(screen, (0, 0, 255), pg_pos, (
                pg_pos[0] + danger_vector[0] * 50,
                pg_pos[1] + danger_vector[1] * 50
            ), 5)
        pygame.display.flip()