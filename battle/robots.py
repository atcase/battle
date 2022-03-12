from dataclasses import dataclass, field
from enum import Enum, auto
from math import atan2, pi, sqrt
from random import random
from typing import Any, Dict, Optional


class GameParameters:
    MAX_VELOCITY = 3
    MAX_TURN_ANGLE = 15
    MAX_TURN_RADAR_ANGLE = 180
    MOTOR_POWER = 1
    BULLET_VELOCITY = 15
    FPS = 20
    COMMAND_RATE = 5
    MAX_DAMAGE = 5
    WEAPON_RECHARGE_RATE = 0.1
    ARENA_WIDTH = 1000
    ARENA_HEIGHT = 1000
    EXPLODE_FRAMES = 6
    FIRING_FRAMES = 6
    EXHAUST_FRAMES = 6


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
        return cls(
            x=random() * GameParameters.ARENA_WIDTH,
            y=random() * GameParameters.ARENA_HEIGHT,
        )

    def clip(self, margin: float = 0.0) -> bool:
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
    velocity_angle: float = 0
    hull_angle: float = field(default_factory=random_angle)
    turret_angle: float = 0
    radar_angle: float = 0
    health: float = 100.0
    weapon_energy: float = 5.0
    radius: int = 20
    radar_ping: Optional[float] = None
    got_hit: bool = False
    bumped_wall: bool = False
    firing_progress: Optional[int] = None
    accelerate_progress: Optional[int] = None
    cmd_q_len: Optional[int] = None

    def live(self) -> bool:
        """Returns whether robot is still alive"""
        return self.health > 0

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Robot":
        return cls(position=Position(**d.pop("position")), **d)


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
    FIRE = auto()
    TURN_HULL = auto()
    TURN_TURRET = auto()
    TURN_RADAR = auto()
    IDLE = auto()


@dataclass
class RobotCommand:
    command_type: RobotCommandType
    parameter: float

    def to_dict(self) -> Dict[str, Any]:
        return {"command_type": self.command_type.value, "parameter": self.parameter}
