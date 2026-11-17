# Run from the archive root

Install requirements.txt, then run:

python code/03_food_geography_and_cuisine_chart.py
python code/04_population_composition.py
python code/05_retail_housing_schools_map.py
python code/06_walking_time_corridor_chart.py

Rebuilt figures are written to analysis_outputs; images preserves the delivered figures.

To download CURRENT inputs: python code/01_download.py raw_data/current_download
To rerun routing with historical raw inputs: python code/02_walktime.py HISTORICAL_RAW_DIRECTORY NEW_OUTPUT_DIRECTORY
The historical raw directory must contain cd403.geojson, nta_qn03.geojson, dohmh_queens.json, subway_entrances.json and cscl_box.geojson. Do not overwrite the archived results with a new snapshot.

Retail corridor counts: python code/07_retail_corridor_statistics.py
