# Gold Backtest Analyzer

A lightweight Python command-line tool for analyzing trading results from a
CSV file. It calculates performance, risk, drawdown, streaks, and results by
day, ISO week, and month.

This is a public portfolio project. The included dataset is fictional and does
not expose any proprietary trading strategy, parameters, or real account data.

## Features

- Net profit, gross profit, and gross loss
- Win rate and trade counts
- Profit factor and payoff ratio
- Average trade, average win, and average loss
- Maximum absolute and percentage drawdown
- Longest winning and losing streaks
- Best and worst trades
- Daily, weekly, and monthly results
- Input validation with readable error messages
- Terminal summary and optional JSON report
- Automated tests using Python's standard library

## Requirements

- Python 3.10 or newer
- No third-party runtime packages

## Quick start

Clone the repository and enter its directory:

```bash
git clone https://github.com/MurilloMarcos13/gold-backtest-analyzer.git
cd gold-backtest-analyzer
```

Run the analyzer with the fictional sample data:

```bash
python analyzer.py sample_data/trades_example.csv
```

Choose an initial balance and generate a complete JSON report:

```bash
python analyzer.py sample_data/trades_example.csv \
  --initial-balance 10000 \
  --output reports/sample_report.json
```

Example terminal output:

```text
Gold Backtest Analyzer
========================================
Initial balance              10000.0
Final balance                10230.0
Net profit                   230.0
Total trades                 12
Win rate (%)                 58.33
Profit factor                2.61
Payoff ratio                 1.86
Maximum drawdown             58.0
Maximum drawdown (%)         0.57
Longest winning streak       2
Longest losing streak        2
```

## CSV format

The first row must contain these column names:

| Column | Description | Example |
|---|---|---|
| `trade_id` | Unique trade identifier | `T001` |
| `open_time` | Opening date and time | `2026-01-05 14:00:00` |
| `close_time` | Closing date and time | `2026-01-05 14:24:00` |
| `symbol` | Traded instrument | `XAUUSD` |
| `side` | Trade direction | `BUY` or `SELL` |
| `volume` | Position volume | `0.01` |
| `entry_price` | Entry price | `2620.10` |
| `exit_price` | Exit price | `2624.30` |
| `profit` | Final monetary result | `42.00` or `-25.00` |

Dates use an ISO-compatible format. Trades are automatically sorted by their
closing time before the calculations are performed.

## Run the tests

```bash
python -m unittest discover -s tests -v
```

## Project structure

```text
gold-backtest-analyzer/
├── analyzer.py
├── requirements.txt
├── sample_data/
│   └── trades_example.csv
├── tests/
│   └── test_analyzer.py
└── reports/
    └── sample_report.json
```

## How the main metrics are calculated

- **Net profit:** sum of all trade results.
- **Profit factor:** gross profit divided by the absolute gross loss.
- **Win rate:** winning trades divided by all trades.
- **Payoff ratio:** average win divided by the absolute average loss.
- **Drawdown:** largest decline from a previous balance peak.
- **Streak:** largest uninterrupted sequence of wins or losses.

## Roadmap

- Import MetaTrader 5 HTML and Excel reports
- Create equity and drawdown charts
- Add configurable risk-of-ruin simulations
- Generate an HTML dashboard
- Compare multiple backtests

## License

Released under the [MIT License](LICENSE).
