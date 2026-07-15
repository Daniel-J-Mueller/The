# Runtime optimization notes

## v0.1 — lazy interpreted strides

- Hypothesis: constructing the complete numeric sequence before entering a loop
  wastes time and memory.
- Change: numeric iteration yields values lazily and no longer allocates an
  O(n) temporary list. Per-value comparison lambdas were replaced with direct
  loop branches.
- Safety: a zero stride now reports an error instead of running forever.
- Result: established the first retained process-level baseline. Source was
  13.57x Python and the minimal loader was 1.52x Python.

## v0.2 — expression cache and native integer range

- Hypothesis: the interpreter repeatedly parsed, validated, and compiled the
  same assignment expression on every iteration.
- Change: validated expression code is cached (bounded to 256 entries).
  Precompiled `intthrough` uses Python's C-level `range` implementation.
- Result: source median fell from 338.395 ms to 135.247 ms, a 60.0% reduction
  and 2.50x speedup. Loader median fell from 37.820 ms to 32.670 ms, although
  some of that smaller change may be process-launch variance.

## v0.3 — lower cache misses to host bytecode

- Hypothesis: after parsing source, executing the intermediate node tree adds
  avoidable dispatch and expression-evaluation overhead.
- Change: valid source without a reusable asset is lowered to the same host
  bytecode backend used by `.then` assets and executed in memory.
- Result: source median fell from 135.247 ms to 117.355 ms, a further 13.2%
  reduction. It is within 0.3% of the full runtime's precompiled path, showing
  that parser/compiler process startup now dominates this workload.
- Decision: keep. The source remains authoritative and no cache is persisted;
  only the in-memory execution backend changed.

## v0.3-throughput — separate startup from loop execution

- Hypothesis: the 10,000-iteration workload is primarily measuring process and
  import startup, concealing generated-code throughput.
- Experiment: run an otherwise equivalent inclusive sum through 5,000,000 with
  identical `total = total + number` loop bodies in The and Python.
- Initial result: rejected as a comparison point. The Python loop ran at module
  scope while generated The ran inside its `PROC`, giving The faster local-name
  bytecode. The rejected measurements remain in CSV to preserve the audit trail.
- Correction: both Python references now use a `main()` function and the exact
  `total = total + number` operation generated for The. Corrected runs carry a
  `-fair` version suffix. This changes the benchmark only, not the runtime.
- Corrected result: the minimal loader measured 183.570 ms against Python at
  179.064 ms, a 1.03x ratio. Generated integer-loop throughput is effectively
  near parity at this scale; startup and asset validation are the next target.

## v0.4 — explicit raw `.then` execution

- Hypothesis: source reading, SHA-256 import, and hashing form a meaningful part
  of minimal-loader startup. A trusted precompiled deployment should be measured
  without those source-authority costs.
- Change: the loader accepts an explicit `.then` path, checks its format and host
  compatibility, and executes it without locating or hashing source. SHA-256 is
  now imported lazily only for normal `.the` validation.
- Safety boundary: raw assets contain host bytecode and must be trusted. Normal
  `.the` execution remains source-authoritative and cryptographically validates
  the adjacent asset. Raw mode is an explicit deployment/benchmark path, not an
  automatic fallback.
- Measurement note: the first `v0.4-raw` and `v0.4-raw-throughput` runs executed
  concurrently and are retained as provisional/contended points. Conclusions
  use the sequential `-clean` checkpoints.
- Clean result: raw startup measured 25.651 ms versus Python at 22.149 ms
  (1.16x). Validated precompiled startup measured 33.172 ms and runtime-compiled
  source measured 116.322 ms. Precompilation is 3.51x faster with source-hash
  validation and raw trusted execution is 4.53x faster than runtime compilation.
- Throughput result: at five million iterations, raw `.then` measured 181.571 ms
  versus Python at 175.447 ms (1.03x). The generated loop remains near parity.
- Decision: keep as an explicit mode. It provides a useful deployment and
  measurement boundary without weakening normal source-authoritative execution.

## v0.5-native-baseline — identify the hosted execution ceiling

- Hypothesis: Python host-bytecode dispatch, rather than The's loop lowering,
  is now the dominant throughput bottleneck.
- Evidence before measurement: disassembly of the generated procedure contains
  a Python `FOR_ITER` and `BINARY_OP` for every source iteration. The minimal
  loader removes compiler startup but cannot remove those VM operations.
- Experiment: compare the five-million-iteration workload with an MSVC `/O2`
  native C reference. Its loop limit comes from `argv`, preventing compile-time
  replacement of the entire loop with a constant result.
- Architectural implication: if confirmed, compilation needs a native machine-
  code slice (or a lower-level JIT/AOT backend). Further Python loader tuning is
  useful for startup but cannot reach the C/ASM throughput target.
- Result: MSVC `/O2` C measured 7.607 ms versus raw hosted `.then` at
  179.655 ms, making the hosted path 23.62x slower. The hypothesis is confirmed:
  Python VM dispatch is the dominant steady-state bottleneck.
- Decision: stop treating host bytecode as the performance destination. Retain
  it as a portable/fallback execution tier and move optimized builds to native
  AOT slices.

## v0.6-the-native-aot — compile The's numeric subset to machine code

- Hypothesis: lowering The's already-parsed iteration and arithmetic nodes to C
  during compilation lets an optimizing native backend remove VM dispatch and
  approach hand-written C without changing source syntax.
- Change: added an experimental AOT backend for integer declarations,
  assignments, inclusive integer iteration, returns, and integer output. It
  emits inspectable C and invokes MSVC with `/O2 /GL /LTCG`.
- Result: native code compiled from the actual `.the` workload measured
  7.689 ms. Hand-written C measured 7.418 ms in the same 15-sample run, so the
  prototype is within 3.7% of C and 22.78x faster than raw hosted `.then` at
  175.186 ms.
- Cause of speedup: the hot loop is native machine code; Python `FOR_ITER`,
  `BINARY_OP`, dynamic object operations, and interpreter dispatch are absent.
- Scope: this is deliberately a numeric subset prototype, not yet a general
  native backend or a native slice embedded in the `.then` container.
- Decision: keep and expand. Next work is typed lowering, native slice metadata,
  deterministic toolchain invocation, and fallback selection.
