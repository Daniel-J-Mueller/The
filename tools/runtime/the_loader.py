#!/usr/bin/env python3
"""Minimal hot-path loader for source-validated or explicitly trusted assets."""

import marshal
import os
import sys

MAGIC = b"THEBC001"


def render(value):
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return format(value, ".15g")
    if isinstance(value, list):
        return "[" + ", ".join(render(item) for item in value) + "]"
    return str(value)


def stride(first, last, step):
    if step == 0:
        raise ValueError("stride step cannot be zero")
    step = abs(step) * (1 if last >= first else -1)
    if step > 0:
        while first <= last:
            yield first
            first += step
    else:
        while first >= last:
            yield first
            first += step


def intthrough(first, last):
    step = 1 if last >= first else -1
    return range(first, last + step, step)


def execute_asset(asset, expected_hash=None):
    try:
        with open(asset, "rb") as handle:
            payload = handle.read()
        if payload[:8] != MAGIC or payload[8:10] != bytes(sys.version_info[:2]):
            return False
        if expected_hash is not None and payload[10:42] != expected_hash:
            return False
        exec(marshal.loads(payload[42:]), {
            "_render": render, "_stride": stride, "_intthrough": intthrough,
        })
        return True
    except (OSError, EOFError, TypeError, ValueError):
        return False


def try_source_asset(source):
    from hashlib import sha256

    try:
        with open(source, "rb") as handle:
            source_hash = sha256(handle.read()).digest()
    except OSError:
        return False
    return execute_asset(os.path.splitext(source)[0] + ".then", source_hash)


def main():
    if len(sys.argv) != 2 or not sys.argv[1].endswith((".the", ".then")):
        print("usage: the FILE.the | FILE.then", file=sys.stderr)
        return 2
    target = sys.argv[1]
    if target.endswith(".then"):
        if execute_asset(target):
            return 0
        print("the: incompatible or invalid .then asset", file=sys.stderr)
        return 1
    if try_source_asset(target):
        return 0
    from the_runtime import main as runtime_main
    return runtime_main(["run", target])


if __name__ == "__main__":
    raise SystemExit(main())
