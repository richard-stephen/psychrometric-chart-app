import pandas as pd
import csv
humidity_ratios = range(5, 31, 5)  # Test from 5 to 30 g/kg in steps of 5
dewpoint_df = pd.read_csv('dewpoint_data.csv')
dewpoint_data = dewpoint_df.to_dict('records')
for data in dewpoint_data:
    hr = data['HR']
    dewpoint = data['Dew point']
    print(f"Humidity Ratio: {hr} g/kg, Dewpoint: {dewpoint}°C")

