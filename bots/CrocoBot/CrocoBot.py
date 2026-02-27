from robocode_tank_royale.bot_api import Color, BulletState
from robocode_tank_royale.bot_api.bot import Bot
from robocode_tank_royale.bot_api.events import ScannedBotEvent, HitByBulletEvent, BulletFiredEvent, BotDeathEvent, \
    TickEvent
import asyncio

GREEN = Color.from_rgb(0x00, 0xFF, 0x00)
RED = Color.from_rgb(0xFF, 0x00, 0x00)
WHITE = Color.from_rgb(0xFF, 0xFF, 0xFF)
COLORS = [
    WHITE,
    RED,
    GREEN
]
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

    def run(self) -> None:
        """Called when a new round is started -> initialize and do some movement."""

        self.body_color = GREEN
        self.turret_color = GREEN
        self.radar_color = GREEN
        self.scan_color = GREEN
        self.bullet_color = GREEN

        # Repeat while the bot is running
        while self.running:
            self.set_turn_radar_right(120)

            facing_at_us = self.get_all_with_tag("facing at us")
            if len(facing_at_us) > 0:
                print(len(facing_at_us))
                self.aim_at(facing_at_us[0][0])
                self.set_fire(1)

                self.radar_color = RED
                self.turret_color = RED
            else:
                self.radar_color = GREEN
                self.turret_color = GREEN

                self.init_fast_scan()
            self.go()

    def init_fast_scan(self):
        self.set_turn_gun_right(60)
        self.set_turn_right(60)
        self.set_turn_radar_right(60)

    def stop_fast_scan(self):
        self.set_turn_gun_right(0)
        self.set_turn_right(0)
        self.set_turn_radar_right(0)


    def aim_at(self, bot:ScannedBotEvent):
        bearing = self.gun_bearing_to(bot.x, bot.y)
        self.set_turn_gun_left(bearing/2)
        self.set_turn_left(bearing/2)


    def update_color(self):
        self.color_tick += 1
        if self.color_tick >= len(COLORS):
            self.color_tick = 0

        self.body_color = COLORS[self.color_tick]


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

        enemy_direction = e.direction
        enemy_to_bot_direction = (self.direction_to(e.x, e.y) + 180) % 360
        #print(enemy_direction, enemy_to_bot_direction)

        tags = []

        if enemy_to_bot_direction - 10 < enemy_direction < enemy_to_bot_direction + 10:
            tags.append("facing at us")
            print("danger")
            self.stop_fast_scan()

        self.enemies[e.scanned_bot_id] = (e, tags)
        self.target_bot = e


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
        # Turn 90 degrees to the bullet direction based on the bearing
        self.turn_right(90 - bearing)


    def on_tick(self, tick_event: TickEvent) -> None:
        #self.update_color()
        pass




async def main() -> None:
    bot = CrocoBot()
    bot.start()


if __name__ == "__main__":
    asyncio.run(main())
