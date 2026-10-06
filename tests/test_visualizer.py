import unittest
import pandas as pd
import json
from core.visualizer import VisualizerEngine

class TestVisualizerEngine(unittest.TestCase):
    def test_growth_trend_motion(self):
        columns = ["Month", "Revenue"]
        rows = [
            ["2024-01", 10000.0],
            ["2024-02", 14500.0],
            ["2024-03", 13200.0],
            ["2024-04", 19800.0],
            ["2024-05", 26000.0]
        ]
        suite = VisualizerEngine.generate_chart_suite(
            columns=columns,
            rows=rows,
            question="What is the revenue growth from January to May?"
        )
        self.assertIn("primary", suite)
        self.assertIn("growth_motion", suite)
        self.assertIn("donut", suite)

        # Ensure primary chart has kinetic motion frames and controls
        primary_fig = suite["primary"]
        self.assertGreaterEqual(len(primary_fig.frames), 2)
        self.assertIsNotNone(primary_fig.layout.updatemenus)
        self.assertIsNotNone(primary_fig.layout.sliders)

        # Check JSON serialization
        fig_json = primary_fig.to_json()
        self.assertTrue(len(fig_json) > 0)

    def test_categorical_ranking_motion(self):
        columns = ["Category", "Total_Sales", "Total_Profit"]
        rows = [
            ["Technology", 850000.0, 145000.0],
            ["Furniture", 740000.0, 18000.0],
            ["Office Supplies", 719000.0, 122000.0]
        ]
        suite = VisualizerEngine.generate_chart_suite(
            columns=columns,
            rows=rows,
            question="What are the top 3 categories by total sales and profit?"
        )
        self.assertIn("primary", suite)
        self.assertIn("growth_motion", suite)
        self.assertIn("donut", suite)
        self.assertIn("treemap", suite)
        self.assertIn("box", suite)
        self.assertIn("radar", suite)

        primary_fig = suite["primary"]
        self.assertEqual(len(primary_fig.frames), 3)

    def test_single_row_edge_case(self):
        columns = ["Metric", "Value"]
        rows = [["Total Portfolio", 1500000.0]]
        suite = VisualizerEngine.generate_chart_suite(
            columns=columns,
            rows=rows,
            question="What is the total portfolio value?"
        )
        self.assertIn("primary", suite)
        self.assertIsNotNone(suite["primary"])

    def test_empty_or_invalid_rows(self):
        suite = VisualizerEngine.generate_chart_suite(
            columns=["col1"],
            rows=[],
            question="Any question?"
        )
        self.assertEqual(suite, {})

if __name__ == "__main__":
    unittest.main()
