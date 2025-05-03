from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import plotly.graph_objects as go
import psychrolib as psy
import pandas as pd
import io # Needed for reading UploadFile content with pandas

app = FastAPI()
psy.SetUnitSystem(psy.SI)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins for simplicity, restrict in production
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

# Custom StaticFiles to prevent caching (good practice for development)
class CustomStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        # Disable caching for static files during development
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.mount("/static", CustomStaticFiles(directory="static", html=True), name="static")

# Constants
ATMOSPHERIC_PRESSURE_PA = 101325
GRAMS_PER_KG = 1000
T_DB_MIN, T_DB_MAX = -10, 50
W_MIN, W_MAX = 0, 30 # Adjusted Y-axis range slightly for better visuals
t_axis = range(-10, 46,5)

# --- Helper Functions ---

def calc_humidity_ratio(T_db, RH_percent, P=ATMOSPHERIC_PRESSURE_PA):
    """Calculates Humidity Ratio (g/kg) from T_db (°C) and RH (%)"""
    RH = RH_percent / 100.0 # Convert percentage to fraction
    try:
        P_ws = psy.GetSatVapPres(T_db)
        if P_ws <= 0: return 0 # Handle edge case for very low temps
        P_w = RH * P_ws
        W = 0.621945 * P_w / (P - P_w)
        return W * GRAMS_PER_KG
    except Exception as e:
        # Minimal logging for psychrolib errors during development
        print(f"Warning: psychrolib calculation error T={T_db}, RH={RH_percent}: {e}")
        return None # Indicate calculation failure

def generate_base_chart(show_design_zone: bool = False):
    """Generates the base psychrometric chart figure with enthalpy lines."""
    T_db_range = np.linspace(T_DB_MIN, T_DB_MAX, 100)
    fig = go.Figure()

    # Saturation Line (100% RH)
    W_sat_list = []
    for t in T_db_range:
        W_sat = calc_humidity_ratio(t, 100.0)
        W_sat_list.append(W_sat)
    fig.add_trace(go.Scatter(
        x=T_db_range, y=W_sat_list, mode='lines', showlegend=False,
        line=dict(color='rgba(38,70,83,0.8)', width=2), hoverinfo='skip'
    ))
    #Adding x axis as temperature points
    for t in t_axis:
        w_sat_t = calc_humidity_ratio(t, 100.0)
        fig.add_trace(go.Scatter(
            x=[t,t], y=[0,w_sat_t], mode='lines',
            line=dict(color='rgba(38,70,83,0.5)', width=1), opacity=0.3, hoverinfo='skip', showlegend=False
        ))
    # Humidity ratio lines
    humidity_ratios = range(5, 31, 5)  # Test from 5 to 30 g/kg in steps of 5
    dewpoint_df = pd.read_csv('dewpoint_data.csv')
    dewpoint_data = dewpoint_df.to_dict('records')
    for data in dewpoint_data:
        hr = data['HR']
        dewpoint = data['Dew point']
        fig.add_trace(go.Scatter(   
            x=[dewpoint, T_DB_MAX], y=[hr,hr], mode='lines',
            line=dict(color='rgba(38,70,83,0.5)', width=1), opacity=0.3, hoverinfo='skip', showlegend=False
        ))
    # Relative Humidity Lines
    RH_levels = [10, 20, 30, 40, 50, 60, 70, 80, 90]
    for rh in RH_levels:
        W_rh_list = []
        for t in T_db_range:
            W_rh = calc_humidity_ratio(t, float(rh))
            W_rh_list.append(W_rh)
        fig.add_trace(go.Scatter(
            x=T_db_range, y=W_rh_list, mode='lines',
            line=dict(color='rgba(38,70,83,0.5)', width=1, dash='dash'), opacity=1.0, hoverinfo='skip', showlegend=False
        ))
        # Add annotation for each RH line inside the chart space
        if rh == 90:
            index_position = int(len(T_db_range) * 0.75)  # 71% of the temperature range for 90% RH
        else:
            index_position = int(len(T_db_range) * 0.75)  # 75% for other RH levels
        fig.add_annotation(x=T_db_range[index_position], y=W_rh_list[index_position],
                           text=f'{rh}%', showarrow=False,
                           font=dict(size=10, color='rgba(38,70,83,1)'),
                           xanchor='center', yanchor='middle')
    try:
        enthalpy_df = pd.read_csv("enthalpy_intersections.csv")
        enthalpy_data = enthalpy_df.to_dict('records')
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="enthalpy_intersections.csv not found in project folder.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading enthalpy_intersections.csv: {str(e)}")

    for data in enthalpy_data:
        h = data["Enthalpy"]  # Enthalpy in kJ/kg
        T_intersect = data["Temperature"]
        W_intersect = data["Humidity Ratio"]

        # Calculate starting point at W=0: h = 1.006 * T
        T_start = h / 1.006  # Temperature at W=0

        # Generate points from T_intersect to T_start
        T_points = np.linspace(T_intersect, T_start, 50)
        W_points = []
        for T in T_points:
            # Use psychrolib's enthalpy model: h = 1.006 * T + (W/1000) * (2501 + 1.86 * T)
            W = ((h - 1.006 * T) * 1000) / (2501 + 1.86 * T)  # W in g/kg
            W_points.append(W)

        # Add the enthalpy line trace
        fig.add_trace(go.Scatter(
            x=T_points,
            y=W_points,
            mode='lines',
            line=dict(color='rgba(38,70,83,1)', width=1, dash='dot'),  # Navy, solid
            hoverinfo='skip',
            showlegend=False,
        ))

        # Add annotation at the saturation intersection
        fig.add_annotation(
            x=T_intersect,
            y=W_intersect,
            text=f"{int(h)}",
            showarrow=False,
            font=dict(size=9, color='purple'),
            xanchor='left',
            yanchor='middle'
        )
        fig.add_annotation(
            x=10,
            y=15,
            text='Enthalpy kJ/kg',
            showarrow=False,
            font=dict(family='Arial, sans-serif', size=18, color='rgba(38,70,83,1)'),
            xanchor='left',
            yanchor='middle'
        )

    # Comfort Zone (Optional)
    if show_design_zone:
        T_comfort = np.array([20, 24])
        W_comfort_low = [calc_humidity_ratio(t, 40, ATMOSPHERIC_PRESSURE_PA) for t in T_comfort]
        W_comfort_high = [calc_humidity_ratio(t, 60, ATMOSPHERIC_PRESSURE_PA) for t in T_comfort]
        fig.add_trace(go.Scatter(
            x=[20, 24, 24, 20, 20],
            y=[W_comfort_low[0], W_comfort_low[1], W_comfort_high[1], W_comfort_high[0], W_comfort_low[0]],
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
            showline=True, linewidth=1, linecolor='black', mirror=True,dtick = 5,
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

# --- API Endpoints ---

@app.get("/api/default-chart")
async def get_default_chart(showDesignZone: bool = False):
    """Serves the base chart without any plotted points."""
    # No broad try-except here; errors in helpers might bubble up (or return None)
    fig = generate_base_chart(showDesignZone)
    return {"status": "success", "figure": fig.to_json()}

@app.post("/api/generate-chart")
async def generate_chart_from_file(file: UploadFile = File(...), showDesignZone: bool = Form(False)):
    """Generates chart with points plotted from an uploaded Excel file."""
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .xlsx files are supported.")

    content = await file.read()
    await file.close() # Close the file after reading

    try:
        df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        # Catch specific pandas/excel reading errors
        raise HTTPException(status_code=400, detail=f"Error reading Excel file: {str(e)}")

    if 'Temperature' not in df.columns or 'Humidity' not in df.columns:
        raise HTTPException(status_code=400, detail="Excel file must contain 'Temperature' (°C) and 'Humidity' (%) columns")

    try:
        T_db_points = df['Temperature'].astype(float).tolist()
        RH_points = df['Humidity'].astype(float).tolist() # Assuming humidity is in %
    except ValueError:
         raise HTTPException(status_code=400, detail="Non-numeric data found in Temperature or Humidity columns.")

    # Basic validation for data points (optional refinement)
    # if not all(isinstance(t, (int, float)) for t in T_db_points) or \
    #    not all(isinstance(rh, (int, float)) and 0 <= rh <= 100 for rh in RH_points):
    #      raise HTTPException(status_code=400, detail="Invalid data found. Check Temperature and Humidity values (0-100%).")

    fig = generate_base_chart(showDesignZone)
    W_points = []
    for t, rh in zip(T_db_points, RH_points):
        W_point = calc_humidity_ratio(t, rh)
        W_points.append(W_point)

    valid_points = []
    for t, w in zip(T_db_points, W_points):
        if w is not None:
            valid_points.append((t, w))
    valid_T_db = []
    valid_W = []
    for point in valid_points:
        valid_T_db.append(point[0])
        valid_W.append(point[1])

    if valid_T_db: # Only add trace if there are valid points
        fig.add_trace(go.Scatter(
            x=valid_T_db, y=valid_W, mode='markers', name='Uploaded Data',
            marker=dict(color='red', size=2, symbol='x'),
            hovertemplate='Temp: %{x:.1f}°C<br>Humidity Ratio: %{y:.2f} g/kg<extra>Uploaded Data</extra>'
        ))

    return {"status": "success", "figure": fig.to_json()}


# Endpoint for Manual Input
@app.post("/api/plot-point")
async def plot_single_point(
    temperature: float = Form(...),
    humidity: float = Form(...),
    showDesignZone: bool = Form(False)
):
    """Generates chart with a single point plotted from manual input."""
    # Basic Input Validation (kept as it's essential)
    if not (T_DB_MIN <= temperature <= T_DB_MAX):
         raise HTTPException(status_code=400, detail=f"Temperature must be between {T_DB_MIN}°C and {T_DB_MAX}°C.")
    if not (0 <= humidity <= 100):
         raise HTTPException(status_code=400, detail="Humidity must be between 0% and 100%.")

    fig = generate_base_chart(showDesignZone)
    W_point = calc_humidity_ratio(temperature, humidity)

    if W_point is None:
         # If calculation failed, inform the client it couldn't be plotted
         raise HTTPException(status_code=400, detail="Could not calculate point properties. Check input values.")

    fig.add_trace(go.Scatter(
        x=[temperature], y=[W_point], mode='markers', name='Plot Point',
        marker=dict(color='red', size=10, symbol='circle'),
        hovertemplate='Temp: %{x:.1f}°C<br>RH: '+f'{humidity:.1f}%'+'<br>Humidity Ratio: %{y:.2f} g/kg<extra>Manual Input</extra>'
    ))

    return {"status": "success", "figure": fig.to_json()}

@app.post("/api/clear-data")
async def clear_data():
    fig = generate_base_chart()
    return {"status": "success", "message": "Data cleared successfully", "figure": fig.to_json()}

# Serve the SPA's index.html at the root
@app.get("/")
async def root():
    return FileResponse("static/index.html", headers={"Cache-Control": "no-store"}) # Ensure index isn't cached

if __name__ == "__main__":
    import uvicorn
    # Use reload=True for development
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=1)
