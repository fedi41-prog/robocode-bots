import asyncio
import math
import queue
import threading
import time


from robocode_tank_royale.bot_api import Color, BulletState
from robocode_tank_royale.bot_api.bot import Bot
from robocode_tank_royale.bot_api.events import ScannedBotEvent, HitByBulletEvent, BulletFiredEvent, BotDeathEvent, \
    TickEvent, Condition, CustomEvent, HitBotEvent, HitWallEvent

from bots.CrocoBotV2.util import pos_to_id
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
# CrocoBot
# ------------------------------------------------------------------
# My Crocodile bot
# ------------------------------------------------------------------
class CrocoBotV2(Bot):


    def __init__(self):
        super().__init__()
        self.danger_map: list[float] = []
        self.enemies: dict[int, tuple[ScannedBotEvent, dict]] = {}

        self.target_id: int = 0
        self.spotted_enemies: set[int] = set()
        self.move_direction = 1

        self.bot_state = STATE_IDLE

        self.compute_queue = queue.Queue()
        self.result_queue = queue.Queue()

        self.lock = threading.Lock()

    def run(self) -> None:
        """Called when a new round is started -> initialize and do some movement."""

        self.body_color = GREEN
        self.turret_color = GREEN
        self.radar_color = GREEN
        self.scan_color = GREEN
        self.bullet_color = GREEN


        self.enemies: dict[int, tuple[ScannedBotEvent, dict]] = {}
        self.target_id: int = 0
        self.spotted_enemies: set[int] = set()
        self.move_direction = 1
        self.bot_state = STATE_IDLE
        self.danger_map = []

        self.compute_queue = queue.Queue()
        self.result_queue = queue.Queue()

        threading.Thread(target=self.compute_loop, daemon=True).start()
        threading.Thread(target=self.main_loop, daemon=True).start()


    def main_loop(self):
        print("main loop starting...")
        # Repeat while the bot is running
        while self.running:
            self.update_color()
            if self.bot_state == STATE_IDLE:
                self.rotate_perpendicular_to_enemies()
                self.gun_turn_rate = self.max_gun_turn_rate

                self.set_forward(50 * self.move_direction)

                # self.set_forward(500)
                # self.set_turn_left(90)

                self.go()

                self.move_direction *= -1

                #df = self.calculate_danger_factor(self.x, self.y)
                #print(df)
            if self.bot_state == STATE_TARGET:
                self.gun_turn_rate = self.max_gun_turn_rate
                self.rotate_perpendicular_to_bot(self.target_id)

                self.forward(50 * self.move_direction)
                self.move_direction *= -1
            if self.bot_state == STATE_MOVING:
                pass




    # =====================
    # =====================





    def rotate_perpendicular_to_bot(self, bot_id):
        b = self.enemies[bot_id][0]
        bearing = self.bearing_to(b.x, b.y)
        if bearing > 90:
            bearing = 180 - bearing
        if bearing <= -90:
            bearing = 180 + bearing

        self.turn_left(bearing)

    async def rotate_perpendicular_to_enemies(self):

        values = []
        weights = []

        for e, _ in self.enemies.values():
            direction = self.direction_to(e.x, e.y)
            distance = self.distance_to(e.x, e.y)

            values.append(direction%180)
            weights.append(1/distance)

        average = weighted_average(values, weights)
        if average == None: return

        bearing = self.calc_bearing(average+90)
        if bearing > 90:
            bearing = 180 - bearing
        if bearing <= -90:
            bearing = 180 + bearing

        self.turn_left(bearing)


    def aim_at(self, bot:ScannedBotEvent):
        bearing = self.gun_bearing_to(bot.x, bot.y)
        self.turn_gun_left(bearing)


    # =====================
    # =====================

    def compute_loop(self):
        print("compute loop starting...")
        while True:
            dm = self.calculate_danger_map()

            with self.lock:
                self.danger_map = dm

            print("danger map updated")


    def calculate_danger_map(self, size: int = 10):
        w, h = self.arena_width // size, self.arena_height // size

        danger_map = [0] * (w * h)

        for x in range(0, w):
            for y in range(0, h):
                i = pos_to_id(x, y, w)
                danger_map[i] = self.calculate_danger_factor(x * size, y * size)

        return danger_map

    def calculate_danger_factor(self, x: float, y: float):
        res = 0

        with self.lock:
            for enemy, _ in self.enemies.values():
                dist = math.dist((enemy.x, enemy.y), (x, y))
                d = (10000 - dist) ** 2
                res += d

        return res / 100000000

    # =======================
    # =======================

    def on_scanned_bot(self, e: ScannedBotEvent) -> None:
        """We saw another bot -> fire!"""
        #d = self.direction_to(e.x, e.y)
        #self.set_turn_gun_right(d)
        with self.lock:
            enemies = self.enemies

        self.spotted_enemies.add(e.scanned_bot_id)

        enemy_direction = e.direction
        enemy_to_bot_direction = self.direction_to(e.x, e.y)
        distance = self.distance_to(e.x, e.y)

        data = {
            "bullet_hit_count":0
        }
        if e.scanned_bot_id in enemies:
            data = enemies[e.scanned_bot_id][1]



        enemies[e.scanned_bot_id] = (e, data)

        if self.bot_state == STATE_IDLE:
            if self.gun_heat == 0:
                firepower = self.calculate_firepower(e)
                if firepower > 0:
                    self.aim_at(e)
                    self.fire(firepower)
        if self.bot_state == STATE_TARGET:
            if e.scanned_bot_id == self.target_id and self.gun_heat == 0:
                self.aim_at(e)
                firepower = self.calculate_firepower(e)
                if firepower > 0:
                    self.aim_at(e)
                    self.fire(firepower)

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



    def on_bot_death(self, e: BotDeathEvent) -> None:
        if e.victim_id in self.enemies.keys():
            self.enemies.pop(e.victim_id)

        if self.target_id == e.victim_id:
            self.target_id = 0
            self.change_state(STATE_IDLE)

    def on_hit_by_bullet(self, e: HitByBulletEvent) -> None:
        bot = e.bullet.owner_id
        if bot in self.enemies:
            hit_count = self.get_bot_data(bot, "bullet_hit_count") + 1
            self.set_bot_data(bot, "bullet_hit_count", hit_count)
            print(f"hit by {bot} X {hit_count}")
            if hit_count > 1:
                self.target_id = bot
                self.change_state(STATE_TARGET)

                print("targeting:", bot)


        else:
            print("hit by unknown bot!")



    # =====================
    # =====================

    def set_bot_data(self, bot_id, data_key, value):
        if bot_id in self.enemies:
            self.enemies[bot_id][1][data_key] = value
        else:
            print("UNKNOWN BOT")
    def get_bot_data(self, bot_id, data_key):
        if bot_id in self.enemies and data_key in self.enemies[bot_id][1]:
            return self.enemies[bot_id][1][data_key]
        else:
            return None

    def is_near_wall(self, margin=18 * 3):
        if margin < self.x < self.arena_width - margin and margin < self.y < self.arena_height - margin:
            return False
        return True
    def on_tick(self, tick_event: TickEvent) -> None:
        pass

    def change_state(self, new_state):
        self.bot_state = new_state
        self.update_color()
    def update_color(self):
        if self.bot_state == STATE_IDLE:
            self.radar_color = GREEN
            self.turret_color = GREEN
        elif self.bot_state == STATE_MOVING:
            self.radar_color = WHITE
            self.turret_color = WHITE
        elif self.bot_state == STATE_SCANNING:
            self.radar_color = BLUE
            self.turret_color = BLUE
        elif self.bot_state == STATE_TARGET:
            self.radar_color = RED
            self.turret_color = RED





async def main() -> None:
    bot = CrocoBotV2()
    bot.start()


if __name__ == "__main__":
    asyncio.run(main())
