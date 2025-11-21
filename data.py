class WaterSupplier:
    def __init__(self, supplier_name, region, potable_water_use, recycled_water_use,
                 population_served, residential_use_per_capita):
        self.supplier_name = supplier_name
        self.region = region
        self.potable_water_use = potable_water_use
        self.recycled_water_use = recycled_water_use
        self.population_served = population_served
        self.residential_use_per_capita = residential_use_per_capita  # RGPCD if provided

    def calculate_total_use(self):
        return self.potable_water_use + self.recycled_water_use

    # Use RGPCD if available; else compute from totals/pop
    def usage_per_person(self):
        if self.residential_use_per_capita and self.residential_use_per_capita > 0:
            return self.residential_use_per_capita  # already gallons/person/day
        # Fallback: if your total use is for a month/year, adjust here accordingly.
        # Assuming total is for 1 day; if it's monthly, divide by 30; if yearly, divide by 365.
        return (self.calculate_total_use() / self.population_served) if self.population_served else 0

    # Treat "efficiency" as meeting the < 50 gpcd target
    def calculate_efficiency(self):
        # return a simple boolean-like score if you still want a numeric value
        return 1.0 if self.usage_per_person() < 50 else 0.0

    def classify_efficiency(self):
        return "Efficient" if self.usage_per_person() < 50 else "Inefficient"

    def summary(self):
        return (
            f"{self.supplier_name} ({self.region})\n"
            f"  Total Use: {self.calculate_total_use():,.2f} gallons\n"
            f"  Efficiency: {self.classify_efficiency()}\n"
            f"  Use per Person: {self.usage_per_person():.2f} gallons/day\n"
        )
