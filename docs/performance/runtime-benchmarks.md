# Runtime benchmarks

The benchmark compares equivalent programs that sum the inclusive integers from
1 through 10,000 and print the result once. Each sample launches a fresh process,
so the results include startup and execution. Compilation is measured separately.

Run it from the repository root:

```text
python tools/benchmark_runtime.py --samples 11 \
  --csv benchmarks/results/runtime.csv \
  --version v0.3 \
  --note "Lower cache-miss source directly to host bytecode"
```

Each CSV row is one plotted point and records the timestamp, optimization
version, execution path, distribution bounds, Python-relative time, sample
count, host details, workload, and the reason for the experiment. Use a new
version ID when behavior or implementation changes; repeated runs of the same
version intentionally remain separate points rather than overwriting history.
Use `--workload throughput` for a five-million-iteration companion workload
that makes generated-code throughput larger than process startup.

## Optimization versions

Measurements below were taken July 14, 2026, on Windows 11 with CPython 3.14.4.
Times are subprocess wall-clock medians; lower is better. These are development
checkpoints rather than language or container-format versions.

Versions through v0.3 used a module-scope Python reference. The `v0.3-fair`
checkpoint moves Python into an equivalent function and matches the generated
assignment form. Use fair-suffixed points for cross-language conclusions; the
older points remain useful for comparing The versions with one another.

| Optimization version | Main change | Source median | Source vs Python | Loader median | Loader vs Python |
|---|---|---:|---:|---:|---:|
| v0.1 | Lazy interpreted strides | 338.395 ms | 13.57x | 37.820 ms | 1.52x |
| v0.2 | Cached validated expressions; C-level integer ranges | 135.247 ms | 5.93x | 32.670 ms | 1.43x |
| v0.3 | Lower cache-miss source to host bytecode | 117.355 ms | 5.10x | 32.682 ms | 1.42x |
| v0.3-fair | Correct equivalent Python function | 120.172 ms | 5.22x | 33.674 ms | 1.46x |

The v0.2 source path takes 40.0% of the v0.1 time, a 60.0% reduction and 2.50x
speedup. Because these
runs used 7 and 11 samples respectively, rerun the benchmark for decisions that
need tighter statistical confidence.

The v0.3 source path is 13.2% faster than v0.2. Its 117.355 ms median is within
0.3% of the full runtime's precompiled path, indicating that process and compiler
startup now dominate this small workload rather than interpreted loop dispatch.

## Current startup comparison (v0.3-fair)

| Path | Median | Minimum | Relative to Python |
|---|---:|---:|---:|
| Python `-S` | 23.043 ms | 22.380 ms | 1.00x |
| The minimal precompiled loader | 33.674 ms | 32.962 ms | 1.46x |
| The full runtime, precompiled asset | 119.804 ms | 117.690 ms | 5.20x |
| Runtime-compiled source | 120.172 ms | 117.820 ms | 5.22x |
| The compiler | 123.217 ms | 121.256 ms | 5.35x |

## Current throughput comparison (v0.3-throughput-fair)

| Path | Median | Minimum | Relative to Python |
|---|---:|---:|---:|
| Python `-S` | 179.064 ms | 173.958 ms | 1.00x |
| The minimal precompiled loader | 183.570 ms | 181.004 ms | 1.03x |
| The full runtime, precompiled asset | 287.692 ms | 282.749 ms | 1.61x |
| Runtime-compiled source | 284.460 ms | 281.493 ms | 1.59x |

Across five million iterations, generated code through the minimal loader is
within 3% of equivalent Python. The small-workload 46% gap is therefore mainly
asset validation and loader startup, not steady-state integer-loop execution.

## Raw precompiled execution (v0.4-raw-clean)

An explicitly supplied `.then` file skips source lookup and hashing. It still
checks the container magic and host-runtime tag, but its host bytecode must be
trusted. This is distinct from normal `.the` execution, which keeps source
authoritative and verifies its SHA-256 digest before reusing an asset.

| Path | Startup median | vs Python | 5M-loop median | vs Python |
|---|---:|---:|---:|---:|
| Python `-S` | 22.149 ms | 1.00x | 175.447 ms | 1.00x |
| Raw trusted `.then` | 25.651 ms | 1.16x | 181.571 ms | 1.03x |
| Validated precompiled `.the` | 33.172 ms | 1.50x | 191.068 ms | 1.09x |
| Runtime-compiled source | 116.322 ms | 5.25x | 282.233 ms | 1.61x |

For this workload, validated precompilation starts 3.51x faster than runtime
compilation. Explicit raw execution starts 4.53x faster. The clean checkpoints
were run sequentially; earlier concurrent v0.4 points remain in the CSV but are
documented as provisional in the experiment notes.

## Native AOT experiment (v0.6-the-native-aot)

The host-bytecode disassembly executes Python `FOR_ITER` and `BINARY_OP`
instructions for every source iteration. An experimental compiler path now
lowers the supported integer subset to inspectable C and invokes MSVC with
`/O2 /GL /LTCG`, removing that VM dispatch.

| Five-million-iteration path | Median | Relative to C |
|---|---:|---:|
| Hand-written C, MSVC optimized | 7.418 ms | 1.00x |
| Native AOT compiled from The | 7.689 ms | 1.04x |
| Raw hosted `.then` | 175.186 ms | 23.62x |
| Equivalent Python | 172.742 ms | 23.29x |

The native prototype is within 3.7% of the C reference and 22.78x faster than
the hosted `.then` path. This identifies native code generation during compile
as the main performance path. Host bytecode remains useful as a compatibility
fallback, but it is not a credible C/ASM-performance endpoint.

The minimal loader is the relevant generated-program comparison. The full
runtime deliberately imports parser/compiler machinery, so its startup cost is
tracked independently. The next optimization target is loader startup and asset
validation; larger execution-only workloads should also be added so process
startup can be separated from steady-state generated-code speed.
