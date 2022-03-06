import json
import requests
import websocket  # type: ignore
from robots import Robot, RobotCommand
from typing import List, Protocol, Union

class Driver(Protocol):
    def get_next_command(self, r: Robot) -> Union[RobotCommand, List[RobotCommand], None]:
        ...

def play(robot_name: str, driver: Driver, url: str):
    print(f"Connecting to {url}")
    ws = websocket.WebSocket()
    try:
        ws.connect(url)
    except ConnectionRefusedError:
        print("Could not connect")
        return
    print("Connected")

    try:
        ws.send(json.dumps({"name": robot_name}))
        for msg in ws:
            if not msg:
                break
            data = json.loads(msg)
            if "echo" in data:
                print(data["echo"])
                continue
            robot_state = Robot.from_dict(data)
            if not robot_state.live():
                print(f"{robot_name} is no longer alive!")
                break
            command = driver.get_next_command(robot_state)
            if command is None:
                continue
            if not isinstance(command, list):
                command = [command]
            for cmd in command:
                if not isinstance(cmd, RobotCommand):
                    raise TypeError(f"Commands should be of type RobotCommand, not {type(cmd)}")
                ws.send(json.dumps(cmd.to_dict()))
    except websocket.WebSocketConnectionClosedException:
        pass
    finally:
        print("Connection closed")

def match():
    match_name = match_name
    requests.get(f"http://localhost:8000/match/{match_name}")