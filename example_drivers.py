from dataclasses import dataclass
from robots import RobotCommand, RobotCommandType, Robot


@dataclass
class StillDriver:
    """A simple robot driver that spins its turret and fires if its radar pings"""

    pinged: bool = False

    def get_next_command(self, r: Robot) -> RobotCommand:
        if r.radar_ping is not None or self.pinged:
            self.pinged = True
            return RobotCommand(RobotCommandType.FIRE, 100)
        return RobotCommand(RobotCommandType.TURN_TURRET, 5)


@dataclass
class PongDriver:
    """Starts moving and then maintains the same speed, bouncing off the walls. Fires if radar pings."""

    accelerate_countdown: int = 3

    def get_next_command(self, r: Robot) -> RobotCommand:
        if self.accelerate_countdown:
            self.accelerate_countdown -= 1
            return RobotCommand(RobotCommandType.ACCELERATE, 0)
        if r.bumped_wall:
            self.accelerate_countdown = 3
            return RobotCommand(RobotCommandType.TURN_HULL, -45)

        if r.radar_ping is not None:
            return RobotCommand(RobotCommandType.FIRE, 100)
        return RobotCommand(RobotCommandType.TURN_TURRET, 2)


@dataclass
class RadarDriver:
    """Stationary driver with a radar search mechanism that improves locking on to targets."""

    turret_dir: float = 90.0
    radar_pinged_last_time: bool = False

    def get_next_command(self, r: Robot) -> RobotCommand:
        if r.radar_ping is not None:
            if r.weapon_energy >= 3 and abs(self.turret_dir) < 5:
                return RobotCommand(RobotCommandType.FIRE, 100)
            self.turret_dir = -self.turret_dir / 2
        elif not self.radar_pinged_last_time:
            self.turret_dir = -self.turret_dir * 2

        self.radar_pinged_last_time = r.radar_ping is not None
        self.turret_dir = max(-15, min(90, self.turret_dir))
        return RobotCommand(RobotCommandType.TURN_TURRET, self.turret_dir)
