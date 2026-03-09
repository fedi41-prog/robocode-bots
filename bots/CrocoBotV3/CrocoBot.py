import asyncio
import math
import queue
import threading
import time
from traceback import walk_tb

from robocode_tank_royale.bot_api import Color, BulletState
from robocode_tank_royale.bot_api.bot import Bot
from robocode_tank_royale.bot_api.events import ScannedBotEvent, HitByBulletEvent, BulletFiredEvent, BotDeathEvent, \
    TickEvent, Condition, CustomEvent, HitBotEvent, HitWallEvent

from bots.CrocoBotV3.event_handling import on_scanned_bot, on_hit_by_bullet, on_bot_death
from bots.CrocoBotV3.rendering import render_loop
from bots.CrocoBotV3.util import dir_to_vector, pos_to_id, calculate_danger_vector, vector_to_dir, normalize, \
    project_enemy_movement
from util import weighted_average

GREEN = Color.from_rgb(0x00, 0xFF, 0x00)
RED = Color.from_rgb(0xFF, 0x00, 0x00)
WHITE = Color.from_rgb(0xFF, 0xFF, 0xFF)
BLUE = Color.from_rgb(0x00, 0x00, 0xFF)
COLORS = [
    WHITE,
    RED,
    GREEN
]

STATE_IDLE = 0
STATE_MOVING = 1
STATE_SCANNING = 2
STATE_TARGET = 3


# ------------------------------------------------------------------
# CrocoBot 3.0
# ------------------------------------------------------------------
# My Crocodile bot
# ------------------------------------------------------------------


class CrocoBot(Bot):


    def __init__(self):
        super().__init__()
        self.danger_vector: tuple[float, float] = None
        #self.danger_map: list[float] = []
        #self.danger_map_scale = 10
        self.enemies: dict[int, tuple[ScannedBotEvent, dict]] = {}
        self.enemy_projection: dict[int, tuple[float, float]] = {}

        self.move_direction = 1

        self.bot_state = STATE_IDLE

        self.lock = threading.Lock()


    def run(self) -> None:
        """Called when a new round is started -> initialize and do some movement."""

        self.body_color = GREEN
        self.turret_color = GREEN
        self.radar_color = GREEN
        self.scan_color = GREEN
        self.bullet_color = GREEN

        self.enemies: dict[int, tuple[ScannedBotEvent, dict]] = {}
        self.move_direction = 1
        self.bot_state = STATE_IDLE
        self.danger_vector = None
        self.enemy_projection = {}

        threading.Thread(target=self.compute_loop, daemon=True).start()

    def on_scanned_bot(self, e: ScannedBotEvent) -> None:
        """We saw another bot -> fire!"""
        # d = self.direction_to(e.x, e.y)
        # self.set_turn_gun_right(d)


        #print("scanned bot!!!")

        data = {
            "bullet_hit_count": 0
        }
        with self.lock:
            enemies = self.enemies
            bot_state = self.bot_state
            if e.scanned_bot_id in enemies:
                data = self.enemies[e.scanned_bot_id][1]

            self.enemies[e.scanned_bot_id] = (e, data)
            self.enemy_projection = project_enemy_movement(self.enemies)
            enemy_projection = self.enemy_projection.copy()

        if bot_state == STATE_IDLE:
            firepower = self.calculate_firepower(e)
            if self.gun_heat == 0 and firepower != 0:
                self.aim_at(*enemy_projection[e.scanned_bot_id])
                self.set_fire(firepower)
                print("fire!!!")

    def on_bullet_fired(self, bullet_fired_event: BulletFiredEvent) -> None:
        print("bullet fired!")

    def calculate_firepower(self, enemy: ScannedBotEvent):
        enemy_direction = enemy.direction
        enemy_to_bot_direction = self.direction_to(enemy.x, enemy.y)
        distance = self.distance_to(enemy.x, enemy.y)
        direction_diff = abs(enemy_direction - enemy_to_bot_direction)
        firepower = 0

        if direction_diff < 10 or (direction_diff < 45 and enemy.speed == 0) or self.distance_to(enemy.x, enemy.y) < 50:
            firepower = 3
        elif direction_diff < 45:
            firepower = 2
        elif enemy.speed == 0:
            firepower = 1

        return firepower
    def aim_at(self, x, y):
        bearing = self.gun_bearing_to(x, y)
        self.set_turn_gun_left(bearing)


    def on_bot_death(self, e: BotDeathEvent) -> None:
        with self.lock:
            if e.victim_id in self.enemies.keys():
                self.enemies.pop(e.victim_id)
            #if self.target_id == e.victim_id:
            #    self.target_id = 0
                #self.change_state(STATE_IDLE)

    def compute_loop(self):
        print("compute thread starting...")
        while self.running:
            with self.lock:
                enemies = self.enemies.copy()


            dvx, dvy = normalize(calculate_danger_vector(enemies, self.x, self.y, self.arena_width, self.arena_height))

            danger_vector = dvx, -dvy

            enemy_projection = project_enemy_movement(enemies)

            with self.lock:
                self.danger_vector = danger_vector
                self.enemy_projection = enemy_projection

    def on_tick(self, tick_event: TickEvent) -> None:
        with self.lock:
            enemies = self.enemies
            bot_state = self.bot_state
            move_direction = self.move_direction
            danger_vector = self.danger_vector

        if bot_state == STATE_IDLE:

            if danger_vector is not None:
                #self.go_to_optimal_direction()
                nx, ny = danger_vector
                dr = vector_to_dir(nx, ny)
                self.go_to_direction(dr, 50)


            self.gun_turn_rate = self.max_gun_turn_rate

    def go_to_direction(self, d, dist):
        d += 270
        d %= 360

        bearing = self.calc_bearing(d)
        self.set_turn_left(bearing)
        self.set_forward(dist)



def main():
    bot = CrocoBot()

    bot_thread = threading.Thread(target=bot.start, daemon=True)
    bot_thread.start()


    render_loop(bot)




if __name__ == "__main__":
    main()
