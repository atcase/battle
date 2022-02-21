from dataclasses import dataclass
from robots import RobotCommand, RobotCommandType, Robot


@dataclass
class StillDriver:
    """A simple robot driver that spins its turret and fires if its radar pings"""

    pinged: bool = False

    def __call__(self, r: Robot) -> RobotCommand:
        if r.radar_pinged or self.pinged:
            self.pinged = True
            return RobotCommand(RobotCommandType.FIRE, 100)
        return RobotCommand(RobotCommandType.TURN_TURRET, 1)


@dataclass
class PongDriver:
    """Starts moving and then maintains the same speed, bouncing off the walls. Fires if radar pings."""

    accelerate_countdown: int = 3

    def __call__(self, r: Robot) -> RobotCommand:
        if self.accelerate_countdown:
            self.accelerate_countdown -= 1
            return RobotCommand(RobotCommandType.ACCELERATE, 0)
        if r.bumped_wall:
            return RobotCommand(RobotCommandType.TURN_TANK, -45)

        if r.radar_pinged:
            return RobotCommand(RobotCommandType.FIRE, 100)
        return RobotCommand(RobotCommandType.TURN_TURRET, 2)


@dataclass
class RadarDriver:
    """Stationary driver with a radar search mechanism that improves locking on to targets."""

    turret_dir: int = 3

    def __call__(self, r: Robot) -> RobotCommand:
        if r.radar_pinged:
            self.turret_dir = -self.turret_dir
            return RobotCommand(RobotCommandType.FIRE, 100)
        return RobotCommand(RobotCommandType.TURN_TURRET, self.turret_dir)
