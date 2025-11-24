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

output_path = "water_use_summary.txt"
with open(output_path, "w") as f:

    # Intro / Methodology
    f.write("============================================================\n")
    f.write(" CALIFORNIA WATER USE ANALYSIS - METHOD EXPLANATION\n")
    f.write("============================================================\n")
    f.write("This report analyzes residential water usage across suppliers.\n")
    f.write("All calculations are based on the following formulas:\n\n")
    f.write("• Efficiency (%) = ((Total Residential Use - Potable Use) / Total Residential Use) * 100\n")
    f.write("   -> Represents the share of recycled/nonpotable water.\n\n")
    f.write("• Population Served = (Total Residential Use / (R-GPCD * 365))\n")
    f.write("   -> Estimates number of residents served using daily per-capita consumption.\n\n")
    f.write("• Overuse Flag = Supplier with R-GPCD above regional median AND efficiency < 5%\n")
    f.write("   -> Identifies potential overconsumption areas.\n\n")
    f.write("• Regional Classification: based on supplier name keywords (Southern, Central, Northern California)\n\n")
    f.write("============================================================\n\n")

    # Supplier summaries
    f.write("=== SUPPLIER SUMMARIES ===\n")
    for s in suppliers[:]:
        f.write(s.summary() + "\n")

    # Overuse report (excluding missing data)
    overuse = df[
        (df["overuse_flag"]) &
        (df["efficiency_label"] != "Missing Data")
    ][
        ["supplier_name", "region", "residential_use_per_capita", "efficiency_percent", "efficiency_label"]
    ].sort_values("residential_use_per_capita", ascending=False)

    f.write("\n=== OVERUSE AREAS (EXCLUDING MISSING DATA) ===\n")
    f.write("Suppliers flagged here have R-GPCD above their region's median and efficiency < 5%.\n")
    f.write(f"Number of flagged suppliers: {len(overuse)}\n\n")
    f.write(overuse.to_string(index=False) + "\n")

    # Data quality summary
    f.write("\n=== DATA QUALITY SUMMARY ===\n")
    f.write("This shows how many rows had usable data for analysis.\n")
    f.write(df['data_quality'].value_counts().to_string() + "\n")

    f.write("\n=== EFFICIENCY DATA SUMMARY ===\n")
    f.write("Suppliers marked 'Missing Data' have no recycled/nonpotable use recorded.\n")
    f.write(df["efficiency_label"].value_counts().to_string() + "\n")

    # Residential Use Intensity by Region
    r_gpcd_summary = df.groupby("region")["residential_use_per_capita"].agg(["mean", "median", "max", "min"])
    f.write("\n=== RESIDENTIAL WATER USE INTENSITY BY REGION ===\n")
    f.write("This shows average (mean), median, and range of daily per-person use in gallons.\n")
    f.write(r_gpcd_summary.sort_values("mean", ascending=False).to_string() + "\n")

    # Top 10 Population Served
    top_pop = df.sort_values("population_served", ascending=False)[["supplier_name", "region", "population_served"]].head(10)
    f.write("\n=== TOP 10 SUPPLIERS BY ESTIMATED POPULATION SERVED ===\n")
    f.write("Shows the largest service areas based on total water and per-capita use.\n")
    f.write(top_pop.to_string(index=False) + "\n")

    # Total Residential Demand by Region
    region_demand = df.groupby("region")[["AWU_POTABLE_TOTAL_RES_GAL", "residential_potable_use"]].sum()
    region_demand["total_gal_perc"] = (region_demand["residential_potable_use"] / region_demand["residential_potable_use"].sum()) * 100
    f.write("\n=== REGIONAL SHARE OF TOTAL RESIDENTIAL WATER USE ===\n")
    f.write("Percentage share of total reported residential water use by region.\n")
    f.write(region_demand.sort_values("residential_potable_use", ascending=False).to_string() + "\n")

    # High-Use Households
    if "AWU_SF_RES_90PCTILE_GAL" in df.columns:
        top_90 = df[["supplier_name", "region", "AWU_SF_RES_90PCTILE_GAL"]].sort_values(
            "AWU_SF_RES_90PCTILE_GAL", ascending=False
        ).head(10)
        f.write("\n=== TOP 10 SUPPLIERS BY 90TH PERCENTILE SINGLE-FAMILY USE ===\n")
        f.write("Highlights where top-consuming households use the most water.\n")
        f.write(top_90.to_string(index=False) + "\n")

    # Cost-of-Service and Financial Insights
    if "AWU_COST_OF_SERVICE_HIGHEST_USERS" in df.columns:
        has_cost_study = df[df["AWU_COST_OF_SERVICE_HIGHEST_USERS"].notna()]
        f.write(f"\n{len(has_cost_study)} SUPPLIERS HAVE COST-OF-SERVICE STUDIES ON RECORD.\n")
        f.write("These studies analyze rate fairness and can incentivize conservation.\n")

    # Regional Summary Overview
    region_summary = df.groupby("region").agg({
        "residential_use_per_capita": "median",
        "population_served": "sum",
        "AWU_POTABLE_TOTAL_RES_GAL": "sum",
        "residential_potable_use": "sum",
        "efficiency_percent": "mean"
    })
    region_summary = region_summary.rename(columns={"efficiency_percent": "avg_efficiency"})
    f.write("\n=== REGIONAL SUMMARY OVERVIEW ===\n")
    f.write("Shows the median R-GPCD, total population served, and average efficiency per region.\n")
    f.write(region_summary.to_string() + "\n")

print(f"All results have been saved to {output_path}")
