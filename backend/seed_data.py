"""
seed_data.py
Starter dataset: stops + routes across Kolkata, Greater Kolkata (Salt Lake,
New Town, Dum Dum) and North 24 Parganas (Barasat, Madhyamgram, Barrackpore).

IMPORTANT: There is no official public real-time API or open GTFS feed for
West Bengal Transport Corporation (WBTC) / private buses at the time this
was written. The route numbers below are real, commonly used Kolkata bus
routes, and stop coordinates are approximate real locations - but the exact
stop sequences and departure times are ILLUSTRATIVE SAMPLE DATA, not an
official timetable. Replace/extend this file with authoritative data (a
transport department release, your own field survey, or a licensed feed)
before relying on it for real commuting decisions. See README.md for how
to plug in a genuine live-position feed if/when one becomes available.
"""

from database import get_conn, init_db

# ---------------------------------------------------------------- stops --
# name -> (area, lat, lon)
STOPS = {
    "Barasat":                  ("Barasat",             22.7239, 88.4813),
    "Madhyamgram":              ("Madhyamgram",         22.6942, 88.4508),
    "Baguiati":                 ("Baguiati",            22.6259, 88.4290),
    "Dum Dum":                  ("Dum Dum",             22.6178, 88.4197),
    "Airport (NSCBI)":          ("Airport",             22.6547, 88.4467),
    "Barrackpore":              ("Barrackpore",         22.7606, 88.3639),
    "Ultadanga":                ("Ultadanga",           22.5980, 88.3921),
    "Salt Lake Karunamoyee":    ("Salt Lake",           22.5817, 88.4171),
    "Salt Lake Sector V":       ("Salt Lake",           22.5761, 88.4315),
    "New Town (Akankha)":       ("New Town",            22.5859, 88.4732),
    "Rajarhat Gate":            ("Rajarhat",            22.6152, 88.4536),
    "Shyambazar":               ("North Kolkata",       22.6013, 88.3745),
    "Sealdah":                  ("Central Kolkata",     22.5697, 88.3697),
    "BBD Bagh":                 ("Central Kolkata",     22.5697, 88.3494),
    "Esplanade":                ("Central Kolkata",     22.5626, 88.3529),
    "Park Street":              ("Central Kolkata",     22.5535, 88.3565),
    "Howrah Station":           ("Howrah",              22.5839, 88.3425),
    "Gariahat":                 ("South Kolkata",       22.5186, 88.3654),
    "Jadavpur":                 ("South Kolkata",       22.4990, 88.3714),
    "Garia":                    ("South Kolkata",       22.4614, 88.3931),
    "Behala Chowrasta":         ("Behala",              22.4989, 88.3129),
}

# route_id -> dict(name, region, operator, trip_minutes, stop_sequence, headway_min, first, last)
# stop_sequence offsets are minutes-from-start (monotonically increasing).
ROUTES = {
    "234": {
        "name": "Barasat - Howrah Station",
        "region": "Barasat & North 24 Parganas",
        "operator": "Private (route-permit)",
        "stops": [
            ("Barasat", 0), ("Madhyamgram", 12), ("Baguiati", 20),
            ("Ultadanga", 32), ("Sealdah", 42), ("BBD Bagh", 50),
            ("Howrah Station", 58),
        ],
        "headway_min": 15, "first": "05:30", "last": "21:30",
    },
    "DN9/1": {
        "name": "Dum Dum - Barasat",
        "region": "Greater Kolkata / Barasat",
        "operator": "Private (route-permit)",
        "stops": [
            ("Dum Dum", 0), ("Baguiati", 10), ("Madhyamgram", 18),
            ("Barasat", 28),
        ],
        "headway_min": 12, "first": "05:45", "last": "22:00",
    },
    "S9": {
        "name": "Karunamoyee (Salt Lake) - Howrah Station",
        "region": "Greater Kolkata (Salt Lake)",
        "operator": "WBTC",
        "stops": [
            ("Salt Lake Karunamoyee", 0), ("Ultadanga", 10),
            ("Shyambazar", 18), ("BBD Bagh", 28), ("Howrah Station", 36),
        ],
        "headway_min": 18, "first": "06:00", "last": "21:00",
    },
    "S12": {
        "name": "New Town - Howrah Station",
        "region": "Greater Kolkata (New Town / Salt Lake)",
        "operator": "WBTC",
        "stops": [
            ("New Town (Akankha)", 0), ("Rajarhat Gate", 8),
            ("Salt Lake Sector V", 16), ("Ultadanga", 28),
            ("Sealdah", 38), ("BBD Bagh", 46), ("Howrah Station", 54),
        ],
        "headway_min": 20, "first": "06:00", "last": "21:30",
    },
    "215": {
        "name": "Garia - Howrah Station",
        "region": "Kolkata (South)",
        "operator": "Private (route-permit)",
        "stops": [
            ("Garia", 0), ("Jadavpur", 12), ("Gariahat", 20),
            ("Park Street", 32), ("Esplanade", 38), ("BBD Bagh", 44),
            ("Howrah Station", 52),
        ],
        "headway_min": 14, "first": "05:30", "last": "22:15",
    },
    "AC-8": {
        "name": "Behala Chowrasta - Airport (NSCBI)",
        "region": "Kolkata / Airport",
        "operator": "WBTC (AC)",
        "stops": [
            ("Behala Chowrasta", 0), ("Park Street", 22), ("Esplanade", 28),
            ("Ultadanga", 40), ("Dum Dum", 50), ("Airport (NSCBI)", 62),
        ],
        "headway_min": 30, "first": "06:30", "last": "20:30",
    },
    "VS-1": {
        "name": "Barrackpore - Esplanade",
        "region": "Greater Kolkata (North)",
        "operator": "Private (route-permit)",
        "stops": [
            ("Barrackpore", 0), ("Dum Dum", 20), ("Shyambazar", 32),
            ("BBD Bagh", 42), ("Esplanade", 46),
        ],
        "headway_min": 16, "first": "05:30", "last": "21:45",
    },
}


def _minutes(hhmm: str) -> int:
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def seed():
    init_db(reset=True)
    with get_conn() as conn:
        for name, (area, lat, lon) in STOPS.items():
            conn.execute(
                "INSERT OR IGNORE INTO stops (name, area, lat, lon) VALUES (?,?,?,?)",
                (name, area, lat, lon),
            )

        for route_id, r in ROUTES.items():
            trip_minutes = r["stops"][-1][1]
            conn.execute(
                "INSERT INTO routes (route_id, name, region, operator, trip_minutes) "
                "VALUES (?,?,?,?,?)",
                (route_id, r["name"], r["region"], r["operator"], trip_minutes),
            )
            for seq, (stop_name, offset) in enumerate(r["stops"]):
                stop_id = conn.execute(
                    "SELECT stop_id FROM stops WHERE name = ?", (stop_name,)
                ).fetchone()["stop_id"]
                conn.execute(
                    "INSERT INTO route_stops (route_id, stop_id, seq, offset_minutes) "
                    "VALUES (?,?,?,?)",
                    (route_id, stop_id, seq, offset),
                )

            # Generate trips at a fixed headway, both directions, for the service window
            start = _minutes(r["first"])
            end = _minutes(r["last"])
            headway = r["headway_min"]
            t = start
            direction = "UP"
            while t <= end:
                hh, mm = divmod(t, 60)
                conn.execute(
                    "INSERT INTO trips (route_id, direction, start_time) VALUES (?,?,?)",
                    (route_id, direction, f"{hh:02d}:{mm:02d}"),
                )
                direction = "DOWN" if direction == "UP" else "UP"
                t += headway

    print("Seeded database with", len(STOPS), "stops and", len(ROUTES), "routes.")


if __name__ == "__main__":
    seed()
