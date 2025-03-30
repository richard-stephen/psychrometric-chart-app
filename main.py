from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import plotly.graph_objects as go
import psychrolib as psy
import pandas as pd

app = FastAPI()
psy.SetUnitSystem(psy.SI)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom StaticFiles to prevent caching
class CustomStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store"
        return response

app.mount("/static", CustomStaticFiles(directory="static", html=True), name="static")

# Constants
ATMOSPHERIC_PRESSURE_PA = 101325
GRAMS_PER_KG = 1000
T_DB_MIN, T_DB_MAX = 0, 50

# Helper function to generate base chart data
def generate_base_chart(show_design_zone: bool = False):
    T_db = np.linspace(T_DB_MIN, T_DB_MAX, 100)

    def calc_humidity_ratio(T_db, RH, P):
        P_ws = psy.GetSatVapPres(T_db)
        P_w = RH * P_ws
        W = 0.621945 * P_w / (P - P_w)
        return W * GRAMS_PER_KG

    W_sat = [calc_humidity_ratio(t, 1.0, ATMOSPHERIC_PRESSURE_PA) for t in T_db]
    RH_levels = [0.2, 0.4, 0.6, 0.8]
    W_RH = {rh: [calc_humidity_ratio(t, rh, ATMOSPHERIC_PRESSURE_PA) for t in T_db] for rh in RH_levels}

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=T_db, y=W_sat, mode='lines', name='100% RH', line=dict(color='blue')))
    for rh, W in W_RH.items():
        fig.add_trace(go.Scatter(x=T_db, y=W, mode='lines', name=f'{int(rh*100)}% RH', line=dict(dash='dash')))

    if show_design_zone:
        T_comfort = np.array([14, 22])
        W_comfort_low = [calc_humidity_ratio(t, 0.4, ATMOSPHERIC_PRESSURE_PA) for t in T_comfort]
        W_comfort_high = [calc_humidity_ratio(t, 0.6, ATMOSPHERIC_PRESSURE_PA) for t in T_comfort]
        fig.add_trace(go.Scatter(
            x=[14, 22, 22, 14, 14],
            y=[W_comfort_low[0], W_comfort_low[1], W_comfort_high[1], W_comfort_high[0], W_comfort_low[0]],
            mode='lines', name='Comfort Zone', line=dict(color='black', dash='dash', width=2),
            fill='toself', fillcolor='rgba(0,255,0,0.1)',
        ))

    fig.update_layout(
        title='Psychrometric Chart',
        title_x=0.5,
        xaxis=dict(
            title='Dry-Bulb Temperature (°C)',
            showline=True,  # Show x-axis line
            linewidth=2,
            linecolor='black',
            mirror=True,    # Mirror line on top
            showgrid=True,
            gridcolor='lightgrey',
            gridwidth=1,
            range=[T_DB_MIN, T_DB_MAX],
            showticklabels=True
        ),
        yaxis=dict(
            title='Humidity Ratio (g/kg)',
            side='right',   # Move y-axis to the right
            showline=True,  # Show y-axis line
            linewidth=2,
            linecolor='black',
            mirror=True,    # Mirror line on left
            showgrid=True,
            gridcolor='lightgrey',
            gridwidth=1,
            range=[0, 50],  # Set a reasonable range for humidity ratio
            showticklabels=True
        ),
        plot_bgcolor='#ffffff',
        paper_bgcolor='#ffffff',
        margin=dict(l=50, r=50, t=50, b=50),
    )
    return fig

# Default chart endpoint
@app.get("/api/default-chart")
async def get_default_chart(showDesignZone: bool = False):
    fig = generate_base_chart(showDesignZone)
    return {"status": "success", "figure": fig.to_json()}

# File upload endpoint
@app.post("/api/generate-chart")
async def generate_chart(file: UploadFile = File(...), showDesignZone: bool = Form(False)):
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")

    try:
        df = pd.read_excel(file.file)
        if 'Temperature' not in df.columns or 'Humidity' not in df.columns:
            raise HTTPException(status_code=400, detail="Excel file must contain 'Temperature' and 'Humidity' columns")
        T_db_room = df['Temperature'].values.tolist()
        RH_room = (df['Humidity'].values / 100).tolist()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

    fig = generate_base_chart(showDesignZone)

    def calc_humidity_ratio(T_db, RH, P):
        P_ws = psy.GetSatVapPres(T_db)
        P_w = RH * P_ws
        W = 0.621945 * P_w / (P - P_w)
        return W * GRAMS_PER_KG

    W_room = [calc_humidity_ratio(t, rh, ATMOSPHERIC_PRESSURE_PA) for t, rh in zip(T_db_room, RH_room)]
    fig.add_trace(go.Scatter(
        x=T_db_room, y=W_room, mode='markers', name='Room Conditions', marker=dict(color='red', size=2,symbol='cross'),
        hovertemplate='Temp: %{x:.1f}°C<br>Humidity: %{y:.1f}g/kg<extra>Room Conditions</extra>'
    ))

    return {"status": "success", "figure": fig.to_json()}

# Serve the SPA
@app.get("/")
async def root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="debug", workers=1)