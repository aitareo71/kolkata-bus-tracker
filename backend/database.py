"""
database.py
SQLite schema + helper functions for the Kolkata Bus Tracker.

Tables:
    routes      - one row per bus route (e.g. "S9", "234", "DN9/1")
    stops       - one row per physical stop
    route_stops - ordered stops for a route, with scheduled offset (minutes
                  from the trip's first departure) and approx. distance
                  along the route (used to interpolate live position)
    trips       - individual scheduled departures ("first bus at 05:40")
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "bus_tracker.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS routes (
    route_id     TEXT PRIMARY KEY,      -- e.g. 'S9', '234', 'DN9/1'
    name         TEXT NOT NULL,         -- human readable, e.g. 'Barasat - Esplanade'
    region       TEXT NOT NULL,         -- 'Kolkata', 'Greater Kolkata', 'Barasat & North 24 Pgs' ...
    operator     TEXT NOT NULL,         -- 'WBTC', 'Private', 'CSTC' ...
    trip_minutes INTEGER NOT NULL       -- typical end-to-end journey time in minutes
);

CREATE TABLE IF NOT EXISTS stops (
    stop_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL UNIQUE,
    area      TEXT NOT NULL,            -- locality, e.g. 'Barasat', 'Salt Lake Sector V'
    lat       REAL NOT NULL,
    lon       REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS route_stops (
    route_id      TEXT NOT NULL REFERENCES routes(route_id),
    stop_id       INTEGER NOT NULL REFERENCES stops(stop_id),
    seq           INTEGER NOT NULL,     -- 0-based order along the route
    offset_minutes REAL NOT NULL,       -- scheduled minutes-from-start to reach this stop
    PRIMARY KEY (route_id, seq)
);

CREATE TABLE IF NOT EXISTS trips (
    trip_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id    TEXT NOT NULL REFERENCES routes(route_id),
    direction   TEXT NOT NULL,          -- 'UP' (start->end) or 'DOWN' (end->start)
    start_time  TEXT NOT NULL           -- 'HH:MM', 24h, first-stop departure
);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(reset: bool = False):
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
    with get_conn() as conn:
        conn.executescript(SCHEMA)


if __name__ == "__main__":
    init_db(reset=True)
    print(f"Initialised database at {DB_PATH}")
