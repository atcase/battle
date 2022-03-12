from dataclasses import dataclass

from battle.player import player_main
from battle.robots import Robot, RobotCommand, RobotCommandType


@dataclass
class StillDriver:
    """A simple robot driver that spins its turret and fires if its radar pings"""

    pinged: bool = False

    def get_next_command(self, r: Robot):
        if r.radar_ping is not None or self.pinged:
            self.pinged = True
            return RobotCommand(RobotCommandType.FIRE, 100)
        return RobotCommand(RobotCommandType.TURN_TURRET, 5)


def main():
    driver = StillDriver()
    player_main("stillbot", driver)
