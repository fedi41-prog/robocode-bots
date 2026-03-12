
import threading

from robocode_tank_royale.bot_api import Color
from robocode_tank_royale.bot_api.bot import Bot
from robocode_tank_royale.bot_api.events import ScannedBotEvent, BulletFiredEvent, BotDeathEvent, \
    TickEvent, WonRoundEvent, GameEndedEvent, RoundEndedEvent

from bots.CrocoBotV4.util import DebugState, calculate_danger_factor, angle_in_range, find_scan_range
from util import calculate_danger_vector, vector_to_dir, normalize

GREEN = Color.from_rgb(0x00, 0xFF, 0x00)
RED = Color.from_rgb(0xFF, 0x00, 0x00)
WHITE = Color.from_rgb(0xFF, 0xFF, 0xFF)
BLUE = Color.from_rgb(0x00, 0x00, 0xFF)

MODE_IDLE = 0
MODE_ESCAPE = 1
MODE_RAM = 2
MODE_AIMING = 3

STATE_MULTI = 10
STATE_ENDGAME = 11
STATE_SHOWDOWN = 12



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
        self.enemies: dict[int, ScannedBotEvent] = {}
        self.debug_state = DebugState()
        self.debug = debug
        self.danger_factor = 0
        self.aim_angle_range = ()
        self.spotted_enemies = set()

        self.gun_dir = 1

        self.bot_mode = MODE_IDLE
        self.round_state = STATE_MULTI

        self.last_scanned_enemies = []


    def run(self) -> None:
        self.body_color = Color.from_hex_color("#6a994e")
        self.turret_color = Color.from_hex_color("#6a994e")
        self.radar_color = Color.from_hex_color("#a7c957")
        self.scan_color = Color.from_hex_color("#a7c957")
        self.bullet_color = Color.from_hex_color("#bc4749")
        self.tracks_color = Color.from_hex_color("#f2e8cf")
        self.gun_color = Color.from_hex_color("#6a994e")

        self.enemies: dict[int, tuple[ScannedBotEvent, dict]] = {}
        self.bot_mode = MODE_IDLE
        self.round_state = STATE_MULTI
        self.danger_vector = None
        self.real_danger_vector = None
        self.danger_factor = 0
        self.aim_angle_range = ()

        self.last_scanned_enemies = []
        self.spotted_enemies = set()

        self.gun_dir = 1

        self.debug_state.set_config(
            self.arena_width,
            self.arena_height
        )

        print(self.calc_gun_heat(0.1))


    def on_round_ended(self, round_ended_event: RoundEndedEvent) -> None:
        print(self.debug_state)
        print(len(self.last_scanned_enemies))

    def on_scanned_bot(self, e: ScannedBotEvent) -> None:
        """We saw another bot!"""
        if e.scanned_bot_id in self.last_scanned_enemies:
            self.last_scanned_enemies.remove(e.scanned_bot_id)
            self.last_scanned_enemies.append(e.scanned_bot_id)
        else:
            self.last_scanned_enemies.append(e.scanned_bot_id)

        self.spotted_enemies.add(e.scanned_bot_id)

        self.enemies[e.scanned_bot_id] = e

        if self.round_state == STATE_SHOWDOWN:
            self.aim_at(e.x, e.y)
            if abs(self.gun_bearing_to(e.x, e.y)) < self.max_gun_turn_rate:
                firepower = self.calculate_firepower(e)
                if self.gun_heat == 0 and firepower != 0:
                    self.set_fire(firepower)

            self.rescan()
        else:
            if self.bot_mode == MODE_IDLE:
                if abs(self.gun_bearing_to(e.x, e.y)) < self.max_gun_turn_rate:
                    firepower = self.calculate_firepower(e)
                    if self.gun_heat == 0 and firepower > 0.5:
                        self.aim_at(e.x, e.y)
                        self.set_fire(firepower)
                        self.bot_mode = MODE_AIMING


    def on_bullet_fired(self, bullet_fired_event: BulletFiredEvent) -> None:
        if self.bot_mode == MODE_AIMING:
            self.bot_mode = MODE_IDLE

    def clean_up_enemies(self):

        if len(self.last_scanned_enemies) > self.enemy_count:
            for _ in range(len(self.last_scanned_enemies) - self.enemy_count):
                e = self.last_scanned_enemies.pop(0)
                if e in self.enemies: self.enemies.pop(e)



    def calc_edge_bearing(self):

        min_bearing = float("inf")
        max_bearing = float("-inf")

        for e in self.enemies.values():
            b = self.bearing_to(e.x, e.y)

            max_bearing = max(b, max_bearing)
            min_bearing = min(b, min_bearing)

        return min_bearing, max_bearing

    def calculate_firepower(self, enemy: ScannedBotEvent):
        enemy_direction = enemy.direction
        enemy_to_bot_direction = self.direction_to(enemy.x, enemy.y)
        distance = self.distance_to(enemy.x, enemy.y)
        direction_diff = abs(enemy_direction - enemy_to_bot_direction)

        p = (
                (0.75 if direction_diff == 0 else 0.75 / direction_diff) +
                (1.25 if enemy.speed == 0 else 1.25 / enemy.speed) +
                (1.5 if distance == 0 else 1.5 / (distance/5))
        )
        firepower = max(0.1, min(3.0, p))

        return firepower
    def aim_at(self, x, y):
        bearing = self.gun_bearing_to(x, y)
        self.set_turn_gun_left(bearing)


    def on_bot_death(self, e: BotDeathEvent) -> None:
        if e.victim_id in self.enemies.keys():
            self.enemies.pop(e.victim_id)


    def on_tick(self, tick_event: TickEvent) -> None:


        self.update_danger()
        self.update_round_state()

        if self.round_state == STATE_MULTI or self.round_state == STATE_ENDGAME:
            if self.bot_mode == MODE_IDLE:
                if self.danger_vector is not None and self.turn_remaining == 0:
                    nx, ny = self.danger_vector
                    dr = (vector_to_dir(nx, ny)+270) % 360

                    self.go_to_direction(dr, 50)

                    #bearing = self.calc_bearing(dr)
                    #if not -self.max_turn_rate < bearing < self.max_turn_rate:
                    #    if bearing < 0: self.turn_rate = -self.max_turn_rate
                    #    else: self.turn_rate = self.max_turn_rate
                    #self.target_speed = self.max_speed

                self.aim_angle_range = find_scan_range([self.direction_to(e.x, e.y) for e in self.enemies.values()])

                # GUN MOVEMENT
                if self.aim_angle_range is not None and (not angle_in_range(self.gun_direction, self.aim_angle_range[0], self.aim_angle_range[1]) or self.gun_turn_rate == 0):
                    d0, d1 = abs(self.aim_angle_range[0]-self.gun_direction), abs(self.aim_angle_range[1]-self.gun_direction)
                    self.gun_turn_rate = self.max_gun_turn_rate if d0 < d1 else -self.max_gun_turn_rate


                if self.radar_turn_rate == 0:
                    self.radar_turn_rate = self.max_radar_turn_rate
                if len(self.spotted_enemies) >= self.enemy_count:
                    self.radar_turn_rate *= -1
                    self.spotted_enemies = set()
        elif self.round_state == STATE_SHOWDOWN:
            if self.last_scanned_enemies[-1] in self.enemies:
                enemy = self.enemies[self.last_scanned_enemies[-1]]

                self.target_speed = self.max_speed / 2
                self.turn_rate = self.max_turn_rate

                if self.gun_direction != self.radar_direction:
                    self.set_turn_radar_left(self.calc_radar_bearing(self.gun_direction))



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
                self.aim_angle_range if self.enemy_count != 1 else None
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

    def update_round_state(self):
        if self.enemy_count == 1:
            self.round_state = STATE_SHOWDOWN
            print("SHOWDOWN")
        elif self.enemy_count <= 4:
            self.round_state = STATE_ENDGAME
        else:
            self.round_state = STATE_MULTI

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
