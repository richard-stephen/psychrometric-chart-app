# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
pip install -r requirements.txt
python main.py
```

App runs at `http://localhost:8000`. For production (Render), the start command is:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Python version: **3.11.11**. No test suite exists in this project.

## Architecture

This is a single-page application with a FastAPI backend and a vanilla JS/HTML/CSS frontend. There is no build step.

**Backend (`main.py`)** — FastAPI app that:
- Generates full Plotly psychrometric chart figures server-side on every request
- Returns complete Plotly JSON via REST API; the frontend renders it with `Plotly.newPlot()`
- Serves static files (`/static/`) with cache-busting headers via `CustomStaticFiles`

**Helper module (`simple_enthalpy.py`)** — All psychrometric calculations live here using `psychrolib` (SI units). Both `calc_humidity_ratio` and `calc_enthalpy` are imported into `main.py`.

**Static data (CSV files)** — Loaded once at startup into module-level constants:
- `dewpoint_data.csv` — HR and dew point pairs used to draw horizontal humidity ratio lines
- `enthalpy_intersections.csv` — Enthalpy line endpoints at the saturation curve

**Frontend (`static/`)** — Plain HTML/CSS/JS with two modules:
- `ChartModule` — fetch wrappers for each API endpoint
- `UIModule` — event listeners and DOM wiring; initialized on `DOMContentLoaded`

Plotly 3.0.1 is loaded from CDN in `index.html`.

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/default-chart?showDesignZone=bool` | Base chart, no data points |
| POST | `/api/generate-chart` | Base chart + points from uploaded `.xlsx` |
| POST | `/api/plot-point` | Base chart + single manually entered point |
| POST | `/api/clear-data` | Returns base chart (effectively same as default-chart) |

All endpoints return `{"status": "success", "figure": "<plotly json string>"}`.

The `.xlsx` upload expects columns named exactly `Temperature` (°C) and `Humidity` (%).

## Code Style

- **JavaScript**: Always use `function` keyword syntax (not arrow functions). Keep it simple — no frameworks, no bundlers.
- **Python**: Keep logic straightforward; avoid over-engineering.
- Chart axis ranges: X (dry-bulb temp) `-10` to `50`°C, Y (humidity ratio) `0` to `30` g/kg.
- CORS is restricted to `https://psychrochart.onrender.com` and `http://localhost:8000`.
