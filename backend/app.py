"""
app.py
FastAPI backend for the Kolkata / Greater Kolkata / Barasat bus tracker.

Run:
    pip install -r requirements.txt
    python seed_data.py      # creates + seeds bus_tracker.db (run once, or
                              # again whenever you edit seed_data.py)
    uvicorn app:app --reload --port 8000

Then open frontend/index.html in a browser (it calls http://localhost:8000).
"""

from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import get_conn, DB_PATH
from tracker import get_provider

app = FastAPI(title="Kolkata Bus Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

provider = get_provider()


@app.get("/api/health")
def health():
    return {"status": "ok", "db_exists": DB_PATH.exists()}


@app.get("/api/routes")
def list_routes():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT route_id, name, region, operator, trip_minutes FROM routes "
            "ORDER BY region, route_id"
        ).fetchall()
        return [dict(r) for r in rows]


@app.get("/api/routes/{route_id}/stops")
def route_stops(route_id: str):
    with get_conn() as conn:
        route = conn.execute(
            "SELECT * FROM routes WHERE route_id = ?", (route_id,)
        ).fetchone()
        if not route:
            raise HTTPException(404, f"Unknown route '{route_id}'")
        stops = conn.execute(
            "SELECT s.stop_id, s.name, s.area, s.lat, s.lon, rs.seq, rs.offset_minutes "
            "FROM route_stops rs JOIN stops s ON s.stop_id = rs.stop_id "
            "WHERE rs.route_id = ? ORDER BY rs.seq",
            (route_id,),
        ).fetchall()
        return {"route": dict(route), "stops": [dict(s) for s in stops]}


@app.get("/api/stops")
def list_stops():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM stops ORDER BY area, name").fetchall()
        return [dict(r) for r in rows]


@app.get("/api/stops/{stop_id}/arrivals")
def stop_arrivals(stop_id: int):
    """Next arrivals at a given stop, derived from the currently active trips."""
    now = datetime.now()
    active = provider.get_active_buses(now)
    arrivals = []
    for bus in active:
        for s in bus["upcoming_stops"]:
            if s["stop_id"] == stop_id:
                arrivals.append(
                    {
                        "route_id": bus["route_id"],
                        "route_name": bus["route_name"],
                        "direction": bus["direction"],
                        "eta_minutes": s["eta_minutes"],
                    }
                )
    arrivals.sort(key=lambda a: a["eta_minutes"])
    return arrivals


@app.get("/api/live")
def live_buses():
    """All currently-running buses with interpolated position + ETAs."""
    now = datetime.now()
    return {
        "server_time": now.strftime("%H:%M:%S"),
        "note": "Positions are estimated from the published schedule "
        "(no live GPS feed is connected) - see README.md.",
        "buses": provider.get_active_buses(now),
    }
