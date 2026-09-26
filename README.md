# Kolkata Bus Tracker

Tracks bus routes and timings across **Kolkata, Greater Kolkata (Salt Lake,
New Town, Dum Dum) and North 24 Parganas (Barasat, Madhyamgram,
Barrackpore)**.

## Important — read this first

There is currently no official public real-time API or open GTFS feed for
WBTC / private Kolkata buses (unlike, say, Bengaluru's BMTC). Google Maps
shows live WBTC arrivals inside its own app, but does not expose that data
for third-party use. So this project ships with:

- A **real, extensible schema** for routes, stops and trips.
- A **starter dataset** of genuine Kolkata bus route numbers and real stop
  locations (`backend/seed_data.py`) — but the exact stop order and
  departure times are illustrative samples, not an official timetable.
- A **schedule-interpolation engine** that estimates where each bus
  "should" be right now, based on the timetable — clearly labelled as an
  estimate, not GPS truth.
- A **clean plug point** (`LiveDataProvider` in `backend/tracker.py`) so
  you can drop in real data the moment you have it: a GPS vendor, an
  agency data-sharing agreement, or your own crowd-sourced tracker app.

Replace `seed_data.py` with authoritative timetables (WBTC, a transport app
export, or your own survey) to make this genuinely useful for commuting.

## Architecture

```
backend/
  database.py    SQLite schema (routes, stops, route_stops, trips)
  seed_data.py   Starter data + population script
  tracker.py     Live-position engine (pluggable data source)
  app.py         FastAPI REST API
frontend/
  index.html     Departure-board style dashboard + live Leaflet map
```

## Run it

```bash
cd backend
pip install -r requirements.txt
python seed_data.py          # creates and fills bus_tracker.db
uvicorn app:app --reload --port 8000
```

Then open `frontend/index.html` in a browser (it calls
`http://localhost:8000`). It polls `/api/live` every 5 seconds.

## API

| Endpoint                          | Returns                                   |
|------------------------------------|--------------------------------------------|
| `GET /api/routes`                  | All routes, grouped by region              |
| `GET /api/routes/{id}/stops`       | Ordered stops + scheduled offsets for a route |
| `GET /api/stops`                   | All stops with coordinates                 |
| `GET /api/stops/{id}/arrivals`     | Next arrivals at one stop, soonest first   |
| `GET /api/live`                    | All currently-running buses: position, next stop, ETA |

## Extending the coverage

To add a route or region (e.g. Baranagar, Rajpur-Sonarpur, Howrah–Shibpur):

1. Add any new stops to `STOPS` in `seed_data.py` with real coordinates.
2. Add a route to `ROUTES` with its ordered stop list and cumulative
   minute-offsets, plus first/last service time and headway.
3. Re-run `python seed_data.py` (this rebuilds the database).

## Plugging in real live data

Implement a new class in `tracker.py`:

```python
class MyGpsFeedProvider(LiveDataProvider):
    def get_active_buses(self, now):
        # call your real feed, return the same list-of-dict shape
        ...
```

Then change `get_provider()` to return it. Nothing in `app.py` or the
frontend needs to change — they only depend on the shared output shape.
