#!/usr/bin/env python3
"""radarbot - a demo robot driver for controlling a battle ship

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
class RadarDriver:
    """Stationary driver with a radar search mechanism that improves locking on to targets."""

    turret_dir: float = 90.0
    radar_pinged_last_time: bool = False

    def get_next_command(self, r: Robot):
        if r.cmd_q_len:
            return None
        if r.radar_ping is not None:
            if r.weapon_energy >= 3 and abs(self.turret_dir) < 5:
                return RobotCommand(RobotCommandType.FIRE, 100)
            self.turret_dir = -self.turret_dir / 2
        elif not self.radar_pinged_last_time:
            self.turret_dir = -self.turret_dir * 2

        self.radar_pinged_last_time = r.radar_ping is not None
        self.turret_dir = max(-15, min(90, self.turret_dir))
        return RobotCommand(RobotCommandType.TURN_TURRET, self.turret_dir)


def main():
    driver = RadarDriver()
    player_main("radarbot", driver)


if __name__ == "__main__":
    main()
