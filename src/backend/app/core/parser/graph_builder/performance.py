import time
from collections import defaultdict
import statistics
from typing import Dict, List, Any


class PerformanceTracker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PerformanceTracker, cls).__new__(cls)
            cls._instance.reset()
        return cls._instance

    def reset(self):
        self.metrics: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, float] = {}
        # For nested or concurrent timers, we might need a unique ID, but for
        # simple blocks a unique key per operation type is okay if we just
        # want average of that operation type.
        # If we want to time a specific block that can be re-entered
        # recursively or concurrently, we need to be careful.
        # For async concurrent tasks, we can't use a single self.timers dict
        # keyed by operation name if multiple tasks update it.
        # We will return a context manager or handle concurrency by just
        # measuring elapsed time locally and calling record_metric.

    def record_metric(self, key: str, value: float):
        self.metrics[key].append(value)

    def get_report(self) -> Dict[str, Any]:
        report = {}
        for key, values in self.metrics.items():
            if values:
                report[key] = {
                    "count": len(values),
                    "total_time": sum(values),
                    "avg_time": statistics.mean(values),
                    "min_time": min(values),
                    "max_time": max(values)
                }
        return report

    def print_report(self):
        print("\n--- Performance Report ---")
        report = self.get_report()
        # Sort by total time descending
        sorted_items = sorted(
            report.items(), key=lambda x: x[1]['total_time'], reverse=True)

        # Header
        print(
            f"{'Name':<40} {'Count':>8} {'Total (s)':>10} "
            f"{'Avg (s)':>10} {'Min (s)':>10} {'Max (s)':>10}"
        )
        print("-" * 92)

        for key, stats in sorted_items:
            print(
                f"{key:<40} {stats['count']:>8} "
                f"{stats['total_time']:>10.4f} {stats['avg_time']:>10.4f} "
                f"{stats['min_time']:>10.4f} {stats['max_time']:>10.4f}"
            )
        print("-" * 92 + "\n")

    def timer(self, key: str):
        return PerformanceTimer(self, key)


class PerformanceTimer:
    def __init__(self, tracker: PerformanceTracker, key: str):
        self.tracker = tracker
        self.key = key
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.tracker.record_metric(self.key, duration)


tracker = PerformanceTracker()
