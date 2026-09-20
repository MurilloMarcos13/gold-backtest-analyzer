"""Analyze trading results stored in a CSV file.

The project intentionally uses only Python's standard library at runtime so it
is easy to study, run, and extend.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


REQUIRED_COLUMNS = {
    "trade_id",
    "open_time",
    "close_time",
    "symbol",
    "side",
    "volume",
    "entry_price",
    "exit_price",
    "profit",
}


@dataclass(frozen=True)
class Trade:
    """A normalized trade loaded from the input CSV file."""

    trade_id: str
    open_time: datetime
    close_time: datetime
    symbol: str
    side: str
    volume: float
    entry_price: float
    exit_price: float
    profit: float


def parse_datetime(value: str) -> datetime:
    """Parse an ISO-like date and raise a readable error when it is invalid."""

    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid date/time: {value!r}") from exc


def load_trades(csv_path: str | Path) -> list[Trade]:
    """Load, validate, and sort trades by closing time."""

    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    trades: list[Trade] = []
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(f"Missing required CSV columns: {missing_list}")

        for line_number, row in enumerate(reader, start=2):
            try:
                trade = Trade(
                    trade_id=row["trade_id"].strip(),
                    open_time=parse_datetime(row["open_time"]),
                    close_time=parse_datetime(row["close_time"]),
                    symbol=row["symbol"].strip().upper(),
                    side=row["side"].strip().upper(),
                    volume=float(row["volume"]),
                    entry_price=float(row["entry_price"]),
                    exit_price=float(row["exit_price"]),
                    profit=float(row["profit"]),
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid data on CSV line {line_number}: {exc}") from exc

            if not trade.trade_id:
                raise ValueError(f"Invalid data on CSV line {line_number}: empty trade_id")
            if trade.side not in {"BUY", "SELL"}:
                raise ValueError(
                    f"Invalid data on CSV line {line_number}: side must be BUY or SELL"
                )
            if trade.volume <= 0:
                raise ValueError(
                    f"Invalid data on CSV line {line_number}: volume must be positive"
                )
            if trade.close_time < trade.open_time:
                raise ValueError(
                    f"Invalid data on CSV line {line_number}: close_time precedes open_time"
                )

            trades.append(trade)

    if not trades:
        raise ValueError("The CSV file contains no trades")

    return sorted(trades, key=lambda trade: trade.close_time)


def longest_streak(profits: Iterable[float], *, winning: bool) -> int:
    """Return the longest consecutive winning or losing streak."""

    longest = 0
    current = 0
    for profit in profits:
        matches = profit > 0 if winning else profit < 0
        if matches:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def calculate_drawdown(
    trades: Iterable[Trade], initial_balance: float
) -> tuple[float, float]:
    """Return maximum absolute and percentage drawdown of the balance curve."""

    balance = initial_balance
    peak = initial_balance
    max_drawdown = 0.0
    max_drawdown_percent = 0.0

    for trade in trades:
        balance += trade.profit
        peak = max(peak, balance)
        drawdown = peak - balance
        drawdown_percent = (drawdown / peak * 100) if peak > 0 else 0.0
        max_drawdown = max(max_drawdown, drawdown)
        max_drawdown_percent = max(max_drawdown_percent, drawdown_percent)

    return max_drawdown, max_drawdown_percent


def group_results(trades: Iterable[Trade], period: str) -> dict[str, float]:
    """Aggregate profit by day, ISO week, or month."""

    grouped: dict[str, float] = {}
    for trade in trades:
        close_time = trade.close_time
        if period == "daily":
            key = close_time.date().isoformat()
        elif period == "weekly":
            iso_year, iso_week, _ = close_time.isocalendar()
            key = f"{iso_year}-W{iso_week:02d}"
        elif period == "monthly":
            key = close_time.strftime("%Y-%m")
        else:
            raise ValueError(f"Unsupported period: {period}")
        grouped[key] = grouped.get(key, 0.0) + trade.profit

    return {key: round(value, 2) for key, value in sorted(grouped.items())}


def trade_summary(trade: Trade) -> dict[str, str | float]:
    """Return the public fields used for best/worst trade summaries."""

    return {
        "trade_id": trade.trade_id,
        "close_time": trade.close_time.isoformat(),
        "symbol": trade.symbol,
        "side": trade.side,
        "profit": round(trade.profit, 2),
    }


def analyze_trades(trades: list[Trade], initial_balance: float = 10_000.0) -> dict:
    """Calculate performance and risk statistics for a list of trades."""

    if initial_balance <= 0:
        raise ValueError("initial_balance must be greater than zero")
    if not trades:
        raise ValueError("At least one trade is required")

    profits = [trade.profit for trade in trades]
    wins = [profit for profit in profits if profit > 0]
    losses = [profit for profit in profits if profit < 0]
    breakeven_count = sum(profit == 0 for profit in profits)

    gross_profit = sum(wins)
    gross_loss = sum(losses)
    net_profit = sum(profits)
    average_win = gross_profit / len(wins) if wins else 0.0
    average_loss = gross_loss / len(losses) if losses else 0.0
    profit_factor = gross_profit / abs(gross_loss) if gross_loss else math.inf
    payoff_ratio = average_win / abs(average_loss) if average_loss else math.inf
    max_drawdown, max_drawdown_percent = calculate_drawdown(trades, initial_balance)

    best_trade = max(trades, key=lambda trade: trade.profit)
    worst_trade = min(trades, key=lambda trade: trade.profit)

    def rounded_or_string(value: float) -> float | str:
        return "Infinity" if math.isinf(value) else round(value, 2)

    return {
        "summary": {
            "initial_balance": round(initial_balance, 2),
            "final_balance": round(initial_balance + net_profit, 2),
            "net_profit": round(net_profit, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(gross_loss, 2),
            "total_trades": len(trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "breakeven_trades": breakeven_count,
            "win_rate_percent": round(len(wins) / len(trades) * 100, 2),
            "profit_factor": rounded_or_string(profit_factor),
            "average_trade": round(net_profit / len(trades), 2),
            "average_win": round(average_win, 2),
            "average_loss": round(average_loss, 2),
            "payoff_ratio": rounded_or_string(payoff_ratio),
            "max_drawdown": round(max_drawdown, 2),
            "max_drawdown_percent": round(max_drawdown_percent, 2),
            "longest_winning_streak": longest_streak(profits, winning=True),
            "longest_losing_streak": longest_streak(profits, winning=False),
        },
        "best_trade": trade_summary(best_trade),
        "worst_trade": trade_summary(worst_trade),
        "daily_results": group_results(trades, "daily"),
        "weekly_results": group_results(trades, "weekly"),
        "monthly_results": group_results(trades, "monthly"),
    }


def print_summary(analysis: dict) -> None:
    """Print the main metrics in a readable terminal report."""

    summary = analysis["summary"]
    labels = {
        "initial_balance": "Initial balance",
        "final_balance": "Final balance",
        "net_profit": "Net profit",
        "total_trades": "Total trades",
        "win_rate_percent": "Win rate (%)",
        "profit_factor": "Profit factor",
        "payoff_ratio": "Payoff ratio",
        "max_drawdown": "Maximum drawdown",
        "max_drawdown_percent": "Maximum drawdown (%)",
        "longest_winning_streak": "Longest winning streak",
        "longest_losing_streak": "Longest losing streak",
    }

    print("\nGold Backtest Analyzer")
    print("=" * 40)
    for key, label in labels.items():
        print(f"{label:<28} {summary[key]}")


def save_json_report(analysis: dict, output_path: str | Path) -> None:
    """Save a complete analysis as formatted JSON."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze trading performance from a CSV export."
    )
    parser.add_argument("csv_file", help="Path to the trades CSV file")
    parser.add_argument(
        "--initial-balance",
        type=float,
        default=10_000.0,
        help="Starting account balance (default: 10000)",
    )
    parser.add_argument("--output", help="Optional path for the JSON report")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    trades = load_trades(args.csv_file)
    analysis = analyze_trades(trades, args.initial_balance)
    print_summary(analysis)

    if args.output:
        save_json_report(analysis, args.output)
        print(f"\nJSON report saved to: {args.output}")


if __name__ == "__main__":
    main()
