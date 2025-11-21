import pandas as pd
from data import WaterSupplier

# 1) Load CSV
df = pd.read_csv("actualwateruse (1).csv")

# 2) Rename columns for readability
df = df.rename(columns={
    "SUPPLIER_NAME": "supplier_name",
    "AWU_TOTAL_RES_GAL": "residential_potable_use",
    "AWU_TOTAL_RES_RGPCD": "residential_use_per_capita",
})

# 3) Ensure numeric types
def to_num(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)

df["residential_potable_use"] = to_num(df["residential_potable_use"])
df["residential_use_per_capita"] = to_num(df["residential_use_per_capita"])

# 4) Calculate potable total (can include recycled later if desired)
df["potable_water_use"] = df["residential_potable_use"]
df["recycled_water_use"] = 0

# 5) Estimate population served (annual data!)
# population = annual residential gallons / (RGPCD * 365)
df["population_served"] = df.apply(
    lambda r: (r["residential_potable_use"] / (r["residential_use_per_capita"] * 365))
    if r["residential_use_per_capita"] > 0 else 0,
    axis=1
)

# 6) Region classifier
def classify_region(name: str) -> str:
    n = str(name).lower()
    if any(x in n for x in ["san diego", "los angeles", "orange", "riverside", "imperial"]):
        return "Southern California"
    if any(x in n for x in ["sacramento", "napa", "bay", "sonoma", "humboldt"]):
        return "Northern California"
    return "Central California"

# 7) Create WaterSupplier objects
suppliers = []
for _, row in df.iterrows():
    suppliers.append(
        WaterSupplier(
            supplier_name=row["supplier_name"],
            region=classify_region(row["supplier_name"]),
            potable_water_use=row["potable_water_use"],
            recycled_water_use=row["recycled_water_use"],
            population_served=row["population_served"],
            residential_use_per_capita=row["residential_use_per_capita"],
        )
    )

# 8) Print sample summaries
for s in suppliers[:]: #controls how many are shown from the dataset
    print(s.summary())

#region only
# for s in suppliers:
#     if s.region == "Southern California":
#         print(s.summary())

#efficiency only
# for s in suppliers:
#     if s.region == "Southern California":
#         print(s.summary())

