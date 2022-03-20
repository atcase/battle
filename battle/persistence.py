from datetime import datetime
from sqlite3 import PARSE_DECLTYPES, Connection, register_adapter


def create_connection() -> Connection:
    register_adapter(datetime, datetime.isoformat)
    c = Connection("battle.db", detect_types=PARSE_DECLTYPES)
    with c:
        c.execute(
            """
            create table if not exists match (
                match_id integer primary key,
                arena_id integer,
                end_time datetime,
                winner text
            )
        """
        )
        c.execute(
            """
            create table if not exists match_stat (
                stat_id integer primary key,
                match_id integer not null references match,
                robot_name text not null,
                command text not null,
                total integer not null
            )
        """
        )
    return c


def store_match(c: Connection, arena_id: int, end_time: datetime, winner: str) -> int:
    with c:
        c.execute("insert into match (arena_id, end_time, winner) values (?, ?, ?)", (arena_id, end_time, winner))
        (match_id,) = c.execute("select last_insert_rowid()").fetchone()
    return match_id


def store_match_cmd_stat(c: Connection, match_id: int, robot_name: str, command: str, total: int):
    with c:
        c.execute(
            "insert into match_stat (match_id, robot_name, command, total) values (?, ?, ?, ?)",
            (match_id, robot_name, command, total),
        )


def get_leaderboard(c: Connection, arena_id: int):
    return c.execute(
        "select winner, count(*) as wins from match where arena_id = ? group by 1 order by 2 desc limit 10", (arena_id,)
    ).fetchall()
