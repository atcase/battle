import argparse
import json
from urllib.parse import urljoin, urlsplit
import webbrowser
import requests
import websocket  # type: ignore
from robots import Robot, RobotCommand
from typing import List, Protocol, Union


class Driver(Protocol):
    def get_next_command(self, r: Robot) -> Union[RobotCommand, List[RobotCommand], None]:
        ...


def play(robot_name: str, driver: Driver, url: str):
    print(f"Connecting to game API server... ", end=None)
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


def main(robot_name: str, driver: Driver):
    argparser = argparse.ArgumentParser()
    argparser.add_argument("name", nargs="?", default=robot_name, help="The name of the player.")
    argparser.add_argument("--game-id", default=0, help="The game ID to play - default is 0")
    argparser.add_argument("--url", default="ws://localhost:8000", help="The game server base URL.")
    argparser.add_argument("--browser", action="store_true", help="Open a browser window to watch the game")

    args = argparser.parse_args()
    url = urljoin(args.url, f"/api/play/{args.game_id}")
    us = urlsplit(args.url)
    watch_url = f"{us.scheme.replace('ws', 'http')}://{us.netloc}/game/{args.game_id}"
    print(f"Watch this game at: {watch_url}")
    if args.browser:
        webbrowser.open(watch_url)
    play(args.name, driver, url)
