import asyncio
from dataclasses import asdict
import json
from pathlib import Path
from typing import Callable, Dict
import aiohttp
from aiohttp import web
import aiohttp_jinja2
import jinja2

from robots import Arena, Robot, GameParameters, RobotCommand, RobotCommandType
from example_drivers import PongDriver, RadarDriver, StillDriver


TEMPLATE_PATH = Path(__file__).parent / "templates"
STATIC_PATH = Path(__file__).parent / "static"


Driver = Callable[[Robot], RobotCommand]


async def runner_task(a: Arena, drivers: Dict[str, Driver], event: asyncio.Event) -> None:
    print(f"Starting battle with: {', '.join(r.name for r in a.robots)}")
    standing_orders = {r.name: RobotCommand(RobotCommandType.IDLE, 0) for r in a.robots}
    while not a.get_winner() and a.remaining > 0:
        a.remaining -= 1
        if a.remaining % GameParameters.COMMAND_RATE == 0:
            # Get new commands for each robot
            standing_orders = {r.name: drivers[r.name](r) for r in a.robots}
            # Process the commands
            a.update_commands(standing_orders)
            # Retain all commands from the driver as standing orders, except for FIRE which only occurs once
            a.reset_flags()
            for command in standing_orders.values():
                if command.command_type is RobotCommandType.FIRE:
                    command.command_type = RobotCommandType.IDLE
        else:
            a.update_commands(standing_orders)
        a.update_arena()
        event.set()
        event.clear()
        await asyncio.sleep(1 / GameParameters.FPS)
    winner = a.get_winner()
    if not winner:
        winner = max(a.robots, key=lambda r: r.health)
    a.winner = winner.name
    event.set()
    event.clear()
    print(f"{winner.name} is the winner!")


async def server_task(arena: Arena, event: asyncio.Event) -> None:
    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(TEMPLATE_PATH))

    app["arena"] = arena
    app["event"] = event
    app.router.add_get("/", index_handler)
    app.router.add_get("/api/watch", watch_handler)
    app.router.add_static("/", STATIC_PATH, name="static", append_version=True)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    try:
        await asyncio.Future()
    finally:
        await runner.cleanup()


class JSONEncoder(json.JSONEncoder):
    """Minimizes JSON string length by reducing resolution of floats, convert bool to int, and transpose"""

    def encode(self, a) -> str:
        if isinstance(a, bool):
            return super().encode(1 if a else 0)
        if isinstance(a, float):
            return f"{round(a,1):g}"
        if isinstance(a, dict):
            items = (f'"{k}"{self.key_separator}{self.encode(v)}' for k, v in a.items())
            return f"{{{self.item_separator.join(items)}}}"
        if isinstance(a, (list, tuple)):
            if len(a) and isinstance(a[0], dict):
                transposed = {k: [e[k] for e in a] for k in a[0].keys()}
                transposed["_t"] = True
                return self.encode(transposed)
            return f"[{self.item_separator.join(self.encode(x) for x in a)}]"
        return super().encode(a)


def arena_state_as_json(arena: Arena):
    d = asdict(arena)
    return d


@aiohttp_jinja2.template("index.html.j2")
async def index_handler(request):
    return {}


async def watch_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async def send_updates():
        try:
            while True:
                try:
                    await asyncio.wait_for(request.app["event"].wait(), 1.0)
                except asyncio.TimeoutError:
                    pass
                payload = arena_state_as_json(request.app["arena"])
                msg = json.dumps(payload, separators=(",", ":"), cls=JSONEncoder)
                # print(msg)
                await ws.send_str(msg)
        except Exception as e:
            print(f"Exception: {e!r}")
        finally:
            print("Exiting sender")

    send_task = asyncio.create_task(send_updates())
    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.ERROR:
                print("ws connection closed with exception %s" % ws.exception())
    finally:
        send_task.cancel()

    print("websocket connection closed")

    return ws


async def amain():
    arena = Arena()
    event = asyncio.Event()
    server = asyncio.create_task(server_task(arena, event))
    while True:
        arena.remaining = 6000
        arena.winner = None
        drivers = {
            "radarbot": RadarDriver().get_next_command,
            "pongbot": PongDriver().get_next_command,
            "stillbot": StillDriver().get_next_command,
        }
        arena.robots = [Robot(k) for k in drivers]
        await runner_task(arena, drivers, event)
        await asyncio.sleep(10)
    await server


if __name__ == "__main__":
    asyncio.run(amain())
