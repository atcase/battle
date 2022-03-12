from dataclasses import dataclass, field, replace
from math import atan2, cos, pi, sin, sqrt
from random import random
from typing import Dict, List, Optional

from battle.robots import GameParameters, Missile, Robot, RobotCommand, RobotCommandType


@dataclass
class Arena:
    """The battle arena"""

    robots: List[Robot] = field(default_factory=list)
    missiles: List[Missile] = field(default_factory=list)
    winner: Optional[str] = None
    remaining: int = 6000

    def __post_init__(self):
        self._prior_radar_angle: Dict[str, float] = {}

    def update_robot_command(self, robot: Robot, command: RobotCommand) -> None:
        """Updates the state of the arena and a single robot based on a command"""
        # print(f"{robot.name} chose to {command.command_type.name}({command.parameter})")
        if command.command_type is RobotCommandType.ACCELERATE:
            vx = robot.velocity * cos(robot.velocity_angle / 180 * pi)
            vy = robot.velocity * sin(robot.velocity_angle / 180 * pi)
            dx = GameParameters.MOTOR_POWER / GameParameters.COMMAND_RATE * cos(robot.hull_angle / 180 * pi)
            dy = GameParameters.MOTOR_POWER / GameParameters.COMMAND_RATE * sin(robot.hull_angle / 180 * pi)
            robot.velocity = sqrt((vx + dx) ** 2 + (vy + dy) ** 2)
            robot.velocity_angle = atan2(vy + dy, vx + dx) / pi * 180
            robot.velocity = min(GameParameters.MAX_VELOCITY, robot.velocity)
            if robot.accelerate_progress is None:
                robot.accelerate_progress = 0
        elif command.command_type is RobotCommandType.FIRE:
            # Add a bit of randomness to the weapon energy for entertainment
            # This will also help with tie breakers
            energy_noise = (random() * 2 - 1) * GameParameters.WEAPON_RECHARGE_RATE
            requested_energy = min(GameParameters.MAX_DAMAGE, max(0, command.parameter))
            energy = min(robot.weapon_energy, requested_energy) + energy_noise
            energy = max(0, energy)
            angle = (robot.hull_angle + robot.turret_angle) % 360
            robot.weapon_energy = max(0, robot.weapon_energy - energy)
            start_position = replace(robot.position)
            start_position.x += 1.01 * robot.radius * cos(angle / 180 * pi)
            start_position.y += 1.01 * robot.radius * sin(angle / 180 * pi)
            m = Missile(start_position, angle, energy)
            self.missiles.append(m)
            if robot.firing_progress is None:
                robot.firing_progress = 0
        elif command.command_type is RobotCommandType.TURN_HULL:
            robot.hull_angle += min(
                GameParameters.MAX_TURN_ANGLE,
                max(-GameParameters.MAX_TURN_ANGLE, command.parameter / GameParameters.COMMAND_RATE),
            )
            robot.hull_angle %= 360
            if robot.accelerate_progress is None:
                robot.accelerate_progress = 0
        elif command.command_type is RobotCommandType.TURN_TURRET:
            robot.turret_angle += command.parameter / GameParameters.COMMAND_RATE
            robot.turret_angle %= 360
        elif command.command_type is RobotCommandType.TURN_RADAR:
            robot.radar_angle += min(
                GameParameters.MAX_TURN_RADAR_ANGLE,
                max(-GameParameters.MAX_TURN_RADAR_ANGLE, command.parameter / GameParameters.COMMAND_RATE),
            )
            robot.radar_angle %= 360

    def update_robot_state(self, robot: Robot) -> None:
        # Update robot position
        robot.position.x += (robot.velocity / GameParameters.COMMAND_RATE) * cos(robot.velocity_angle / 180 * pi)
        robot.position.y += (robot.velocity / GameParameters.COMMAND_RATE) * sin(robot.velocity_angle / 180 * pi)
        if robot.position.clip(margin=robot.radius):
            robot.bumped_wall = True

        # Recharge weapon
        robot.weapon_energy += GameParameters.WEAPON_RECHARGE_RATE / GameParameters.COMMAND_RATE
        robot.weapon_energy = min(GameParameters.MAX_DAMAGE, robot.weapon_energy)

        # Manage turret firing progress for animations
        if robot.firing_progress is not None:
            robot.firing_progress += 1
            if robot.firing_progress >= GameParameters.FIRING_FRAMES:
                robot.firing_progress = None

        # Manage exhaust progress for animations
        if robot.accelerate_progress is not None:
            robot.accelerate_progress += 1
            if robot.accelerate_progress >= GameParameters.EXHAUST_FRAMES:
                robot.accelerate_progress = None

    def update_missile(self, missile: Missile) -> None:
        """Updates the state of a single missile"""
        if missile.exploding:
            missile.explode_progress += 1
        else:
            v = GameParameters.BULLET_VELOCITY / GameParameters.COMMAND_RATE
            missile.position.x += v * cos(missile.angle / 180 * pi)
            missile.position.y += v * sin(missile.angle / 180 * pi)
            missile.position.clip()

    def reset_flags(self):
        for robot in self.robots:
            if not robot.live():
                continue
            robot.got_hit = False
            robot.radar_ping = None
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
                    robot.hull_angle + robot.turret_angle + robot.radar_angle - base_angle + 180.0
                ) % 360.0 - 180.0
                if (
                    now_angle > 0
                    and target_angle > 0
                    and now_angle > target_angle
                    or now_angle < 0
                    and target_angle < 0
                    and now_angle < target_angle
                ):
                    robot.radar_ping = abs(target.position - robot.position)
                    break

            # Save prior radar state for next calculation
            self._prior_radar_angle[robot.name] = robot.hull_angle + robot.turret_angle + robot.radar_angle

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

        # Missile - Robot collision detection
        for missile in self.missiles:
            for robot in self.robots:
                if not robot.live():
                    continue
                # print(abs(`robot.position - missile.position))
                if abs(robot.position - missile.position) < robot.radius:
                    if not missile.exploding:
                        robot.health -= missile.energy
                        print(f"{robot.name} was hit! Health={robot.health:.2f} Energy={missile.energy:.2f}")
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
                missile.explode_progress = GameParameters.EXPLODE_FRAMES

        self.missiles = [m for m in self.missiles if m.live()]

        # Update radar pings
        self.update_radars()

    def get_winner(self) -> Optional[Robot]:
        """Returns the winner or None if no winner yet"""
        if len(self.robots) <= 1:
            return None
        remaining = [r for r in self.robots if r.live()]
        if len(remaining) == 1:
            return remaining[0]
        if len(remaining) == 0:
            # If all robots are dead, return the one that sustained the least damage
            return max(self.robots, key=lambda r: r.health)
        return None

    def get_robot(self, robot_name: str) -> Robot:
        for r in self.robots:
            if r.name == robot_name:
                return r
        raise KeyError(robot_name)
