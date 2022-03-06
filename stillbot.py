#!/usr/bin/env python3

from dataclasses import dataclass
from robots import RobotCommand, RobotCommandType, Robot
from player import main


@dataclass
class StillDriver:
    """A simple robot driver that spins its turret and fires if its radar pings"""

    pinged: bool = False

    def get_next_command(self, r: Robot):
        if r.radar_ping is not None or self.pinged:
            self.pinged = True
            return RobotCommand(RobotCommandType.FIRE, 100)
        return RobotCommand(RobotCommandType.TURN_TURRET, 5)


if __name__ == "__main__":
    driver = StillDriver()
    main("stillbot", driver)
