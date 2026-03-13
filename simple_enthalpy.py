import numpy as np
import psychrolib as psy

# Set unit system to SI
psy.SetUnitSystem(psy.SI)

# Constants
ATMOSPHERIC_PRESSURE_PA = 101325
GRAMS_PER_KG = 1000


def calc_humidity_ratio(T_db, RH_percent, P=ATMOSPHERIC_PRESSURE_PA):
    """Calculates Humidity Ratio (g/kg) from T_db (°C) and RH (%)"""
    RH = RH_percent / 100.0
    try:
        P_ws = psy.GetSatVapPres(T_db)
        if P_ws <= 0:
            return None
        P_w = RH * P_ws
        W = 0.621945 * P_w / (P - P_w)
        return W * GRAMS_PER_KG
    except (ValueError, TypeError) as e:
        print(f"Warning: psychrolib calculation error T={T_db}, RH={RH_percent}: {e}")
        return None


def calc_humidity_ratios_vectorized(T_db_arr, RH_percent_arr, P=ATMOSPHERIC_PRESSURE_PA):
    """Vectorized humidity ratio calculation for arrays of T_db (°C) and RH (%)."""
    T_db = np.asarray(T_db_arr, dtype=float)
    RH = np.asarray(RH_percent_arr, dtype=float) / 100.0

    # ASHRAE saturation vapor pressure coefficients (same as psychrolib)
    C1 = -5.6745359e3; C2 = 6.3925247e0; C3 = -9.6778430e-3
    C4 = 6.2215701e-7; C5 = 2.0747825e-9; C6 = -9.4840240e-13; C7 = 4.1635019e0
    C8 = -5.8002206e3; C9 = 1.3914993e0; C10 = -4.8640239e-2
    C11 = 4.1764768e-5; C12 = -1.4452093e-8; C13 = 6.5459673e0

    T_K = T_db + 273.15
    ln_P_ws = np.where(
        T_db < 0,
        C1/T_K + C2 + C3*T_K + C4*T_K**2 + C5*T_K**3 + C6*T_K**4 + C7*np.log(T_K),
        C8/T_K + C9 + C10*T_K + C11*T_K**2 + C12*T_K**3 + C13*np.log(T_K)
    )
    P_ws = np.exp(ln_P_ws)

    P_w = RH * P_ws
    W = 0.621945 * P_w / (P - P_w)
    W_gkg = W * GRAMS_PER_KG

    valid = np.isfinite(W_gkg) & (P_ws > 0)
    return W_gkg, valid


def calc_enthalpy(T_db, W, P=ATMOSPHERIC_PRESSURE_PA):
    """Calculates Enthalpy (kJ/kg) from T_db (°C) and Humidity Ratio (g/kg)"""
    try:
        W_kg = W / GRAMS_PER_KG
        enthalpy = psy.GetMoistAirEnthalpy(T_db, W_kg)
        return enthalpy / 1000  # Convert J/kg to kJ/kg
    except (ValueError, TypeError) as e:
        print(f"Warning: psychrolib enthalpy calculation error T={T_db}, W={W}: {e}")
        return None
