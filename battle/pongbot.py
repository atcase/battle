#!/usr/bin/env python3
"""pongbot - a demo robot driver for controlling a battle ship

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
class PongDriver:
    """Starts moving and then maintains the same speed, bouncing off the walls. Fires if radar pings."""

    def get_next_command(self, r: Robot):
        if r.cmd_q_len:
            return None
        if r.bumped_wall or r.got_hit:
            return [
                RobotCommand(RobotCommandType.TURN_HULL, -45),
                RobotCommand(RobotCommandType.TURN_TURRET, 45),
                RobotCommand(RobotCommandType.ACCELERATE, 0),
                RobotCommand(RobotCommandType.ACCELERATE, 0),
                RobotCommand(RobotCommandType.ACCELERATE, 0),
            ]
        elif abs((r.velocity_angle - r.hull_angle + 180) % 360 - 180) > 1 or r.velocity == 0:
            return [
                RobotCommand(RobotCommandType.ACCELERATE, 0),
                RobotCommand(RobotCommandType.ACCELERATE, 0),
                RobotCommand(RobotCommandType.ACCELERATE, 0),
                RobotCommand(RobotCommandType.ACCELERATE, 0),
            ]

        if r.radar_ping is not None:
            return RobotCommand(RobotCommandType.FIRE, 100)
        return RobotCommand(RobotCommandType.TURN_TURRET, 2)


def main():
    driver = PongDriver()
    player_main("pongbot", driver)
