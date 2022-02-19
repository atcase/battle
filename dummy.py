from dataclasses import dataclass
from robots import RobotCommand, RobotCommandType, Robot

@dataclass
class StillDriver:
    pinged: bool = False

    def __call__(self, r: Robot) -> RobotCommand:
        if r.radar_pinged or self.pinged:
            self.pinged = True
            return RobotCommand(RobotCommandType.FIRE, 1.0)
        return RobotCommand(RobotCommandType.TURN_TURRET, 1.0)

@dataclass
class PongDriver:
    starting: bool = True

    def __call__(self, r: Robot) -> RobotCommand:
        if self.starting:
            self.starting = False
            return RobotCommand(RobotCommandType.ACCELERATE, 0.0)
        if r.position.x == 0.0 or r.position.x == 1.0 or r.position.y == 0.0 or r.position.y == 1.0:
            return RobotCommand(RobotCommandType.TURN_TANK, -45.0)

        if r.radar_pinged:
            return RobotCommand(RobotCommandType.FIRE, 1.0)
        return RobotCommand(RobotCommandType.TURN_TURRET, 3.0)

@dataclass
class RadarDriver:
    turret_dir: float = 2.0

    def __call__(self, r:Robot) -> RobotCommand:
        if r.radar_pinged:
            self.turret_dir = -self.turret_dir
            return RobotCommand(RobotCommandType.FIRE, 1.0)
        return RobotCommand(RobotCommandType.TURN_TURRET, self.turret_dir)