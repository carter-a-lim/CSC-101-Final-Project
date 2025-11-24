# CSC-101-Final-Project
Data input: https://data.ca.gov/dataset/urban-water-use-objectives-compiled-report-data/resource/9a773df4-af2f-450d-b0e5-f49f4a1e1523

# Data Cleaning NOAH:
turn csv into classes ->
### Expected way of doing it + output
use pandas library, maybe use groq api for lableing region, create new file eg data.py which jus contains the list of the classes

Class Name: WaterSupplier \
Attributes: \
supplier_name — name of the urban water supplier \
region — regional classification (e.g., Northern, Southern California) \
potable_water_use — potable water use in gallons \
recycled_water_use — recycled water volume \
population_served — total population served by the supplier \
residential_use_per_capita — residential gallons per capita per day \
Methods:\
calculate_total_use() – returns total water use (potable + recycled) \
calculate_efficiency() – computes efficiency ratio (recycled / total) \
classify_efficiency() – returns category label: "Efficient", "Moderate", or "Inefficient" \
usage_per_person() – calculates per-person daily water use \
summary() – returns formatted summary string for output

# Data structure: CARTER:
Store WaterSupplier elements in a list, each will be created by loading data from a csv file.

Dictionaries
One to keep track of average efficiency by region \
One to store “tips” (ways to improve efficiency or compliment if doing well)

Outline of file handling (data source, input/output format).\
Data Output: txt file, will have supplier name, total use, efficiency, efficiency-category, etc. also output efficiency by region.

### Expected outputs or insights.
Which regions use the most potable vs recycled water\
Efficiency percentage by region or company\
Residential gallons per capita per day (R-GPCD)\
Identification of “overuse” areas

### key metrics:
Potable vs. Total Residential Water Use
- Determines potable demand and inferred recycled/nonpotable share.
- Aggregated by region to identify where potable reliance is highest.

Efficiency Percentage (Recycled/Nonpotable Share)
- Efficiency % = (Nonpotable ÷ Total) × 100
- Categorized per supplier and averaged by region.

Residential Gallons per Capita per Day (R-GPCD)
- Indicates average daily residential water use per person.
- Used for comparisons across suppliers and regions.

Overuse Identification
- Flags suppliers with:
- R-GPCD above regional median
- Efficiency below 5%
- Provides a list of “overuse areas.”
