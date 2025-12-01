import unittest
from data import WaterSupplier

class TestCases(unittest.TestCase):

    def test_total_use(self):
        supplier = WaterSupplier("Test City", "Central California", 500, 100, 50, 10)
        self.assertEqual(supplier.calculate_total_use(), 600)

    def test_usage_per_person(self):
        supplier = WaterSupplier("Test City", "Central California", 500, 100, 50, 10)
        self.assertEqual(supplier.usage_per_person(), 10)

    def test_efficiency_classification_efficient(self):
        supplier = WaterSupplier("Efficient City", "Northern California", 100, 50, 10, 40)
        self.assertEqual(supplier.classify_efficiency(), "Efficient")

    def test_efficiency_classification_inefficient(self):
        supplier = WaterSupplier("Inefficient City", "Southern California", 100, 10, 10, 90)
        self.assertEqual(supplier.classify_efficiency(), "Inefficient")

    def test_summary_contains_name(self):
        supplier = WaterSupplier("Summary City", "Central California", 1000, 200, 50, 60)
        self.assertIn("Summary City", supplier.summary())

if __name__ == "__main__":
    unittest.main()
