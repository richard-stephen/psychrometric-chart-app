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
            return 0
        P_w = RH * P_ws
        W = 0.621945 * P_w / (P - P_w)
        return W * GRAMS_PER_KG
    except (ValueError, TypeError) as e:
        print(f"Warning: psychrolib calculation error T={T_db}, RH={RH_percent}: {e}")
        return None


def calc_enthalpy(T_db, W, P=ATMOSPHERIC_PRESSURE_PA):
    """Calculates Enthalpy (kJ/kg) from T_db (°C) and Humidity Ratio (g/kg)"""
    try:
        W_kg = W / GRAMS_PER_KG
        enthalpy = psy.GetMoistAirEnthalpy(T_db, W_kg)
        return enthalpy / 1000  # Convert J/kg to kJ/kg
    except (ValueError, TypeError) as e:
        print(f"Warning: psychrolib enthalpy calculation error T={T_db}, W={W}: {e}")
        return 0
