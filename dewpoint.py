from scipy.optimize import root_scalar  # Import root_scalar from scipy 
import psychrolib as psy

# Constants
ATMOSPHERIC_PRESSURE_PA = 101325
GRAMS_PER_KG = 1000
T_DB_MIN, T_DB_MAX = -15, 50


def find_dewpoint_from_humidity_ratio(humidity_ratio, pressure=ATMOSPHERIC_PRESSURE_PA, temp_range=(T_DB_MIN, T_DB_MAX)):
    """
    Find the dewpoint temperature corresponding to a given humidity ratio using a numerical solver.

    Args:
        humidity_ratio (float): Humidity ratio in g/kg.
        pressure (float): Atmospheric pressure in Pa.
        temp_range (tuple): Range of temperatures to search within (min, max) in Celsius.

    Returns:
        float: Dewpoint temperature in Celsius, or None if not found.
    """
    humidity_ratio_kg_kg = humidity_ratio / GRAMS_PER_KG  # Convert g/kg to kg/kg
    def objective(T_dew):
        hr_calc = psy.GetHumRatioFromTDewPoint(T_dew,ATMOSPHERIC_PRESSURE_PA)
        return hr_calc - humidity_ratio_kg_kg

    try:
        result = root_scalar(objective, bracket=[temp_range[0], temp_range[1]], method='brentq')
        if result.converged:
            return result.root
        else:
            return None
    except Exception as e:
        print(f"Solver failed for humidity ratio {humidity_ratio}: {e}")
        return None

if __name__ == "__main__":
    # Set unit system to SI
    psy.SetUnitSystem(psy.SI)
    
    # Test the dewpoint calculation for a range of humidity ratios
    humidity_ratios = range(5, 31, 5)  # Test from 5 to 30 g/kg in steps of 5
    # Prepare data for CSV
    csv_file_path = 'dewpoint_data.csv'  # New file for dewpoint data
    new_data = []
    for hr in humidity_ratios:
        dewpoint = find_dewpoint_from_humidity_ratio(hr)
        new_data.append([hr, dewpoint])
    # Write new data to CSV
    import csv
    with open(csv_file_path, 'w', newline='') as csvfile:  # 'w' mode to create/overwrite a new file
        writer = csv.writer(csvfile)
        writer.writerow(['HR', 'Dew point'])  # Column headers
        for row in new_data:
            writer.writerow(row)
    print(f"\nResults saved to new file {csv_file_path}")