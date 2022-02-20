from dataclasses import dataclass
from robots import RobotCommand, RobotCommandType, Robot


@dataclass
class StillDriver:
    """A simple robot driver that spins its turret and fires if its radar pings"""

    pinged: bool = False

    def __call__(self, r: Robot) -> RobotCommand:
        if r.radar_pinged or self.pinged:
            self.pinged = True
            return RobotCommand(RobotCommandType.FIRE, 1.0)
        return RobotCommand(RobotCommandType.TURN_TURRET, 1.0)


@dataclass
class PongDriver:
    """Starts moving and then maintains the same speed, bouncing off the walls. Fires if radar pings."""

    accelerate_countdown: int = 3

    def __call__(self, r: Robot) -> RobotCommand:
        if self.accelerate_countdown:
            self.accelerate_countdown -= 1
            return RobotCommand(RobotCommandType.ACCELERATE, 0.0)
        if r.bumped_wall:
            return RobotCommand(RobotCommandType.TURN_TANK, -45.0)

        if r.radar_pinged:
            return RobotCommand(RobotCommandType.FIRE, 1.0)
        return RobotCommand(RobotCommandType.TURN_TURRET, 3.0)


@dataclass
class RadarDriver:
    """Stationary driver with a radar search mechanism that improves locking on to targets."""

    turret_dir: float = 5.0

    def __call__(self, r: Robot) -> RobotCommand:
        if r.radar_pinged:
            self.turret_dir = -self.turret_dir
            return RobotCommand(RobotCommandType.FIRE, 1.0)
        return RobotCommand(RobotCommandType.TURN_TURRET, self.turret_dir)
