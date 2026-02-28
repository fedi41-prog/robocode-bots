import math

from robocode_tank_royale.bot_api import Color, BulletState
from robocode_tank_royale.bot_api.bot import Bot
from robocode_tank_royale.bot_api.events import ScannedBotEvent, HitByBulletEvent, BulletFiredEvent, BotDeathEvent, \
    TickEvent, Condition, CustomEvent, HitBotEvent, HitWallEvent
import asyncio

GREEN = Color.from_rgb(0x00, 0xFF, 0x00)
RED = Color.from_rgb(0xFF, 0x00, 0x00)
WHITE = Color.from_rgb(0xFF, 0xFF, 0xFF)
BLUE = Color.from_rgb(0x00, 0x00, 0xFF)
COLORS = [
    WHITE,
    RED,
    GREEN
]

STATE_SCANNING = 0
STATE_LOCK_TARGET = 1
# ------------------------------------------------------------------
# CrocoBot
# ------------------------------------------------------------------
# My Crocodile bot
# ------------------------------------------------------------------
class CrocoBot(Bot):



    def __init__(self):
        super().__init__()
        self.bullets: list[BulletState] = []
        self.enemies: dict[int, tuple[ScannedBotEvent, list[str]]] = {}
        self.target_bot: ScannedBotEvent = None
        self.color_tick = 0
        self.spotted_enemies: set[int] = set()
        self.move_direction = 1

        self.bot_state = STATE_SCANNING


    def run(self) -> None:
        """Called when a new round is started -> initialize and do some movement."""

        self.body_color = GREEN
        self.turret_color = GREEN
        self.radar_color = GREEN
        self.scan_color = GREEN
        self.bullet_color = GREEN

        ticks_before_scan = 3

        # Repeat while the bot is running
        while self.running:
            self.update_color()
            if self.bot_state == STATE_SCANNING:
                facing_at_us = self.get_all_with_tag("facing at us")
                if len(facing_at_us) > 0:
                    self.bot_state = STATE_LOCK_TARGET

                    self.target_bot = facing_at_us[0]

                else:

                    self.update_radar()


            if self.bot_state == STATE_LOCK_TARGET:
                self.align_radar()
                self.aim_at(self.target_bot[0])

            self.update_movement()
            self.update_gun()

            self.go()

    def can_hit_any_bot(self):

        for i in self.enemies.keys():
            e = self.enemies[i][0]
            if self.can_hit(e.x, e.y):
                print("can shoot", e.scanned_bot_id)
                return True

        return False

    def can_hit(self, x, y, radius=18):
        # Richtungsvektor Gun
        theta = math.radians(90 - self.gun_direction)
        dx, dy = math.cos(theta), math.sin(theta)

        # Vektor zum Ziel
        vx, vy = x - self.x, y - self.y

        # Projektion (Skalarprodukt)
        forward = vx * dx + vy * dy
        if forward > 0:
            return False  # Ziel ist hinter uns

        dist = distance_point_to_line((self.x, self.y), self.gun_direction, (x, y))
        return dist <= radius and angle_diff(
            self.direction_to(x, y),
            self.gun_direction
        ) <= 45



    def align_radar(self):
        bearing = self.calc_radar_bearing(self.gun_direction)
        self.set_turn_radar_left(bearing)


    def stop_radar(self):
        self.radar_turn_rate = 0

    def update_gun(self):
        if self.can_hit_any_bot(): self.set_fire(2)

        if self.bot_state == STATE_SCANNING:
            self.gun_turn_rate = self.max_gun_turn_rate

        #if self.target_bot:
        #self.aim_at(self.target_bot)

    def update_radar(self):
        if self.radar_turn_rate == 0:
            self.radar_turn_rate = self.max_radar_turn_rate
        if len(self.spotted_enemies) >= self.enemy_count:
            self.radar_turn_rate *= -1

            self.spotted_enemies = set()
    def update_movement(self):

        self.target_speed = self.max_speed * self.move_direction
        if self.is_near_wall(150):
            bearing = self.bearing_to(self.arena_width/2, self.arena_height/2)
            self.set_turn_left(bearing*self.move_direction)
            print("near to wall!")

            self.target_speed /= 2

    def on_hit_bot(self, bot_hit_bot_event: HitBotEvent) -> None:
        self.move_direction *= -1

    def on_hit_wall(self, bot_hit_wall_event: HitWallEvent) -> None:
        self.move_direction *= -1

    def is_near_wall(self, margin=18*3):
        if margin < self.x < self.arena_width - margin and margin < self.y < self.arena_height - margin:
            return False
        return True


    def aim_at(self, bot:ScannedBotEvent):
        bearing = self.gun_bearing_to(bot.x, bot.y)

        self.set_turn_gun_left(bearing)
        bearing2 = self.bearing_to(bot.x, bot.y)
        self.set_turn_left((180 - bearing2)%180)


    def update_color(self):
        if self.bot_state == STATE_SCANNING:
            self.radar_color = BLUE
            self.turret_color = BLUE
        elif self.bot_state == STATE_LOCK_TARGET:
            self.radar_color = RED
            self.turret_color = RED
        else:
            self.radar_color = GREEN
            self.turret_color = GREEN


    def get_all_with_tag(self, tag:str) -> list[tuple[ScannedBotEvent, list]]:
        res = []
        for i in self.enemies.keys():
            e = self.enemies[i]
            if tag in e[1]:
                res.append(e)

        return res

    def on_scanned_bot(self, e: ScannedBotEvent) -> None:
        """We saw another bot -> fire!"""
        #d = self.direction_to(e.x, e.y)
        #self.set_turn_gun_right(d)

        self.spotted_enemies.add(e.scanned_bot_id)
        self.update_radar()

        enemy_direction = e.direction
        enemy_to_bot_direction = self.direction_to(e.x, e.y)
        #print(enemy_direction, enemy_to_bot_direction)

        tags = []

        bullet_laser_dist = distance_point_to_line((e.x, e.y), enemy_direction, (self.x, self.y))

        if bullet_laser_dist <= 18:
            tags.append("facing at us")
            print("danger")



        self.enemies[e.scanned_bot_id] = (e, tags)

        self.aim_at(e)

        if self.can_hit_any_bot(): self.set_fire(2)


        #bearing = self.bearing_to(float(e.x), float(e.y))
        #bearing_from_gun = self.gun_bearing_to(float(e.x), float(e.y))
        ## Turn the gun toward the scanned bot
        #self.set_turn_left(bearing+90)
        #self.set_turn_gun_left(bearing_from_gun-90)

        # If it is close enough and gun is cool, fire with power based on alignment & energy
        #if abs(bearing_from_gun) <= 3 and self.gun_heat == 0:
        #    firepower = min(3 - abs(bearing_from_gun), self.energy - 0.1)
        #    if firepower > 0:
        #        self.set_fire(firepower)


    def on_bot_death(self, e: BotDeathEvent) -> None:
        if e.victim_id in self.enemies.keys():
            self.enemies.pop(e.victim_id)

        if self.target_bot.scanned_bot_id == e.victim_id:
            self.target_bot = None

    def on_hit_by_bullet(self, e: HitByBulletEvent) -> None:
        """We were hit by a bullet -> turn perpendicular to the bullet."""
        # Calculate the bearing to the direction of the bullet
        bearing = self.calc_bearing(e.bullet.direction)
        bearing2 = self.calc_gun_bearing(e.bullet.direction)
        # Turn 90 degrees to the bullet direction based on the bearing
        self.turn_right(90 - bearing)
        self.turn_gun_right(180 - bearing2)


    def on_tick(self, tick_event: TickEvent) -> None:
        #self.update_color()
        pass



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
    bot = CrocoBot()
    bot.start()


if __name__ == "__main__":
    asyncio.run(main())
