import psychrolib as psy

# Set unit system to SI
psy.SetUnitSystem(psy.SI)

# Constants
GRAMS_PER_KG = 1000

def calc_enthalpy(T_db, W, P=101325):
    """Calculates Enthalpy (kJ/kg) from T_db (°C) and Humidity Ratio (g/kg)"""
    try:
        W_kg = W / 1000  # Convert g/kg to kg/kg
        enthalpy = psy.GetMoistAirEnthalpy(T_db, W_kg)
        return enthalpy / 1000  # Convert J/kg to kJ/kg
    except Exception as e:
        print(f"Warning: psychrolib enthalpy calculation error T={T_db}, W={W}: {e}")
        return 0  # Return 0 instead of None to avoid further issues
