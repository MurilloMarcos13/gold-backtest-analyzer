from pathlib import Path
import unittest

from analyzer import analyze_trades, load_trades, longest_streak


SAMPLE_FILE = Path(__file__).parent.parent / "sample_data" / "trades_example.csv"


class AnalyzerTests(unittest.TestCase):
    def test_loads_and_sorts_sample_trades(self):
        trades = load_trades(SAMPLE_FILE)

        self.assertEqual(len(trades), 12)
        self.assertEqual(trades[0].trade_id, "T001")
        self.assertEqual(trades[-1].trade_id, "T012")

    def test_calculates_main_metrics(self):
        analysis = analyze_trades(load_trades(SAMPLE_FILE), initial_balance=10_000)
        summary = analysis["summary"]

        self.assertEqual(summary["net_profit"], 230.0)
        self.assertEqual(summary["gross_profit"], 373.0)
        self.assertEqual(summary["gross_loss"], -143.0)
        self.assertEqual(summary["total_trades"], 12)
        self.assertEqual(summary["winning_trades"], 7)
        self.assertEqual(summary["losing_trades"], 5)
        self.assertEqual(summary["win_rate_percent"], 58.33)
        self.assertEqual(summary["profit_factor"], 2.61)
        self.assertEqual(summary["max_drawdown"], 58.0)

    def test_calculates_streaks(self):
        profits = [10, 20, -5, -6, -7, 0, 4]

        self.assertEqual(longest_streak(profits, winning=True), 2)
        self.assertEqual(longest_streak(profits, winning=False), 3)

    def test_groups_results_by_month(self):
        analysis = analyze_trades(load_trades(SAMPLE_FILE))

        self.assertEqual(
            analysis["monthly_results"],
            {"2026-01": 99.0, "2026-02": 131.0},
        )

    def test_rejects_non_positive_initial_balance(self):
        trades = load_trades(SAMPLE_FILE)

        with self.assertRaisesRegex(ValueError, "greater than zero"):
            analyze_trades(trades, initial_balance=0)


if __name__ == "__main__":
    unittest.main()
