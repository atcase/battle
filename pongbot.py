from dataclasses import dataclass
from robots import RobotCommand, RobotCommandType, Robot
from player import play

@dataclass
class PongDriver:
    """Starts moving and then maintains the same speed, bouncing off the walls. Fires if radar pings."""

    def get_next_command(self, r: Robot) -> RobotCommand:
        if r.cmd_q_len > 0:
            return None
        if r.bumped_wall or r.got_hit:
            return [
                RobotCommand(RobotCommandType.TURN_HULL, -45),
                RobotCommand(RobotCommandType.TURN_TURRET, 45),
                RobotCommand(RobotCommandType.ACCELERATE, 0),
                RobotCommand(RobotCommandType.ACCELERATE, 0),
                RobotCommand(RobotCommandType.ACCELERATE, 0),
            ]
        elif abs((r.velocity_angle - r.hull_angle + 180) % 360 - 180) > 1 or r.velocity == 0:
            return [
                RobotCommand(RobotCommandType.ACCELERATE, 0),
                RobotCommand(RobotCommandType.ACCELERATE, 0),
                RobotCommand(RobotCommandType.ACCELERATE, 0),
                RobotCommand(RobotCommandType.ACCELERATE, 0),
            ]

        if r.radar_ping is not None:
            return RobotCommand(RobotCommandType.FIRE, 100)
        return RobotCommand(RobotCommandType.TURN_TURRET, 2)


if __name__ == "__main__":
    URL = "ws://localhost:8000/api/play/0"
    driver = PongDriver()
    play("pongbot", driver, URL)
