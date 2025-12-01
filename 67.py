import pandas as pd
from data import WaterSupplier

# CSV to list of objects is by Noah
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

df["AWU_POTABLE_TOTAL_RES_GAL"] = to_num(df["AWU_POTABLE_TOTAL_RES_GAL"])
df["residential_potable_use"] = to_num(df["residential_potable_use"])
df["residential_use_per_capita"] = to_num(df["residential_use_per_capita"])

# Data quality flag
df["data_quality"] = df.apply(
    lambda r: "incomplete"
    if (r["residential_potable_use"] <= 0 or r["AWU_POTABLE_TOTAL_RES_GAL"] <= 0 or r["residential_use_per_capita"] <= 0)
    else "good",
    axis=1
)

# Filter only valid rows
df = df[df["data_quality"] == "good"].copy()

# 4) Derived fields
df["recycled_or_nonpotable_use"] = (
    df["residential_potable_use"] - df["AWU_POTABLE_TOTAL_RES_GAL"]
).clip(lower=0)
df["potable_water_use"] = df["AWU_POTABLE_TOTAL_RES_GAL"]
df["recycled_water_use"] = df["recycled_or_nonpotable_use"]

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

df["region"] = df["supplier_name"].apply(classify_region)

# 7) Efficiency metrics
df["efficiency_percent"] = (
    (df["residential_potable_use"] - df["AWU_POTABLE_TOTAL_RES_GAL"]) /
    df["residential_potable_use"].replace(0, pd.NA)
) * 100
df["efficiency_percent"] = df["efficiency_percent"].clip(lower=0, upper=100)
df["efficiency_label"] = df["efficiency_percent"].apply(lambda x: "Missing Data" if x == 0 else "Reported")

# Remove extreme R-GPCD outliers
df.loc[df["residential_use_per_capita"] > 1000, "residential_use_per_capita"] = None

# Adaptive regional medians for overuse flag
regional_medians = df.groupby("region")["residential_use_per_capita"].median().to_dict()
df["overuse_flag"] = df.apply(
    lambda r: (r["residential_use_per_capita"] > regional_medians.get(r["region"], 80))
    and (r["efficiency_percent"] < 5),
    axis=1
)

# 8) Create WaterSupplier objects
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

# summary by carter
with open("water_use_summary.txt", "w") as f:
    tips = {
        "high_usage": "Try reducing outdoor watering and check for leaks.",
        "efficient": "Great job! Keep maintaining low water usage.",
        "missing": "No recycled water recorded. Consider conservation programs or better tracking."
    }

    f.write("CALIFORNIA WATER USE SUMMARY\n\n")

    # Potable vs Nonpotable by region
    f.write("1. POTABLE VS NONPOTABLE (RECYCLED) WATER BY REGION\n")
    region_potable = df.groupby("region")["AWU_POTABLE_TOTAL_RES_GAL"].sum()
    region_total = df.groupby("region")["residential_potable_use"].sum()
    region_nonpotable = region_total - region_potable

    for region in region_total.index:
        f.write(f"{region}:\n")
        f.write(f"   Potable Use: {region_potable[region]:,.0f} gallons\n")
        f.write(f"   Nonpotable Use: {region_nonpotable[region]:,.0f} gallons\n\n")

    # Efficiency by region
    f.write("2. WATER EFFICIENCY BY REGION\n")
    region_eff = df.groupby("region")["efficiency_percent"].mean()

    for region, eff in region_eff.items():
        f.write(f"{region}: {eff:.5f}% efficiency\n")
    f.write("\n")

    # R-GPCD by region
    f.write("3. RESIDENTIAL GALLONS PER CAPITA PER DAY (R-GPCD)\n")
    region_gpcd = df.groupby("region")["residential_use_per_capita"].mean()

    for region, gpcd in region_gpcd.items():
        f.write(f"{region}: {gpcd:.2f} gallons/person/day\n")
    f.write("\n")

    # Overuse identification
    f.write("4. IDENTIFIED OVERUSE AREAS\n")
    overuse = df[
        (df["overuse_flag"]) &
        (df["efficiency_label"] != "Missing Data")
    ][["supplier_name", "region", "residential_use_per_capita", "efficiency_percent"]]

    if len(overuse) == 0:
        f.write("No overuse areas identified.\n\n")
    else:
        for _, row in overuse.iterrows():
            f.write(f"{row['supplier_name']} ({row['region']}):\n")
            f.write(f"   R-GPCD: {row['residential_use_per_capita']:.2f}\n")
            f.write(f"   Efficiency: {row['efficiency_percent']:.2f}%\n\n")

    # === SUSTAINABILITY TIP *PER REGION* ===
    f.write("=== SUSTAINABILITY TIP BY REGION ===\n")

    # Determine tip for each region using your existing tips dict
    for region, eff in region_eff.items():

        if eff == 0:
            chosen_tip = tips["missing"]
        elif eff < 0.6:
            chosen_tip = tips["high_usage"]
        else:
            chosen_tip = tips["efficient"]

        f.write(f"{region}:\n")
        f.write(f"   {chosen_tip}\n\n")


print("Summary written to water_use_summary.txt")
