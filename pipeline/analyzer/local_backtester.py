from __future__ import annotations

import ast
from dataclasses import asdict
import logging
import math
from pathlib import Path
from statistics import mean
from typing import Any

from backtesting import Backtest, Strategy
import numpy as np
import pandas as pd
import yfinance as yf

from pipeline.models import AlphaCandidate, PreBacktestMetrics, PreBacktestResult
from pipeline.workflow_tracker import match_theory_ids, parse_expression_features


LOGGER = logging.getLogger(__name__)


class ProxySignalStrategy(Strategy):
    upper: float = 0.6
    lower: float = 0.4

    def init(self) -> None:
        pass

    def next(self) -> None:
        value = float(self.data.Signal[-1])
        if np.isnan(value):
            return
        if value >= self.upper:
            if self.position.is_short:
                self.position.close()
            if not self.position.is_long:
                self.buy()
        elif value <= self.lower:
            if self.position.is_long:
                self.position.close()
            if not self.position.is_short:
                self.sell()


class ExpressionSeriesEvaluator:
    def __init__(self, frame: pd.DataFrame, *, rank_window: int = 63, zscore_window: int = 20) -> None:
        self.frame = frame.copy()
        self.rank_window = max(rank_window, 5)
        self.zscore_window = max(zscore_window, 5)
        self.namespace: dict[str, pd.Series] = {
            "close": self.frame["Close"].astype(float),
            "volume": self.frame["Volume"].astype(float),
            "vwap": ((self.frame["High"] + self.frame["Low"] + self.frame["Close"]) / 3.0).astype(float),
        }
        self.namespace["returns"] = self.namespace["close"].pct_change().fillna(0.0)

    def evaluate(self, expression: str) -> pd.Series:
        tree = ast.parse(expression, mode="eval")
        result = self._eval(tree.body)
        if isinstance(result, pd.Series):
            return result.replace([np.inf, -np.inf], np.nan)
        return pd.Series(float(result), index=self.frame.index, dtype=float)

    def _eval(self, node: ast.AST) -> pd.Series | float:
        if isinstance(node, ast.Name):
            key = node.id.lower()
            if key not in self.namespace:
                raise ValueError(f"Unsupported field '{node.id}' in local backtest evaluator.")
            return self.namespace[key]
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            value = self._eval(node.operand)
            return -value
        if isinstance(node, ast.BinOp):
            left = self._eval(node.left)
            right = self._eval(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            raise ValueError(f"Unsupported binary operator '{type(node.op).__name__}'.")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            func = node.func.id.lower()
            args = [self._eval(arg) for arg in node.args]
            if func == "rank":
                return self._rolling_rank(self._coerce_series(args[0]))
            if func == "ts_mean":
                return self._coerce_series(args[0]).rolling(self._coerce_int(args[1])).mean()
            if func == "ts_delta":
                return self._coerce_series(args[0]).diff(self._coerce_int(args[1]))
            if func == "ts_std_dev":
                return self._coerce_series(args[0]).rolling(self._coerce_int(args[1])).std(ddof=0)
            if func == "ts_corr":
                return self._coerce_series(args[0]).rolling(self._coerce_int(args[2])).corr(self._coerce_series(args[1]))
            if func == "zscore":
                series = self._coerce_series(args[0])
                window = self._coerce_int(args[1]) if len(args) > 1 else self.zscore_window
                rolling_std = series.rolling(window).std(ddof=0).replace(0.0, np.nan)
                return (series - series.rolling(window).mean()) / rolling_std
            raise ValueError(f"Unsupported function '{node.func.id}' in local backtest evaluator.")
        raise ValueError(f"Unsupported expression node '{type(node).__name__}'.")

    def _rolling_rank(self, series: pd.Series) -> pd.Series:
        return series.rolling(self.rank_window).apply(_percent_rank_last, raw=True)

    def _coerce_series(self, value: pd.Series | float) -> pd.Series:
        if isinstance(value, pd.Series):
            return value.astype(float)
        return pd.Series(float(value), index=self.frame.index, dtype=float)

    @staticmethod
    def _coerce_int(value: pd.Series | float) -> int:
        if isinstance(value, pd.Series):
            raise ValueError("Window argument cannot be a series.")
        return max(int(value), 1)


class LocalBacktester:
    def __init__(
        self,
        cache_dir: Path,
        *,
        settings: dict[str, Any] | None = None,
        quality_thresholds: dict[str, float] | None = None,
    ) -> None:
        cfg = settings or {}
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.quality_thresholds = quality_thresholds or {}
        self.start = str(cfg.get("start", "2019-01-01"))
        self.interval = str(cfg.get("interval", "1d"))
        self.cash = float(cfg.get("cash", 10000))
        self.commission = float(cfg.get("commission", 0.002))
        self.rank_window = int(cfg.get("rank_window", 63))
        self.zscore_window = int(cfg.get("zscore_window", 20))
        self.min_score = float(cfg.get("min_score", 0.52))
        self.min_sharpe = float(cfg.get("min_sharpe", 0.2))
        self.min_fitness = float(cfg.get("min_fitness", 0.15))
        self.min_returns = float(cfg.get("min_returns", 0.01))
        self.max_drawdown = float(cfg.get("max_drawdown", 0.35))
        self.max_self_correlation = float(cfg.get("max_self_correlation", self.quality_thresholds.get("self_correlation_max", 0.7)))
        self.max_live_candidates = int(cfg.get("max_live_candidates", 6))
        self.upper_signal = float(cfg.get("upper_signal", 0.6))
        self.lower_signal = float(cfg.get("lower_signal", 0.4))
        self.min_symbol_coverage = int(cfg.get("min_symbol_coverage", 2))
        self.symbols_by_strategy = cfg.get(
            "symbols",
            {
                "momentum": ["SPY", "QQQ", "IWM"],
                "mean_reversion": ["SPY", "DIA", "QQQ"],
                "volume": ["SPY", "IWM", "XLF", "XLK"],
                "default": ["SPY", "QQQ", "IWM"],
            },
        )

    def rank_candidates(
        self,
        candidates: list[AlphaCandidate],
        history: list[dict[str, Any]],
        *,
        max_promoted: int | None = None,
    ) -> tuple[list[tuple[AlphaCandidate, PreBacktestResult]], list[tuple[AlphaCandidate, PreBacktestResult]]]:
        promoted_cap = max(1, int(max_promoted or self.max_live_candidates))
        scored = [(candidate, self.evaluate(candidate, history)) for candidate in candidates]
        passing = [(candidate, result) for candidate, result in scored if result.passed]
        passing.sort(key=lambda item: item[1].score, reverse=True)
        blocked = [(candidate, result) for candidate, result in scored if not result.passed]
        promoted: list[tuple[AlphaCandidate, PreBacktestResult]] = []
        for index, (candidate, result) in enumerate(passing):
            if index < promoted_cap:
                result.promoted = True
                promoted.append((candidate, result))
            else:
                result.reasons.append(
                    f"Local backtest passed with score {result.score:.2f}, but higher-scoring candidates filled the live simulation quota."
                )
                blocked.append((candidate, result))
        blocked.sort(key=lambda item: item[1].score, reverse=True)
        return promoted, blocked

    def evaluate(self, candidate: AlphaCandidate, history: list[dict[str, Any]]) -> PreBacktestResult:
        symbols = self._symbols_for_strategy(candidate.strategy_type)
        runs: list[dict[str, Any]] = []
        failures: list[str] = []
        highest_similarity = self._highest_similarity(candidate.expression, history)
        theory_ids = match_theory_ids(candidate.expression)
        features = parse_expression_features(candidate.expression)

        for symbol in symbols:
            try:
                frame = self._load_symbol_frame(symbol)
                if frame is None or len(frame) < 180:
                    failures.append(f"{symbol}: not enough cached market data")
                    continue
                signal = self._signal_for_expression(candidate.expression, frame)
                stats = self._run_backtest(frame, signal)
                if stats is None:
                    failures.append(f"{symbol}: signal did not produce enough trades")
                    continue
                runs.append({"symbol": symbol, **stats})
            except Exception as exc:
                LOGGER.warning("Local backtest failed for symbol=%s expression=%s error=%s", symbol, candidate.expression, exc)
                failures.append(f"{symbol}: {exc}")

        coverage = len(runs)
        if coverage:
            sharpe = mean(run["sharpe"] for run in runs)
            annual_returns = mean(run["annual_returns"] for run in runs)
            drawdown = mean(run["drawdown"] for run in runs)
            turnover = min(1.0, mean(run["turnover"] for run in runs))
        else:
            sharpe = 0.0
            annual_returns = 0.0
            drawdown = 1.0
            turnover = 1.0

        fitness = self._fitness_proxy(sharpe, annual_returns, turnover)
        metrics = PreBacktestMetrics(
            sharpe=round(sharpe, 4),
            fitness=round(fitness, 4),
            annual_returns=round(annual_returns, 4),
            turnover=round(turnover, 4),
            drawdown=round(drawdown, 4),
            self_correlation=round(highest_similarity, 4),
        )
        score = self._score(metrics, coverage=coverage, total_symbols=len(symbols))
        reasons: list[str] = []
        if coverage < self.min_symbol_coverage:
            reasons.append(f"Only {coverage}/{len(symbols)} proxy markets produced valid backtests.")
        if metrics.sharpe < self.min_sharpe:
            reasons.append(f"Proxy Sharpe {metrics.sharpe:.2f} < local threshold {self.min_sharpe:.2f}.")
        if metrics.fitness < self.min_fitness:
            reasons.append(f"Proxy fitness {metrics.fitness:.2f} < local threshold {self.min_fitness:.2f}.")
        if metrics.annual_returns < self.min_returns:
            reasons.append(f"Proxy annual return {metrics.annual_returns:.2%} < local threshold {self.min_returns:.2%}.")
        if metrics.drawdown > self.max_drawdown:
            reasons.append(f"Proxy drawdown {metrics.drawdown:.2%} > local maximum {self.max_drawdown:.2%}.")
        if metrics.self_correlation > self.max_self_correlation:
            reasons.append(
                f"Expression similarity {metrics.self_correlation:.2f} > local novelty cap {self.max_self_correlation:.2f}."
            )
        if score < self.min_score:
            reasons.append(f"Composite local backtest score {score:.2f} < promote threshold {self.min_score:.2f}.")

        evidence = [
            f"Proxy symbols used: {', '.join(run['symbol'] for run in runs) if runs else 'none'}.",
            f"Theme: {features['theme']}.",
        ]
        if theory_ids:
            evidence.append(f"Theory matches: {', '.join(theory_ids)}.")
        if runs:
            evidence.extend(
                f"{run['symbol']}: Sharpe {run['sharpe']:.2f}, Return {run['annual_returns']:.2%}, Drawdown {run['drawdown']:.2%}, Trades/year {run['trades_per_year']:.1f}."
                for run in runs[:4]
            )
        if failures:
            evidence.append(f"Proxy backtest misses: {'; '.join(failures[:3])}.")

        return PreBacktestResult(
            passed=not reasons,
            promoted=False,
            score=round(score, 4),
            confidence=round(min(1.0, coverage / max(len(symbols), 1)), 4),
            reasons=reasons,
            evidence=evidence,
            theory_ids=theory_ids,
            analogs=runs[:6],
            highest_similarity=round(highest_similarity, 4),
            estimated_metrics=metrics,
        )

    def as_payload(self, result: PreBacktestResult) -> dict[str, Any]:
        payload = asdict(result)
        payload["estimated_metrics"] = asdict(result.estimated_metrics)
        return payload

    def _symbols_for_strategy(self, strategy_type: str) -> list[str]:
        strategy_key = str(strategy_type or "").lower()
        return list(self.symbols_by_strategy.get(strategy_key, self.symbols_by_strategy.get("default", ["SPY", "QQQ", "IWM"])))

    def _load_symbol_frame(self, symbol: str) -> pd.DataFrame | None:
        cache_path = self.cache_dir / f"{symbol}_{self.interval}.csv"
        frame: pd.DataFrame | None = None
        if cache_path.exists():
            try:
                frame = pd.read_csv(cache_path, header=[0, 1], index_col=0, parse_dates=True)
            except Exception:
                try:
                    frame = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                except Exception:
                    frame = None
        if frame is None or frame.empty:
            downloaded = yf.download(symbol, start=self.start, interval=self.interval, auto_adjust=False, progress=False, threads=False)
            if downloaded is None or downloaded.empty:
                return None
            frame = self._normalize_price_frame(downloaded)
            frame.to_csv(cache_path)
        else:
            frame = self._normalize_price_frame(frame)
        required = ["Open", "High", "Low", "Close", "Volume"]
        if any(column not in frame.columns for column in required):
            return None
        return frame[required].dropna().copy()

    @staticmethod
    def _normalize_price_frame(frame: pd.DataFrame) -> pd.DataFrame:
        normalized = frame.copy()
        if isinstance(normalized.columns, pd.MultiIndex):
            normalized.columns = [str(column[0]).title() for column in normalized.columns]
        else:
            normalized.columns = [str(column).title() for column in normalized.columns]
        normalized = normalized.loc[~normalized.index.astype(str).isin(["Ticker", "Date"])]
        return normalized

    def _signal_for_expression(self, expression: str, frame: pd.DataFrame) -> pd.Series:
        lookback = self._extract_max_lookback(expression)
        evaluator = ExpressionSeriesEvaluator(
            frame,
            rank_window=max(self.rank_window, lookback * 3),
            zscore_window=max(self.zscore_window, lookback),
        )
        raw_signal = evaluator.evaluate(expression)
        normalized = raw_signal.rolling(max(self.rank_window, lookback * 3)).apply(_percent_rank_last, raw=True)
        return normalized.clip(lower=0.0, upper=1.0)

    def _run_backtest(self, frame: pd.DataFrame, signal: pd.Series) -> dict[str, Any] | None:
        data = frame.copy()
        data["Signal"] = signal
        data = data.dropna()
        if len(data) < 180:
            return None

        strategy_cls = type(
            "BoundProxySignalStrategy",
            (ProxySignalStrategy,),
            {"upper": self.upper_signal, "lower": self.lower_signal},
        )
        stats = Backtest(
            data,
            strategy_cls,
            cash=self.cash,
            commission=self.commission,
            exclusive_orders=True,
            trade_on_close=True,
            finalize_trades=True,
        ).run()
        trades = float(stats.get("# Trades", 0) or 0.0)
        exposure = float(stats.get("Exposure Time [%]", 0.0) or 0.0)
        if trades <= 0 and exposure <= 0:
            return None
        duration_days = max((data.index[-1] - data.index[0]).days, 1)
        years = max(duration_days / 365.25, 0.25)
        trades_per_year = trades / years
        turnover = min(1.0, trades_per_year / 40.0)
        return {
            "sharpe": float(stats.get("Sharpe Ratio", 0.0) or 0.0),
            "annual_returns": float(stats.get("Return (Ann.) [%]", 0.0) or 0.0) / 100.0,
            "drawdown": abs(float(stats.get("Max. Drawdown [%]", 0.0) or 0.0)) / 100.0,
            "turnover": turnover,
            "trades": trades,
            "trades_per_year": trades_per_year,
        }

    def _score(self, metrics: PreBacktestMetrics, *, coverage: int, total_symbols: int) -> float:
        sharpe_score = _clamp((metrics.sharpe + 0.25) / 1.75)
        fitness_score = _clamp((metrics.fitness + 0.1) / 1.4)
        returns_score = _clamp((metrics.annual_returns + 0.02) / 0.18)
        drawdown_score = _clamp(1.0 - (metrics.drawdown / max(self.max_drawdown, 0.05)))
        turnover_mid = (self.quality_thresholds.get("turnover_min", 0.01) + self.quality_thresholds.get("turnover_max", 0.7)) / 2.0
        turnover_score = _clamp(1.0 - abs(metrics.turnover - turnover_mid) / max(turnover_mid, 0.15))
        novelty_score = _clamp(1.0 - metrics.self_correlation)
        coverage_score = _clamp(coverage / max(total_symbols, 1))
        return (
            sharpe_score * 0.24
            + fitness_score * 0.2
            + returns_score * 0.14
            + drawdown_score * 0.14
            + turnover_score * 0.1
            + novelty_score * 0.1
            + coverage_score * 0.08
        )

    @staticmethod
    def _fitness_proxy(sharpe: float, annual_returns: float, turnover: float) -> float:
        if turnover <= 0:
            turnover = 0.125
        magnitude = math.sqrt(abs(annual_returns) / max(turnover, 0.125)) if annual_returns != 0 else 0.0
        fitness = magnitude * sharpe
        return -abs(fitness) if annual_returns < 0 else fitness

    @staticmethod
    def _highest_similarity(expression: str, history: list[dict[str, Any]]) -> float:
        target = set(_tokenize_expression(expression))
        if not target:
            return 0.0
        highest = 0.0
        for item in history:
            other_expression = str(item.get("expression") or "")
            if not other_expression:
                continue
            other = set(_tokenize_expression(other_expression))
            union = target | other
            if not union:
                continue
            highest = max(highest, len(target & other) / len(union))
        return highest

    @staticmethod
    def _extract_max_lookback(expression: str) -> int:
        digits = [int(token) for token in _tokenize_expression(expression) if token.isdigit()]
        usable = [value for value in digits if 1 <= value <= 252]
        return max(usable) if usable else 20


def _percent_rank_last(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0 or np.isnan(arr[-1]):
        return np.nan
    valid = arr[~np.isnan(arr)]
    if valid.size == 0:
        return np.nan
    return float((valid <= arr[-1]).mean())


def _tokenize_expression(expression: str) -> list[str]:
    token = ""
    items: list[str] = []
    for char in str(expression or ""):
        if char.isalnum() or char in {"_", "."}:
            token += char
            continue
        if token:
            items.append(token.lower())
            token = ""
    if token:
        items.append(token.lower())
    return items


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))
