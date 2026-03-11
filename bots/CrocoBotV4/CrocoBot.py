
import threading

from robocode_tank_royale.bot_api import Color
from robocode_tank_royale.bot_api.bot import Bot
from robocode_tank_royale.bot_api.events import ScannedBotEvent, BulletFiredEvent, BotDeathEvent, \
    TickEvent

from bots.CrocoBotV4.util import DebugState, calculate_danger_factor, angle_in_range, find_scan_range
from util import calculate_danger_vector, vector_to_dir, normalize

GREEN = Color.from_rgb(0x00, 0xFF, 0x00)
RED = Color.from_rgb(0xFF, 0x00, 0x00)
WHITE = Color.from_rgb(0xFF, 0xFF, 0xFF)
BLUE = Color.from_rgb(0x00, 0x00, 0xFF)

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


    def __init__(self, debug=False):
        super().__init__()
        self.real_danger_vector: tuple[float, float] = None
        self.danger_vector: tuple[float, float] = None
        self.enemies: dict[int, tuple[ScannedBotEvent, dict]] = {}
        self.debug_state = DebugState()
        self.debug = debug
        self.danger_factor = 0
        self.aim_angle_range = ()

        self.spotted_enemies: set[id] = set()

        self.gun_dir = 1

        self.bot_state = STATE_IDLE


    def run(self) -> None:
        self.body_color = Color.from_hex_color("#ffbe0b")
        self.turret_color = Color.from_hex_color("#fb5607")
        self.radar_color = Color.from_hex_color("#fb5607")
        self.scan_color = Color.from_hex_color("#8ecae6")
        self.bullet_color = Color.from_hex_color("#ff006e")
        self.tracks_color = Color.from_hex_color("#ffbe0b")
        self.gun_color = Color.from_hex_color("#ff006e")

        self.enemies: dict[int, tuple[ScannedBotEvent, dict]] = {}
        self.bot_state = STATE_IDLE
        self.danger_vector = None
        self.real_danger_vector = None
        self.danger_factor = 0
        self.spotted_enemies = set()
        self.aim_angle_range = ()

        self.gun_dir = 1

        self.debug_state.set_config(
            self.arena_width,
            self.arena_height
        )

    def on_scanned_bot(self, e: ScannedBotEvent) -> None:
        """We saw another bot!"""
        self.spotted_enemies.add(e.scanned_bot_id)

        data = {
            "bullet_hit_count": 0
        }

        bot_state = self.bot_state
        if e.scanned_bot_id in self.enemies:
            data = self.enemies[e.scanned_bot_id][1]

        data["last_seen"] = self.turn_number
        self.enemies[e.scanned_bot_id] = (e, data)


        if bot_state == STATE_IDLE:
            if abs(self.gun_bearing_to(e.x, e.y)) < self.max_gun_turn_rate:
                firepower = self.calculate_firepower(e)
                if self.gun_heat == 0 and firepower != 0:
                    self.aim_at(e.x, e.y)
                    self.set_fire(firepower)
                    print("fire!!!")

        self.clean_up_enemies()
    def clean_up_enemies(self):
        if len(self.enemies) > self.enemy_count:
            enemies = list(self.enemies.values())
            enemies.sort(key=lambda x: x[1]["last_seen"], reverse=True)
            for i in range(len(self.enemies) - self.enemy_count):
                e = enemies.pop()
                self.enemies.pop(e[0].scanned_bot_id)

    def calc_edge_bearing(self):

        min_bearing = float("inf")
        max_bearing = float("-inf")

        for e, _ in self.enemies.values():
            b = self.bearing_to(e.x, e.y)

            max_bearing = max(b, max_bearing)
            min_bearing = min(b, min_bearing)

        return min_bearing, max_bearing

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
        if e.victim_id in self.enemies.keys():
            self.enemies.pop(e.victim_id)
        #if self.target_id == e.victim_id:
        #    self.target_id = 0
            #self.change_state(STATE_IDLE)

    def on_tick(self, tick_event: TickEvent) -> None:


        self.update_danger()
        if self.danger_vector is not None:
            nx, ny = self.danger_vector
            dr = (vector_to_dir(nx, ny)+270) % 360
            self.go_to_direction(dr, 50)


        self.aim_angle_range = find_scan_range([self.direction_to(e.x, e.y) for e, _ in self.enemies.values()])

        # GUN MOVEMENT
        if not angle_in_range(self.gun_direction, self.aim_angle_range[0], self.aim_angle_range[1]) or self.gun_turn_rate == 0:
            d0, d1 = abs(self.aim_angle_range[0]-self.gun_direction), abs(self.aim_angle_range[1]-self.gun_direction)
            self.gun_turn_rate = self.max_gun_turn_rate if d0 < d1 else -self.max_gun_turn_rate

        self.radar_turn_rate = self.max_radar_turn_rate

        #else:
        #    t = list(self.enemies.values())[0][0]
        #    self.aim_at(t.x, t.y)


        if self.debug:
            self.debug_state.set(

                self.x,
                self.y,
                self.direction,
                self.radar_direction,
                self.gun_direction,

                self.enemies.copy(),
                self.danger_vector,
                self.real_danger_vector,
                self.aim_angle_range
            )

        self.clean_up_enemies()



    def update_danger(self):

        dvx, dvy = calculate_danger_vector(self.enemies, self.x, self.y, self.arena_width, self.arena_height)

        self.danger_vector = normalize((dvx, -dvy))
        self.real_danger_vector = (dvx, -dvy)

        self.danger_factor = calculate_danger_factor(self.enemies, self.arena_width, self.arena_height, self.x, self.y)

    def go_to_direction(self, d, dist):
        bearing = self.calc_bearing(d)
        self.set_turn_left(bearing)

        if abs(bearing) < 90:
            self.set_forward(dist)
        else:
            self.set_forward(-dist)

def main(debug=False):
    bot = CrocoBot(debug)

    if bot.debug:
        from debug import render_loop
        bot_thread = threading.Thread(target=bot.start, daemon=True)
        bot_thread.start()
        render_loop(bot.debug_state)
    else:
        bot.start()





if __name__ == "__main__":
    main(True)
