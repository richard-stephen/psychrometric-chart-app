from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import io
import copy
from simple_enthalpy import calc_humidity_ratio, calc_enthalpy, ATMOSPHERIC_PRESSURE_PA, GRAMS_PER_KG

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://psychrochart.onrender.com", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom StaticFiles to prevent caching
class CustomStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


app.mount("/static", CustomStaticFiles(directory="static", html=True), name="static")

# Constants
COLOR_PRIMARY    = 'rgba(38,70,83,1)'
COLOR_PRIMARY_80 = 'rgba(38,70,83,0.8)'
COLOR_PRIMARY_50 = 'rgba(38,70,83,0.5)'

T_DB_MIN, T_DB_MAX = -10, 50
W_MIN, W_MAX = 0, 30
t_axis = range(-10, 46, 5)

# Load static data once at startup
DEWPOINT_DATA = pd.read_csv('dewpoint_data.csv').to_dict('records')
ENTHALPY_DATA = pd.read_csv('enthalpy_intersections.csv').to_dict('records')

# Pre-computed chart data (computed once at startup)
T_DB_RANGE    = np.linspace(T_DB_MIN, T_DB_MAX, 100)
W_SAT_LIST    = [calc_humidity_ratio(t, 100.0) for t in T_DB_RANGE]
_SAT_AT_T     = {t: calc_humidity_ratio(t, 100.0) for t in t_axis}
_T_comfort    = np.array([20, 24])
W_COMFORT_LOW  = [calc_humidity_ratio(t, 40) for t in _T_comfort]
W_COMFORT_HIGH = [calc_humidity_ratio(t, 60) for t in _T_comfort]


# --- Helper Functions ---

def generate_base_chart(show_design_zone: bool = False):
    """Generates the base psychrometric chart figure with enthalpy lines."""
    fig = go.Figure()

    # Saturation Line (100% RH)
    fig.add_trace(go.Scatter(
        x=T_DB_RANGE, y=W_SAT_LIST, mode='lines', showlegend=False,
        line=dict(color=COLOR_PRIMARY_80, width=2), hoverinfo='skip'
    ))

    # Vertical dry-bulb temperature lines
    for t in t_axis:
        fig.add_trace(go.Scatter(
            x=[t, t], y=[0, _SAT_AT_T[t]], mode='lines',
            line=dict(color=COLOR_PRIMARY_50, width=1), opacity=0.3, hoverinfo='skip', showlegend=False
        ))

    # Horizontal humidity ratio lines (from dew point to T_DB_MAX)
    for data in DEWPOINT_DATA:
        hr = data['HR']
        dewpoint = data['Dew point']
        fig.add_trace(go.Scatter(
            x=[dewpoint, T_DB_MAX], y=[hr, hr], mode='lines',
            line=dict(color=COLOR_PRIMARY_50, width=1), opacity=0.3, hoverinfo='skip', showlegend=False
        ))

    # Relative Humidity Lines
    RH_levels = [10, 20, 30, 40, 50, 60, 70, 80, 90]
    for rh in RH_levels:
        W_rh_list = [calc_humidity_ratio(t, float(rh)) for t in T_DB_RANGE]
        fig.add_trace(go.Scatter(
            x=T_DB_RANGE, y=W_rh_list, mode='lines',
            line=dict(color=COLOR_PRIMARY_50, width=1, dash='dash'), opacity=1.0, hoverinfo='skip', showlegend=False
        ))
        index_position = int(len(T_DB_RANGE) * 0.75)
        fig.add_annotation(
            x=T_DB_RANGE[index_position], y=W_rh_list[index_position],
            text=f'{rh}%', showarrow=False,
            font=dict(size=10, color=COLOR_PRIMARY),
            xanchor='center', yanchor='middle'
        )

    # Enthalpy lines
    for data in ENTHALPY_DATA:
        h = data["Enthalpy"]
        T_intersect = data["Temperature"]
        W_intersect = data["Humidity Ratio"]

        T_start = h / 1.006
        T_points = np.linspace(T_intersect, T_start, 50)
        W_points = [((h - 1.006 * T) * 1000) / (2501 + 1.86 * T) for T in T_points]

        fig.add_trace(go.Scatter(
            x=T_points, y=W_points, mode='lines',
            line=dict(color=COLOR_PRIMARY, width=1, dash='dot'),
            hoverinfo='skip', showlegend=False,
        ))
        fig.add_annotation(
            x=T_intersect, y=W_intersect,
            text=f"{int(h)}", showarrow=False,
            font=dict(size=9, color='purple'),
            xanchor='left', yanchor='middle'
        )

    # "Enthalpy kJ/kg" label — added once, outside the loop
    fig.add_annotation(
        x=10, y=15,
        text='Enthalpy kJ/kg', showarrow=False,
        font=dict(family='Arial, sans-serif', size=18, color=COLOR_PRIMARY),
        xanchor='left', yanchor='middle'
    )

    # Comfort Zone (Optional)
    if show_design_zone:
        fig.add_trace(go.Scatter(
            x=[20, 24, 24, 20, 20],
            y=[W_COMFORT_LOW[0], W_COMFORT_LOW[1], W_COMFORT_HIGH[1], W_COMFORT_HIGH[0], W_COMFORT_LOW[0]],
            mode='lines', name='Comfort Zone', line=dict(color='green', dash='dash', width=2),
            fill='toself', fillcolor='rgba(0,255,0,0.1)',
            hovertemplate='Comfort Zone<extra></extra>'
        ))

    # Update Layout
    fig.update_layout(
        template='plotly_white',
        plot_bgcolor='white', paper_bgcolor='white',
        title=dict(
            text='<b>Psychrometric Chart</b>',
            font=dict(family='"Segoe UI", sans-serif', size=28, color='#111111')
        ), title_x=0.5,
        xaxis=dict(
            title='Dry-Bulb Temperature (°C)', range=[T_DB_MIN, T_DB_MAX],
            showline=True, linewidth=1, linecolor='black', mirror=True, dtick=5,
            showgrid=False, gridcolor='lightgrey', gridwidth=1, zeroline=False
        ),
        yaxis=dict(
            title='Humidity Ratio (g water / kg dry air)', range=[W_MIN, W_MAX], side='right',
            showline=True, linewidth=1, linecolor='black', mirror=True,
            showgrid=False, gridcolor='lightgrey', gridwidth=1, zeroline=False
        ),
        margin=dict(l=40, r=60, t=60, b=40),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(255,255,255,0.7)"),
        hovermode='closest'
    )
    return fig


# Cache both base chart variants at startup
BASE_CHART_NO_ZONE   = generate_base_chart(False)
BASE_CHART_WITH_ZONE = generate_base_chart(True)


def get_base_chart(show_design_zone: bool) -> go.Figure:
    """Returns a deep copy of the cached base chart."""
    src = BASE_CHART_WITH_ZONE if show_design_zone else BASE_CHART_NO_ZONE
    return copy.deepcopy(src)


# --- API Endpoints ---

@app.get("/api/default-chart")
async def get_default_chart(showDesignZone: bool = False):
    """Serves the base chart without any plotted points."""
    fig = get_base_chart(showDesignZone)
    return {"status": "success", "figure": fig.to_json()}


@app.post("/api/generate-chart")
async def generate_chart_from_file(file: UploadFile = File(...), showDesignZone: bool = Form(False)):
    """Generates chart with points plotted from an uploaded Excel file."""
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .xlsx files are supported.")

    content = await file.read()
    await file.close()

    try:
        df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
    except Exception as e:
        error_msg = str(e)
        print(f"Excel reading error: {error_msg}")
        raise HTTPException(status_code=400, detail=f"Error reading Excel file: {error_msg}")

    if 'Temperature' not in df.columns or 'Humidity' not in df.columns:
        raise HTTPException(status_code=400, detail="Excel file must contain 'Temperature' (°C) and 'Humidity' (%) columns")

    try:
        T_db_points = df['Temperature'].astype(float).tolist()
        RH_points = df['Humidity'].astype(float).tolist()
    except ValueError:
        raise HTTPException(status_code=400, detail="Non-numeric data found in Temperature or Humidity columns.")

    fig = get_base_chart(showDesignZone)
    valid_T_db = []
    valid_W = []
    for t, rh in zip(T_db_points, RH_points):
        W = calc_humidity_ratio(t, rh)
        if W is not None:
            valid_T_db.append(t)
            valid_W.append(W)

    if valid_T_db:
        fig.add_trace(go.Scatter(
            x=valid_T_db, y=valid_W, mode='markers', name='Uploaded Data',
            marker=dict(color='red', size=2, symbol='x'),
            hovertemplate='Temp: %{x:.1f}°C<br>Humidity Ratio: %{y:.2f} g/kg<extra>Uploaded Data</extra>'
        ))

    return {"status": "success", "figure": fig.to_json()}


@app.post("/api/plot-point")
async def plot_single_point(
    temperature: float = Form(...),
    humidity: float = Form(...),
    showDesignZone: bool = Form(False)
):
    """Generates chart with a single point plotted from manual input."""
    if not (T_DB_MIN <= temperature <= T_DB_MAX):
        raise HTTPException(status_code=400, detail=f"Temperature must be between {T_DB_MIN}°C and {T_DB_MAX}°C.")
    if not (0 <= humidity <= 100):
        raise HTTPException(status_code=400, detail="Humidity must be between 0% and 100%.")

    fig = get_base_chart(showDesignZone)
    W_point = calc_humidity_ratio(temperature, humidity)

    if W_point is None:
        raise HTTPException(status_code=400, detail="Could not calculate point properties. Check input values.")

    enthalpy = calc_enthalpy(temperature, W_point)
    legend_name = (
        f"Point<br>T: {temperature:.1f}°C<br>"
        f"Relative Humidity: {humidity:.1f}%<br>"
        f"Humidity Ratio: {W_point:.2f} g/kg<br>"
        f"Enthalpy: {enthalpy:.1f} kJ/kg"
    )
    hover_template = (
        '<b>Point Properties:</b><br>'
        f'Temp: %{{x:.1f}}°C<br>'
        f'RH: {humidity:.1f}%<br>'
        f'Humidity Ratio: %{{y:.2f}} g/kg<br>'
        f'Enthalpy: {enthalpy:.1f} kJ/kg<br>'
        '<extra></extra>'
    )

    fig.add_trace(go.Scatter(
        x=[temperature], y=[W_point], mode='markers', name=legend_name,
        marker=dict(color='red', size=10, symbol='circle'),
        hovertemplate=hover_template
    ))
    fig.update_layout(
        legend=dict(
            x=0.01, y=0.99,
            xanchor='left', yanchor='top',
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='black', borderwidth=1
        )
    )

    return {"status": "success", "figure": fig.to_json()}


@app.post("/api/clear-data")
async def clear_data():
    fig = get_base_chart(False)
    return {"status": "success", "message": "Data cleared successfully", "figure": fig.to_json()}


@app.get("/")
async def root():
    return FileResponse("static/index.html", headers={"Cache-Control": "no-store"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=1)
