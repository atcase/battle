#!/usr/bin/env python3
"""stillbot - a demo robot driver for controlling a battle ship

This example file can be copied as a basis for your own robot. Copy it into a local
folder, rename it to e.g. yourbot.py, start editing and run it from the command line as:

  $ python3 yourbot.py

You'll want to edit the default name of your bots in the last line of this file, e.g.

  player_main("yourbot", driver)
"""

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
