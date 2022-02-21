from dataclasses import dataclass, field, replace
from enum import Enum, auto
from math import atan2, cos, sin, pi, sqrt
from random import randint
from typing import Dict, List, Optional


class GameParameters:
    MAX_VELOCITY = 5
    MAX_TURN_ANGLE = 15
    MAX_TURN_RADAR_ANGLE = 180
    MOTOR_POWER = 1
    BULLET_VELOCITY = 20
    FPS = 20
    COMMAND_RATE = 2
    MAX_DAMAGE = 5
    WEAPON_RECHARGE_RATE = 1
    ARENA_WIDTH = 1000
    ARENA_HEIGHT = 1000
    EXPLODE_FRAMES = 8


def random_angle() -> int:
    """Returns a random angle in the range 0..360"""
    return randint(0, 359)


@dataclass
class Position:
    """A position, used for either robots or missiles"""

    x: int
    y: int

    @classmethod
    def random(cls) -> "Position":
        """Returns a new random position]"""
        return cls(
            x=randint(0, GameParameters.ARENA_WIDTH),
            y=randint(0, GameParameters.ARENA_HEIGHT),
        )

    def clip(self, margin: int = 0) -> bool:
        """Updates the position co-ordinates so they are within the bounds of the arena. Returns true if
        changed."""
        new_x = max(margin, min(GameParameters.ARENA_WIDTH - margin, self.x))
        new_y = max(margin, min(GameParameters.ARENA_HEIGHT - margin, self.y))
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

    x: int
    y: int

    def __abs__(self) -> float:
        return sqrt(self.x * self.x + self.y * self.y)

    def angle(self) -> float:
        return atan2(self.y, self.x) * 180.0 / pi


@dataclass
class Robot:
    """The current state of a single robot"""

    name: str
    position: Position = field(default_factory=Position.random)
    velocity: int = 0
    tank_angle: int = field(default_factory=random_angle)
    turret_angle: int = 0
    radar_angle: int = 0
    health: int = 100
    weapon_energy: int = 100
    radius: int = 20
    radar_pinged: bool = False
    got_hit: bool = False
    bumped_wall: bool = False

    def live(self) -> bool:
        """Returns whether robot is still alive"""
        return self.health > 0


@dataclass
class Missile:
    """The current state of a single missile"""

    position: Position
    angle: float
    energy: int
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
    parameter: int


@dataclass
class Arena:
    """The battle arena"""

    robots: List[Robot] = field(default_factory=list)
    missiles: List[Missile] = field(default_factory=list)
    winner: Optional[str] = None

    _prior_radar_angle = {}

    def update_robot_command(self, robot: Robot, command: RobotCommand) -> None:
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
            energy_noise = randint(-1, 1)
            requested_energy = GameParameters.MAX_DAMAGE * min(100, max(0, command.parameter))
            energy = min(robot.weapon_energy, requested_energy) + energy_noise
            energy = int(max(0, energy))
            angle = int((robot.tank_angle + robot.turret_angle) % 360)
            robot.weapon_energy = max(0, robot.weapon_energy - energy)
            start_position = replace(robot.position)
            start_position.x += int(2 * robot.radius * cos(angle / 180 * pi))
            start_position.y += int(2 * robot.radius * sin(angle / 180 * pi))
            m = Missile(start_position, angle, energy)
            self.missiles.append(m)
        elif command.command_type is RobotCommandType.TURN_TANK:
            robot.tank_angle += min(
                GameParameters.MAX_TURN_ANGLE,
                max(-GameParameters.MAX_TURN_ANGLE, command.parameter),
            )
            robot.tank_angle %= 360
        elif command.command_type is RobotCommandType.TURN_TURRET:
            robot.turret_angle += command.parameter
            robot.turret_angle %= 360
        elif command.command_type is RobotCommandType.TURN_RADAR:
            robot.radar_angle += min(
                GameParameters.MAX_TURN_RADAR_ANGLE,
                max(-GameParameters.MAX_TURN_RADAR_ANGLE, command.parameter),
            )
            robot.radar_angle %= 360

    def update_robot_state(self, robot: Robot) -> None:
        # Update robot position
        robot.position.x += int(robot.velocity * cos(robot.tank_angle / 180 * pi))
        robot.position.y += int(robot.velocity * sin(robot.tank_angle / 180 * pi))
        if robot.position.clip(margin=robot.radius):
            robot.bumped_wall = True

        # Recharge weapon
        robot.weapon_energy += GameParameters.WEAPON_RECHARGE_RATE
        robot.weapon_energy = min(GameParameters.MAX_DAMAGE, robot.weapon_energy)

    def update_missile(self, missile: Missile) -> None:
        """Updates the state of a single missile"""
        if missile.exploding:
            missile.explode_progress += 1
        else:
            v = GameParameters.BULLET_VELOCITY
            missile.position.x += int(v * cos(missile.angle / 180 * pi))
            missile.position.y += int(v * sin(missile.angle / 180 * pi))
            missile.position.clip()

    def reset_flags(self):
        for robot in self.robots:
            if not robot.live():
                continue
            robot.got_hit = False
            if robot.radar_pinged:
                print(f"Clearing ping: {robot}")
            robot.radar_pinged = False
            robot.bumped_wall = False

    def update_radars(self) -> None:
        for robot in self.robots:
            if not robot.live():
                continue

            # Update radar pings
            for target in self.robots:
                if robot is target or not target.live():
                    continue

                base_angle = self._prior_radar_angle.get(robot.name, 0.0)
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

            # Save prior radar state for next calculation
            self._prior_radar_angle[robot.name] = robot.tank_angle + robot.turret_angle + robot.radar_angle

    def update_commands(self, commands: Dict[str, RobotCommand]) -> None:
        for robot in self.robots:
            if not robot.live():
                continue

            command = commands[robot.name]
            self.update_robot_command(robot, command)

    def update_arena(self) -> None:
        """Updates the state of the arena (all robots & missiles)"""

        # Update all robots
        for robot in self.robots:
            if not robot.live():
                robot.velocity = 0
                continue
            self.update_robot_state(robot)

        # Update all missiles
        for missile in self.missiles:
            self.update_missile(missile)
        self.missiles = [m for m in self.missiles if m.live()]

        # Missile - Robot collision detection
        for missile in self.missiles:
            for robot in self.robots:
                if not robot.live():
                    continue
                # print(abs(`robot.position - missile.position))
                if abs(robot.position - missile.position) < robot.radius:
                    if not missile.exploding:
                        print(f"{robot.name} was hit! Health={robot.health} Energy={missile.energy}")
                        robot.health -= missile.energy
                        missile.exploding = True
                        robot.got_hit = True
                        break
            if (
                missile.position.x <= 0
                or missile.position.x >= GameParameters.ARENA_WIDTH
                or missile.position.y <= 0
                or missile.position.y >= GameParameters.ARENA_HEIGHT
            ):
                # print(f"Missile hit edge: {missile.position}")
                missile.exploding = True

        # Update radar pings
        self.update_radars()

    def get_winner(self) -> Optional[Robot]:
        """Returns the winner or None if no winner yet"""
        remaining = [r for r in self.robots if r.live()]
        if len(remaining) == 1:
            return remaining[0]
        if len(remaining) == 0:
            # If all robots are dead, return the one that sustained the least damage
            return max(self.robots, key=lambda r: r.health)
        return None
