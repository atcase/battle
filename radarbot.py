#!/usr/bin/env python3

from dataclasses import dataclass
from robots import RobotCommand, RobotCommandType, Robot
from player import main


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


if __name__ == "__main__":
    driver = RadarDriver()
    main("radarbot", driver)
