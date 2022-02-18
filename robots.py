from dataclasses import dataclass, field
from enum import Enum, auto
from math import cos, sin, pi
from random import random
from typing import Callable, Dict, List


class GameParameters:
    MAX_VELOCITY = 10.0
    MAX_TURN_ANGLE = 45
    MOTOR_POWER = 1.0
    BULLET_VELOCITY = 20.0
    FPS = 10
    MAX_DAMAGE = 0.1
    WEAPON_RECHARGE_RATE = 0.1
    ARENA_WIDTH = 1000.0
    ARENA_HEIGHT = 1000.0


def random_angle() -> float:
    """Returns a random angle in the range 0..360"""
    return random() * 360.0


@dataclass
class Position:
    """A position, used for either robots or missiles"""
    x: float
    y: float

    @classmethod
    def random(cls) -> "Position":
        """Returns a new random position]"""
        return cls(x=random() * GameParameters.ARENA_WIDTH, y=random() * GameParameters.ARENA_HEIGHT)

    def clip(self) -> None:
        """Updates the position co-ordinates so they are within the bounds of the arena"""
        self.x = max(0, min(GameParameters.ARENA_WIDTH, self.x))
        self.y = max(0, min(GameParameters.ARENA_HEIGHT, self.y))


@dataclass
class Robot:
    """The current state of a single robot"""
    name: str
    position: Position = field(default_factory=Position.random)
    velocity: float = 0.0
    tank_angle: float = field(default_factory=random_angle)
    turret_angle: float = 0.0
    radar_angle: float = 0.0
    health: float = 1.0
    weapon_energy: float = 1.0
    radius: float = 0.01

@dataclass
class Missile:
    """The current state of a single missile"""
    position: Position
    angle: float
    energy: float
    exploding: bool = False
    explode_progress: int = 0


class RobotCommandType(Enum):
    ACCELERATE = auto()
    DECELERATE = auto()
    FIRE = auto()
    TURN_TANK = auto()
    TURN_TURRET = auto()
    TURN_RADAR = auto()
    IDLE = auto()

@dataclass
class RobotCommand:
    command_type: RobotCommandType
    parameter: float


Driver = Callable[[Robot], RobotCommand]




@dataclass
class Arena:
    """The battle arena"""
    robots: List[Robot] = field(default_factory=list)
    missiles: List[Missile] = field(default_factory=list)
    robot_drivers: Dict[str, Driver] = field(default_factory=dict)

    def update_robot(self, robot: Robot, command: RobotCommand) -> None:
        """Updates the state of the arena and a single robot based on a command"""
        if command == RobotCommandType.ACCELERATE:
            robot.velocity += GameParameters.MOTOR_POWER
            robot.velocity = min(GameParameters.MAX_VELOCITY, robot.velocity)
        elif command == RobotCommandType.DECELERATE:
            robot.velocity -= GameParameters.MOTOR_POWER
            robot.velocity = max(-GameParameters.MAX_VELOCITY, robot.velocity)
        elif command == RobotCommandType.FIRE:
            energy = min(robot.weapon_energy, command.parameter)
            angle = robot.tank_angle + robot.turret_angle
            robot.weapon_energy = max(0, robot.weapon_energy - command.parameter)
            m = Missile(robot.position, angle, energy)
            self.missiles.append(m)
        elif command == RobotCommandType.TURN_TANK:
            robot.tank_angle += min(GameParameters.MAX_TURN_ANGLE, max(-GameParameters.MAX_TURN_ANGLE, command.parameter))
            robot.tank_angle %= 360
        elif command == RobotCommandType.TURN_TURRET:
            robot.turret_angle += command.parameter
            robot.turret_angle %= 360
        elif command == RobotCommandType.TURN_RADAR:
            robot.radar_angle += command.parameter
            robot.radar_angle %= 360
        
        # Update robot position
        robot.position.x += robot.velocity * cos(robot.tank_angle / 180 * pi)
        robot.position.y += robot.velocity * sin(robot.tank_angle / 180 * pi)
        robot.position.clip()

    def update_missile(self, missile: Missile) -> None:
        """Updates the state of a single missile"""
        if missile.exploding:
            missile.explode_progress += 1
        else:
            v = GameParameters.BULLET_VELOCITY
            missile.position.x += v * cos(missile.angle / 180 * pi)
            missile.position.y += v * sin(missile.angle / 180 * pi)
            missile.position.clip()

    def update_arena(self):
        """Updates the state of the arena (all robots & missiles)"""
        # Update all robots
        for robot in self.robots:
            command = self.robot_drivers[robot.name](robot)
            self.update_robot(robot, command)
        # Update all missiles
        for missile in self.missiles:
            self.update_missile(missile)
        # Collision detection (incl. walls)
        

def main():
    a = Arena(1000, 1000)
    robot = Robot("sample")
    a.robots.append(robot)


if __name__ == "__main__":
    main()
