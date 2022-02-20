from dataclasses import dataclass, field, replace
from enum import Enum, auto
from math import atan2, cos, sin, pi, sqrt
from random import random
from typing import Callable, Dict, List, Optional


class GameParameters:
    MAX_VELOCITY = 0.005
    MAX_TURN_ANGLE = 45.0
    MAX_TURN_RADAR_ANGLE = 180.0
    MOTOR_POWER = 0.001
    BULLET_VELOCITY = 0.02
    FPS = 20
    MAX_DAMAGE = 0.1
    WEAPON_RECHARGE_RATE = 0.01
    ARENA_WIDTH = 1000.0
    ARENA_HEIGHT = 1000.0
    EXPLODE_FRAMES = 8


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
        return cls(x=random(), y=random())

    def clip(self, margin: float = 0.0) -> bool:
        """Updates the position co-ordinates so they are within the bounds of the arena. Returns true if
        changed."""
        new_x = max(margin, min(1.0 - margin, self.x))
        new_y = max(margin, min(1.0 - margin, self.y))
        if (new_x, new_y) != (self.x, self.y):
            self.x, self.y = (new_x, new_y)
            return True
        return False

    def __sub__(self, other: "Position") -> "PositionDelta":
        """Return the delta between two positions"""
        return PositionDelta(self.x - other.x, self.y - other.y)


@dataclass
class PositionDelta(Position):
    """A position delta, used to determine distance between two positions"""

    x: float
    y: float

    def __abs__(self) -> float:
        return sqrt(self.x * self.x + self.y * self.y)

    def angle(self) -> float:
        return atan2(self.y, self.x) * 180.0 / pi


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
    radius: float = 0.02
    radar_pinged: bool = False
    got_hit: bool = False
    bumped_wall: bool = False

    def live(self) -> bool:
        """Returns whether robot is still alive"""
        return self.health > 0.0


@dataclass
class Missile:
    """The current state of a single missile"""

    position: Position
    angle: float
    energy: float
    exploding: bool = False
    explode_progress: int = 0

    def live(self) -> bool:
        """Returns whether missile has finished exploding"""
        return self.explode_progress < GameParameters.EXPLODE_FRAMES


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
    winner: Optional[str] = None
    robot_drivers: Dict[str, Driver] = field(default_factory=dict)

    def update_robot(self, robot: Robot, command: RobotCommand) -> None:
        """Updates the state of the arena and a single robot based on a command"""
        # print(f"{robot.name} chose to {command.command_type.name}({command.parameter})")
        if command.command_type is RobotCommandType.ACCELERATE:
            robot.velocity += GameParameters.MOTOR_POWER
            robot.velocity = min(GameParameters.MAX_VELOCITY, robot.velocity)
        elif command.command_type is RobotCommandType.DECELERATE:
            robot.velocity -= GameParameters.MOTOR_POWER
            robot.velocity = max(-GameParameters.MAX_VELOCITY, robot.velocity)
        elif command.command_type is RobotCommandType.FIRE:
            # Add a bit of randomness to the weapon energy for entertainment
            # This will also help with tie breakers
            energy_noise = (random() - 0.5) * GameParameters.WEAPON_RECHARGE_RATE
            requested_energy = min(GameParameters.MAX_DAMAGE, command.parameter)
            energy = min(robot.weapon_energy, requested_energy) + energy_noise
            angle = (robot.tank_angle + robot.turret_angle) % 360.0
            robot.weapon_energy = max(0, robot.weapon_energy - energy)
            start_position = replace(robot.position)
            start_position.x += robot.radius * cos(angle / 180 * pi)
            start_position.y += robot.radius * sin(angle / 180 * pi)
            m = Missile(start_position, angle, energy)
            self.missiles.append(m)
        elif command.command_type is RobotCommandType.TURN_TANK:
            robot.tank_angle += min(
                GameParameters.MAX_TURN_ANGLE, max(-GameParameters.MAX_TURN_ANGLE, command.parameter)
            )
            robot.tank_angle %= 360
        elif command.command_type is RobotCommandType.TURN_TURRET:
            robot.turret_angle += command.parameter
            robot.turret_angle %= 360
        elif command.command_type is RobotCommandType.TURN_RADAR:
            robot.radar_angle += min(
                GameParameters.MAX_TURN_RADAR_ANGLE, max(-GameParameters.MAX_TURN_RADAR_ANGLE, command.parameter)
            )
            robot.radar_angle %= 360

        # Update robot position
        robot.position.x += robot.velocity * cos(robot.tank_angle / 180 * pi)
        robot.position.y += robot.velocity * sin(robot.tank_angle / 180 * pi)
        robot.bumped_wall = robot.position.clip(margin=robot.radius)

        # Recharge weapon
        robot.weapon_energy += GameParameters.WEAPON_RECHARGE_RATE
        robot.weapon_energy = min(GameParameters.MAX_DAMAGE, robot.weapon_energy)

    def update_missile(self, missile: Missile) -> None:
        """Updates the state of a single missile"""
        if missile.exploding:
            missile.explode_progress += 1
        else:
            v = GameParameters.BULLET_VELOCITY
            missile.position.x += v * cos(missile.angle / 180 * pi)
            missile.position.y += v * sin(missile.angle / 180 * pi)
            missile.position.clip()

    def update_arena(self) -> None:
        """Updates the state of the arena (all robots & missiles)"""
        # Save prior radar state
        prior_radar_angle = {r.name: r.tank_angle + r.turret_angle + r.radar_angle for r in self.robots}

        # Update all robots
        for robot in self.robots:
            if not robot.live():
                continue
            command = self.robot_drivers[robot.name](robot)
            self.update_robot(robot, command)

        # Update all missiles
        for missile in self.missiles:
            self.update_missile(missile)
        self.missiles = [m for m in self.missiles if m.live()]

        # Missile - Robot collision detection
        for robot in self.robots:
            robot.got_hit = False
        for missile in self.missiles:
            for robot in self.robots:
                if not robot.live():
                    continue
                # print(abs(`robot.position - missile.position))
                if abs(robot.position - missile.position) < robot.radius:
                    if not missile.exploding:
                        print(f"{robot.name} was hit! {robot.health=} {missile.energy=}")
                        robot.health -= missile.energy
                        missile.exploding = True
                        robot.got_hit = True
                        break
            if (
                missile.position.x <= 0
                or missile.position.x >= 1.0
                or missile.position.y <= 0
                or missile.position.y >= 1.0
            ):
                # print(f"Missile hit edge: {missile.position}")
                missile.exploding = True

        # Update radar pings
        for robot in self.robots:
            robot.radar_pinged = False
            if not robot.live():
                continue
            for target in self.robots:
                if robot is target or not target.live():
                    continue

                base_angle = prior_radar_angle[robot.name]
                target_angle = ((target.position - robot.position).angle() - base_angle + 180.0) % 360.0 - 180.0
                now_angle = (
                    robot.tank_angle + robot.turret_angle + robot.radar_angle - base_angle + 180.0
                ) % 360.0 - 180.0
                if (
                    now_angle > 0
                    and target_angle > 0
                    and now_angle > target_angle
                    or now_angle < 0
                    and target_angle < 0
                    and now_angle < target_angle
                ):
                    robot.radar_pinged = True
                    break

    def get_winner(self) -> Optional[Robot]:
        """Returns the winner or None if no winner yet"""
        remaining = [r for r in self.robots if r.live()]
        if len(remaining) == 1:
            return remaining[0]
        if len(remaining) == 0:
            # If all robots are dead, return the one that sustained the least damage
            return max(self.robots, key=lambda r: r.health)
        return None
