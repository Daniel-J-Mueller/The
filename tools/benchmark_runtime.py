#!/usr/bin/env python3
"""Compare The execution paths with an equivalent Python program."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "tools" / "runtime" / "the_runtime.py"
LOADER = ROOT / "tools" / "runtime" / "the_loader.py"
NATIVE = ROOT / "tools" / "runtime" / "the_native.py"
WORKLOADS = {
    "startup": (
        ROOT / "benchmarks" / "runtime" / "numeric_loop.the",
        ROOT / "benchmarks" / "runtime" / "numeric_loop.py",
        "inclusive sum from 1 through 10,000",
    ),
    "throughput": (
        ROOT / "benchmarks" / "runtime" / "numeric_loop_large.the",
        ROOT / "benchmarks" / "runtime" / "numeric_loop_large.py",
        "inclusive sum from 1 through 5,000,000",
    ),
}


def measure(command: list[str], samples: int, cwd: Path) -> dict[str, float]:
    timings = []
    for _ in range(samples):
        started = time.perf_counter_ns()
        subprocess.run(command, cwd=cwd, stdout=subprocess.DEVNULL,
                       stderr=subprocess.PIPE, check=True)
        timings.append((time.perf_counter_ns() - started) / 1_000_000)
    timings.sort()
    return {
        "median_ms": round(statistics.median(timings), 3),
        "min_ms": round(timings[0], 3),
        "max_ms": round(timings[-1], 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=11)
    parser.add_argument("--workload", choices=WORKLOADS, default="startup")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--csv", type=Path, help="append result points to a CSV file")
    parser.add_argument("--version", default="working", help="optimization checkpoint ID")
    parser.add_argument("--note", default="", help="cause or purpose of this checkpoint")
    args = parser.parse_args()
    if args.samples < 3:
        parser.error("--samples must be at least 3")
    the_source, python_source, workload_name = WORKLOADS[args.workload]

    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        source = work / "compiled" / the_source.name
        source.parent.mkdir()
        shutil.copyfile(the_source, source)
        source_only = work / "source" / the_source.name
        source_only.parent.mkdir()
        shutil.copyfile(the_source, source_only)
        compile_command = [sys.executable, str(RUNTIME), "compile", str(source)]
        subprocess.run(compile_command, stdout=subprocess.DEVNULL, check=True)

        commands = {
            "python": [sys.executable, "-S", str(python_source)],
            "then-raw": [sys.executable, "-S", str(LOADER), str(source.with_suffix(".then"))],
            "the-loader": [sys.executable, "-S", str(LOADER), str(source)],
            "the-precompiled": [sys.executable, str(RUNTIME), "run", str(source)],
            "the-source": [sys.executable, str(RUNTIME), "run", str(source_only)],
            "the-compile": compile_command,
        }
        native = ROOT / "benchmarks" / "results" / "numeric_loop_native.exe"
        if args.workload == "throughput" and native.exists():
            commands["native-c-o2"] = [str(native), "5000000"]
        the_native = ROOT / "benchmarks" / "results" / "numeric_loop_the_native.exe"
        if args.workload == "throughput" and the_native.exists():
            commands["the-native-aot"] = [str(the_native)]
        results = {name: measure(command, args.samples, ROOT)
                   for name, command in commands.items()}

    baseline = results["python"]["median_ms"]
    for result in results.values():
        result["vs_python"] = round(result["median_ms"] / baseline, 2)
    report = {
        "platform": platform.platform(),
        "processor": platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
        "python": sys.version.split()[0],
        "samples": args.samples,
        "workload": workload_name,
        "results": results,
    }
    if args.csv:
        destination = args.csv if args.csv.is_absolute() else ROOT / args.csv
        destination.parent.mkdir(parents=True, exist_ok=True)
        fields = ["timestamp_utc", "version", "path", "median_ms", "min_ms",
                  "max_ms", "vs_python", "samples", "python", "platform",
                  "processor", "workload", "note"]
        exists = destination.exists() and destination.stat().st_size > 0
        with destination.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            if not exists:
                writer.writeheader()
            timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
            for name, result in results.items():
                writer.writerow({
                    "timestamp_utc": timestamp, "version": args.version,
                    "path": name, **result, "samples": args.samples,
                    "python": report["python"], "platform": report["platform"],
                    "processor": report["processor"], "workload": report["workload"],
                    "note": args.note,
                })
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{report['platform']} | Python {report['python']} | {args.samples} samples")
        print(f"{'path':<18} {'median ms':>10} {'min ms':>10} {'vs Python':>10}")
        for name, result in results.items():
            print(f"{name:<18} {result['median_ms']:>10.3f} "
                  f"{result['min_ms']:>10.3f} {result['vs_python']:>9.2f}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
