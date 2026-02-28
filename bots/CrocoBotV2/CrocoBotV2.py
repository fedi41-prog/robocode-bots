import asyncio
import math

from robocode_tank_royale.bot_api import Color, BulletState
from robocode_tank_royale.bot_api.bot import Bot
from robocode_tank_royale.bot_api.events import ScannedBotEvent, HitByBulletEvent, BulletFiredEvent, BotDeathEvent, \
    TickEvent, Condition, CustomEvent, HitBotEvent, HitWallEvent


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
        self.bullets: list[BulletState] = []
        self.enemies: dict[int, tuple[ScannedBotEvent, list[str]]] = {}
        self.target: ScannedBotEvent = None
        self.color_tick = 0
        self.spotted_enemies: set[int] = set()
        self.move_direction = 1

        self.bot_state = STATE_IDLE


    def run(self) -> None:
        """Called when a new round is started -> initialize and do some movement."""

        self.body_color = GREEN
        self.turret_color = GREEN
        self.radar_color = GREEN
        self.scan_color = GREEN
        self.bullet_color = GREEN

        self.turn_radar_left(10)

        # Repeat while the bot is running
        while self.running:
            self.update_color()
            if self.bot_state == STATE_IDLE:
                self.rotate_perpendicular_to_enemies()
                self.gun_turn_rate = self.max_gun_turn_rate

                self.forward(50 * self.move_direction)
                self.move_direction *= -1


    # =====================
    # =====================

    def rotate_perpendicular_to_enemies(self):

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

        print(bearing)
        self.turn_left(abs(bearing))


    def aim_at(self, bot:ScannedBotEvent):
        bearing = self.gun_bearing_to(bot.x, bot.y)
        self.set_turn_gun_left(bearing)


    # =====================
    # =====================


    def on_scanned_bot(self, e: ScannedBotEvent) -> None:
        """We saw another bot -> fire!"""
        #d = self.direction_to(e.x, e.y)
        #self.set_turn_gun_right(d)

        self.spotted_enemies.add(e.scanned_bot_id)

        enemy_direction = e.direction
        enemy_to_bot_direction = self.direction_to(e.x, e.y)

        tags = []

        # tags hinzufügen

        self.enemies[e.scanned_bot_id] = (e, tags)

        if self.bot_state == STATE_IDLE:
            direction_diff = abs(enemy_direction - enemy_to_bot_direction)
            if direction_diff < 10 or direction_diff < 45 and e.speed == 0:
                self.fire(3)
            elif direction_diff < 45: #Feind schlecht positioniert
                self.fire(2)
            else:
                self.fire(1)


    def on_bot_death(self, e: BotDeathEvent) -> None:
        if e.victim_id in self.enemies.keys():
            self.enemies.pop(e.victim_id)

        if self.target.scanned_bot_id == e.victim_id:
            self.target = None


    # =====================
    # =====================

    def get_all_with_tag(self, tag:str) -> list[tuple[ScannedBotEvent, list]]:
        res = []
        for i in self.enemies.keys():
            e = self.enemies[i]
            if tag in e[1]:
                res.append(e)

        return res
    def is_near_wall(self, margin=18 * 3):
        if margin < self.x < self.arena_width - margin and margin < self.y < self.arena_height - margin:
            return False
        return True
    def on_tick(self, tick_event: TickEvent) -> None:
        pass
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


def weighted_average(values, weights) -> float:
    if sum(weights) == 0 or len(values) < 0: return None
    return sum(w * g for w, g in zip(values, weights)) / sum(weights)

def angle_diff(a, b):
    d = (a - b + 180) % 360 - 180
    return abs(d)

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


async def main() -> None:
    bot = CrocoBotV2()
    bot.start()


if __name__ == "__main__":
    asyncio.run(main())
