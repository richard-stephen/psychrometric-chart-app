import numpy as np
import psychrolib as psy
from scipy.optimize import root_scalar
import csv

# Set unit system to SI
psy.SetUnitSystem(psy.SI)

# Constants
ATMOSPHERIC_PRESSURE_PA = 101325
GRAMS_PER_KG = 1000
T_DB_MIN, T_DB_MAX = -15, 50


def calc_humidity_ratio(T_db, RH_percent, P=ATMOSPHERIC_PRESSURE_PA):
    RH = RH_percent / 100.0  # Convert percentage to fraction
    try:
        P_ws = psy.GetSatVapPres(T_db)
        P_w = RH * P_ws
        W = 0.621945 * P_w / (P - P_w)
        return W * GRAMS_PER_KG
    except Exception as e:
        print(f"Warning: psychrolib calculation error T={T_db}, RH={RH_percent}: {e}")
        return None  # Indicate calculation failure


def calc_enthalpy(T_db, W, P=ATMOSPHERIC_PRESSURE_PA):
    """Calculates Enthalpy (kJ/kg) from T_db (°C) and Humidity Ratio (g/kg)"""
    try:
        W_kg = W / GRAMS_PER_KG  # Convert g/kg to kg/kg
        enthalpy = psy.GetMoistAirEnthalpy(T_db, W_kg)
        return enthalpy / 1000  # Convert J/kg to kJ/kg
    except Exception as e:
        print(f"Warning: psychrolib enthalpy calculation error T={T_db}, W={W}: {e}")
        return None


def find_saturation_temp_for_enthalpy(target_enthalpy, P=ATMOSPHERIC_PRESSURE_PA):
    """Find the temperature at which the enthalpy at saturation (100% RH) equals the target enthalpy."""
    def objective(T_db):
        W_sat = calc_humidity_ratio(T_db, 100.0, P)
        enthalpy = calc_enthalpy(T_db, W_sat, P)
        return enthalpy - target_enthalpy

    try:
        result = root_scalar(objective, bracket=[T_DB_MIN, T_DB_MAX], method='brentq')
        if result.converged:
            T_db = result.root
            W_sat = calc_humidity_ratio(T_db, 100.0, P)
            return T_db, W_sat
        else:
            return None, None
    except Exception as e:
        print(f"Solver failed for enthalpy {target_enthalpy}: {e}")
        return None, None


def precalculate_enthalpy_intersections():
    """Pre-calculate intersection points of enthalpy lines with the saturation line."""
    enthalpy_levels = range(-10, 101, 10)  # Enthalpy levels from -10 to 100 kJ/kg
    intersections = {}
    for h in enthalpy_levels:
        T_db, W = find_saturation_temp_for_enthalpy(h)
        if T_db is not None and W is not None:
            intersections[h] = (T_db, W)
        else:
            print(f"Failed to find intersection for enthalpy {h} kJ/kg")
    
    # Save intersections to CSV file
    with open('enthalpy_intersections.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Enthalpy (kJ/kg)', 'Temperature (°C)', 'Humidity Ratio (g/kg)'])
        for h, (T_db, W) in intersections.items():
            writer.writerow([h, T_db, W])
    
    return intersections


if __name__ == "__main__":
    # Calculate and print the intersections for reference
    intersections = precalculate_enthalpy_intersections()
    print("Intersection data has been saved to 'enthalpy_intersections.csv'")
