"""
tracker.py

Two pieces:

1. LiveDataProvider - an abstract interface. `ScheduleInterpolationProvider`
   below is the default implementation: since no public real-time feed
   exists for Kolkata buses, it estimates "live" position/ETA by
   interpolating each scheduled trip's progress against the clock. This is
   an approximation, not GPS truth - treat it as a placeholder.

2. If you get access to a real feed (a GPS vendor, a driver-side app, an
   agency partnership, etc.), implement a new class with the same
   `get_active_buses()` signature and swap it in `app.py`. Nothing else
   needs to change.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from database import get_conn


class LiveDataProvider(ABC):
    @abstractmethod
    def get_active_buses(self, now: datetime) -> list[dict]:
        """Return currently-running buses with position + per-stop ETA."""
        raise NotImplementedError


class ScheduleInterpolationProvider(LiveDataProvider):
    """Estimates live positions from the static schedule. No real GPS."""

    def get_active_buses(self, now: datetime) -> list[dict]:
        clock_min = now.hour * 60 + now.minute + now.second / 60
        active = []

        with get_conn() as conn:
            trips = conn.execute(
                "SELECT trip_id, route_id, direction, start_time FROM trips"
            ).fetchall()

            routes = {r["route_id"]: r for r in conn.execute("SELECT * FROM routes")}

            stops_by_route: dict[str, list[dict]] = {}
            for row in conn.execute(
                "SELECT rs.route_id, rs.seq, rs.offset_minutes, "
                "s.stop_id, s.name, s.area, s.lat, s.lon "
                "FROM route_stops rs JOIN stops s ON s.stop_id = rs.stop_id "
                "ORDER BY rs.route_id, rs.seq"
            ):
                stops_by_route.setdefault(row["route_id"], []).append(dict(row))

            for trip in trips:
                route_id = trip["route_id"]
                stops = stops_by_route.get(route_id, [])
                if len(stops) < 2:
                    continue
                trip_minutes = routes[route_id]["trip_minutes"]

                h, m = map(int, trip["start_time"].split(":"))
                start_min = h * 60 + m
                elapsed = clock_min - start_min

                # Only show buses currently mid-trip (ignore yesterday/tomorrow)
                if elapsed < 0 or elapsed > trip_minutes:
                    continue

                ordered = stops if trip["direction"] == "UP" else list(reversed(stops))
                if trip["direction"] == "DOWN":
                    # Recompute offsets counting down from the end of the route
                    ordered = [
                        {**s, "offset_minutes": trip_minutes - s["offset_minutes"]}
                        for s in ordered
                    ]

                # find current segment
                seg = None
                for i in range(len(ordered) - 1):
                    a, b = ordered[i], ordered[i + 1]
                    if a["offset_minutes"] <= elapsed <= b["offset_minutes"]:
                        seg = (a, b)
                        break
                if seg is None:
                    continue
                a, b = seg
                span = max(b["offset_minutes"] - a["offset_minutes"], 0.01)
                frac = (elapsed - a["offset_minutes"]) / span
                lat = a["lat"] + (b["lat"] - a["lat"]) * frac
                lon = a["lon"] + (b["lon"] - a["lon"]) * frac

                upcoming = [
                    {
                        "stop_id": s["stop_id"],
                        "name": s["name"],
                        "area": s["area"],
                        "eta_minutes": round(s["offset_minutes"] - elapsed, 1),
                    }
                    for s in ordered
                    if s["offset_minutes"] >= elapsed
                ]

                active.append(
                    {
                        "trip_id": trip["trip_id"],
                        "route_id": route_id,
                        "route_name": routes[route_id]["name"],
                        "region": routes[route_id]["region"],
                        "operator": routes[route_id]["operator"],
                        "direction": trip["direction"],
                        "lat": round(lat, 6),
                        "lon": round(lon, 6),
                        "next_stop": upcoming[0]["name"] if upcoming else None,
                        "next_stop_eta_min": upcoming[0]["eta_minutes"] if upcoming else None,
                        "upcoming_stops": upcoming[:6],
                    }
                )

        return active


def get_provider() -> LiveDataProvider:
    """Single place to swap in a real live-data provider later."""
    return ScheduleInterpolationProvider()
