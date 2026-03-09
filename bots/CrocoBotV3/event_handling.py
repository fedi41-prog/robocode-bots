from robocode_tank_royale.bot_api.events import ScannedBotEvent, HitByBulletEvent
from robocode_tank_royale.schema import BotDeathEvent


def on_scanned_bot(
        self,
        e:ScannedBotEvent,
        enemies: dict[int, tuple[ScannedBotEvent, dict]]
):
    data = {
        "bullet_hit_count": 0
    }
    if e.scanned_bot_id in enemies:
        data = enemies[e.scanned_bot_id][1]

    enemies[e.scanned_bot_id] = (e, data)

def on_hit_by_bullet(
        self,
        e:HitByBulletEvent,
        enemies: dict[int, tuple[ScannedBotEvent, dict]]
):
    pass

def on_bot_death(
        self,
        e:BotDeathEvent,
        enemies: dict[int, tuple[ScannedBotEvent, dict]]
):
    pass