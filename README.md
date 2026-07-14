# The

![The](assets/The-Logo.png)

> The language is a new general-purpose programming and scripting language.

This repository will develop a language from its specification and lowest-level runtime foundations through a complete, production-ready toolchain. The language should be fast, extensible, Turing complete, safe by default, precise in its behavior, and pleasant to read and write.

The project is currently in the **requirements and design phase**. Nothing in this document should be read as a claim that an implementation already exists. Decisions that affect compatibility must be documented before code makes them accidental.

## Core compilation model

The language will use three related units: **PAGEs**, **compiled pages**, and **books**.

- A **PAGE** is a named, explicitly bounded region of `.the` source code.
- A **compiled page** is the reusable record produced for a PAGE inside a `.then` asset.
- A **book** is a precompiled runbook containing an ahead-of-time reference map for all pages used by a program.

Source inside a PAGE may reuse its compiled page when the effective-input hash and all compilation dependencies remain valid. If the PAGE changes, it is runtime-compiled or rebuilt with `then`. Source outside PAGEs is compiled in memory whenever the script runs and is not persisted in `.then`.

Packages are collections of pages plus the metadata needed to discover, validate, link, and use them. The toolchain must automatically determine which pages a program actually uses and establish unambiguous references between them. A book stores this resolved reference information ahead of time so subsequent execution can avoid repeating discovery work and can represent repeated page references compactly.

Conceptually:

```text
source
  |-- PAGE A --hash valid----> reuse compiled page A ----\
  |             `-hash changed-> compile PAGE A ----------+-> resolve -> run
  |-- PAGE B ----------------> compile/reuse page B ------/
  `-- loose source ----------> runtime compile -----------/

book = precompiled runbook + resolved page reference table
```

These terms describe required behavior, not yet a file format or surface syntax.

### PAGE source requirements

- Every PAGE must have a name and matching, syntactically explicit opening and closing rows.
- PAGE names must be unique within their defined namespace; the specification must define that namespace and canonical name format.
- Boundary mismatches, accidental nesting, duplicate names, and illegal cross-boundary constructs must produce precise diagnostics.
- PAGEs may not nest in the initial design.
- A PAGE must form a compilation unit with explicit inputs, outputs, imports, exports, and required capabilities.
- References crossing a PAGE boundary must participate in dependency tracking and invalidation.
- Moving or renaming a PAGE must have deterministic effects on identity and caching.
- Debug information and diagnostics must map compiled instructions back to the original PAGE and source spans.
- Formatting and documentation tools must preserve PAGE identity and valid boundaries.

### PAGE hash and invalidation requirements

The PAGE hash must be specified as a reproducible **effective-input hash**, not merely a checksum of visible source text. At minimum, its input model must account for:

- normalized PAGE source and compilation-relevant boundary metadata;
- language edition and compiler version or compiler compatibility identifier;
- target platform, architecture, ABI, and compilation profile;
- enabled features, capabilities, optimization settings, and semantic compiler flags;
- hashes and public interface identities of imported pages;
- relevant standard-library, package, macro, generated-code, and build-extension inputs;
- environment values only when explicitly declared as build inputs.

The exact hash algorithm and canonical serialization must be versioned. Cache validity must never depend on timestamps alone. A cryptographic digest should be used where collision resistance or artifact integrity matters.

Invalidation must be dependency-aware: changing a page's private implementation should not force recompilation of dependents when its stable exported interface and required inline/optimization metadata are unchanged. Any optimization that embeds implementation details must record that dependency so stale code cannot be reused.

### Page requirements

A page must contain or reference enough information to:

- identify its source PAGE, package, version, language edition, target, and compilation profile;
- verify the effective-input hash and artifact integrity;
- expose a typed, versioned public interface for resolution without parsing its original source;
- enumerate dependencies, symbols, capabilities, initialization behavior, and compatibility constraints;
- link without relying on ambiguous global names or filesystem location;
- support diagnostics, debugging, profiling, and source mapping;
- reject incompatible or corrupted artifacts safely;
- permit deterministic cache eviction and reconstruction from source when source is available.

Pages must be content-addressable or have an equivalent identity scheme that prevents two different artifacts from silently occupying the same identity. Cached pages are derived artifacts, not the authority for source semantics. Loading an untrusted page must be treated like loading untrusted object code and must pass validation appropriate to its trust boundary.

The compiler must define whether a page stores native code, portable bytecode, intermediate representation, or a layered combination. That choice must not weaken the semantic guarantees of the source language.

### Package requirements

- A package must declare its identity, version, exported page names, dependencies, supported targets, language editions, and integrity metadata.
- The resolver must discover the transitive set of pages actually referenced by the entry program while detecting missing, ambiguous, incompatible, and cyclic relationships.
- Page references must use stable qualified identities rather than source-order indexes or incidental paths.
- Unused pages should not be linked into a program unless required by declared initialization or reflection semantics.
- Package initialization must be explicit, ordered deterministically, and included in dependency analysis.
- Cycles must either be rejected with an actionable dependency trace or governed by fully specified initialization semantics.
- Package sources and precompiled pages must have clear precedence and verification rules.
- Resolution must be reproducible from the package manifest, lockfile, target configuration, and declared inputs.

### Book requirements

A book is an immutable, precompiled execution plan rather than an unrelated second packaging system. It must contain or reference:

- the entry point and runtime compilation plan for any loose source;
- a compact table assigning local reference identifiers to fully qualified page identities;
- the resolved page dependency graph and deterministic initialization order;
- expected hashes, versions, targets, interfaces, and compatibility constraints;
- required runtime, package, capability, and platform metadata;
- enough information to validate every referenced page before execution.

Books must deduplicate repeated page references through their local reference table. They must fail safely or trigger a clearly defined rebuild when a referenced page no longer satisfies the recorded identity or compatibility constraints. A book must not silently run with a different dependency graph from the one it records.

The format must define whether pages are embedded, stored beside the book, or retrieved from a content-addressed cache. It should support a compact distributable mode and a self-contained mode if both can preserve reproducibility and security. Portability across machines and targets must be explicit rather than assumed.

### Runtime compilation requirements

- Script startup must identify PAGE regions before compiling loose source.
- Cache lookup, validation, recompilation, reference resolution, and execution must have deterministic ordering and observable diagnostics.
- Concurrent processes compiling the same PAGE must not corrupt or partially publish a compiled page; asset publication must be atomic.
- A failed recompilation must not replace the last valid cached artifact, but stale artifacts must not be executed as though they match changed source.
- Runtime compilation should expose explainable status such as cache hit, cache miss, invalidation reason, compile duration, and selected artifact when diagnostic output is requested.
- Sandboxed or restricted environments must be able to disable runtime compilation and require a valid book and page set.
- Runtime compilation permissions, generated native code, temporary files, and executable-memory behavior must be covered by the threat model.
- The runtime must place bounded limits on cache size, compilation resources, dependency depth, and malformed metadata.

## Product vision

The language should combine:

- predictable performance suitable for systems, application, and scripting work;
- memory and type safety without making ordinary programs cumbersome;
- compact, readable source whose intent can be followed from top to bottom;
- explicit behavior where hidden control flow, coercion, or allocation would be surprising;
- a small, coherent core that can grow through libraries, packages, tooling, and stable extension interfaces;
- first-class interoperability with existing systems rather than an isolated ecosystem;
- one consistent language across quick scripts, reusable libraries, and compiled applications.

When these goals conflict, the project should generally prefer correctness and clarity first, predictable behavior second, and benchmark-demonstrated optimization third. Convenience must not silently weaken safety.

## Guiding principles

1. **Readable by design.** Common code should resemble a precise explanation of the work it performs. Syntax should be regular, searchable, and resistant to ambiguity.
2. **Safe by default.** Memory errors, unchecked null access, data races, and undefined behavior should be prevented or isolated behind explicit unsafe boundaries.
3. **Pay only for what is used.** Abstractions should have documented costs and compile away where practical. Hidden allocation, blocking, and copying should be minimized.
4. **Deterministic semantics.** Evaluation order, numeric behavior, errors, resource cleanup, and concurrency rules must be specified rather than left to an implementation.
5. **Small trusted core.** The compiler, runtime, and standard library should minimize privileged machinery and expose ordinary, composable mechanisms.
6. **Extensible without fragmentation.** Packages, macros or metaprogramming, foreign-function interfaces, and tooling protocols should have stable boundaries and compatibility rules.
7. **Tooling is part of the language.** Formatting, package management, documentation, testing, diagnostics, and editor support are product requirements, not optional extras.
8. **Evidence over aspiration.** Performance, safety, usability, and compatibility claims require tests, benchmarks, or written rationale.

## High-level requirements

### Language semantics

The specification must define:

- lexical grammar, source encoding, comments, identifiers, keywords, and literals;
- a context-free grammar with unambiguous precedence and associativity;
- declarations, expressions, statements, scopes, modules, and visibility;
- functions, closures, recursion, and the constructs necessary for Turing completeness;
- value and reference semantics, mutability, identity, copying, movement, and destruction;
- primitive types, user-defined data types, generics, interfaces/traits/protocols, and type inference boundaries;
- exhaustive pattern matching or an equally safe mechanism for decomposing structured values;
- conversions and casts, with no surprising implicit narrowing or lossy coercion;
- nullability or absence represented explicitly;
- recoverable errors and unrecoverable failures, including propagation and stack information;
- evaluation order, short-circuiting, overflow, floating-point behavior, and integer division;
- resource lifetime and deterministic cleanup behavior;
- concurrency and asynchronous execution semantics, including cancellation and data-race prevention;
- unsafe operations, if any, contained by syntactically visible and auditable boundaries;
- compile-time behavior, reflection, and metaprogramming limits;
- a versioned compatibility policy for source, binary, and package interfaces.

Every valid program must have behavior defined by the language specification, except where the specification deliberately identifies implementation-defined behavior. Implementation-defined behavior must be queryable or documented; undefined behavior must never be reachable from safe code.

### Type system and safety

The language must provide:

- static checking for production code, with diagnostics that explain both the problem and likely correction;
- sound rules for ownership, borrowing, tracing, reference counting, regions, or whichever memory strategy is selected;
- bounds-checked memory access in safe code;
- explicit handling of optional values and fallible operations;
- protection against use-after-free, double-free, invalid aliasing, and uninitialized reads;
- concurrency rules that prevent data races in safe code;
- controlled integer overflow behavior and checked alternatives;
- isolation of native interoperation and raw memory access;
- a threat model and security response process before the first stable release.

The exact memory-management and type-system models remain open design decisions. They must be evaluated against latency, throughput, implementation complexity, learnability, foreign interoperability, and suitability for both short scripts and long-running applications.

### Execution and performance

The implementation must eventually support:

- fast startup for command-line scripts;
- competitive steady-state throughput for compiled applications;
- bounded and measurable runtime overhead;
- optimized release builds and fast incremental development builds;
- reproducible builds;
- a documented intermediate representation and optimization pipeline;
- separate compilation, incremental compilation, and caching where feasible;
- debugging information and profiler-friendly output;
- cross-compilation and a clearly defined target-support policy;
- benchmarking against representative workloads, not isolated microbenchmarks alone.

The initial execution model—native ahead-of-time compilation, bytecode/virtual machine, just-in-time compilation, interpretation, or a staged combination—must be selected through prototypes and recorded in an architecture decision record (ADR).

Performance targets must become numeric before implementation milestones are declared complete. Baselines should include startup time, compile time, peak memory, binary size, latency, throughput, and standard-library workloads on named reference hardware.

### Extensibility and interoperability

The language and toolchain must include:

- a module and package system with explicit public APIs;
- PAGEs as explicit incremental compilation units and `.then` as their reusable asset container;
- books as compact, validated precompiled execution plans;
- deterministic dependency resolution and lockfiles for applications;
- semantic versioning guidance and compatibility checking;
- a package registry protocol that can support mirrors and private registries;
- an extension model for compiler tools that does not require arbitrary compiler internals to remain stable;
- hygienic, inspectable metaprogramming if macros are adopted;
- a stable C-compatible foreign-function interface as the minimum interoperability layer;
- a documented application binary interface for supported targets, or explicit rules where ABI stability is not promised;
- build-system hooks for native libraries, code generation, and platform-specific resources;
- serialization and wire formats implemented in libraries rather than privileged syntax wherever possible.

Extensions must not be able to silently change the meaning of unrelated source files. Generated code must be inspectable, diagnostics must map back to user source, and build extensions must declare their inputs and outputs for reproducibility.

### Standard library

The standard library must be cohesive, documented, tested, and versioned with a clear stability policy. Its eventual scope should include:

- core types, collections, iterators, strings, Unicode, and byte buffers;
- numeric operations and explicit-width numeric types;
- errors, results, optional values, and resource management;
- filesystem paths, files, streams, processes, environment, and terminal I/O;
- time, duration, randomness, and platform-independent synchronization;
- concurrency, tasks, channels or equivalent coordination primitives, and cancellation;
- networking primitives and secure integration points for maintained TLS implementations;
- encoding, decoding, hashing, and common data formats;
- testing, assertions, benchmarks, and property/fuzz-testing integration.

The core library should stay small. Features that can evolve independently should ship as maintained packages rather than permanently expanding the language's privileged surface.

### Developer experience and tooling

A complete product requires one cohesive command-line entry point that eventually provides:

- create, build, run, test, benchmark, check, format, lint, document, package, and publish workflows;
- dependency addition, removal, update, audit, and tree inspection;
- clear, stable exit codes and machine-readable output;
- offline operation after dependencies are cached;
- helpful diagnostics with source spans, context, suggestions, and error codes;
- an official formatter with one canonical output;
- a linter with configurable policy but stable defaults;
- a language server supporting completion, navigation, rename, references, semantic highlighting, and inline diagnostics;
- debugger integration and a documented debug adapter strategy;
- generated API documentation with cross-links and runnable examples;
- a read-evaluate-print loop or comparably quick interactive workflow;
- shell completion and support for common editors and continuous-integration environments.

### Platform support

Support tiers must be published before release. Each tier should state whether it receives continuous testing, prebuilt toolchains, debugging support, and security fixes.

The design should account for:

- 64-bit Windows, Linux, and macOS as primary desktop/server targets;
- major x86-64 and ARM64 architectures;
- WebAssembly as a first-class design consideration;
- containers and minimal/headless environments;
- path, process, terminal, dynamic-library, and Unicode differences across platforms;
- future embedded or freestanding targets without requiring them in the initial release.

## Specification requirements

The language specification is a versioned product artifact and the source of truth. It must include:

- formal or precisely testable grammar and semantic rules;
- examples and counterexamples for each feature;
- a glossary with one term per concept;
- implementation limits and portability requirements;
- a conformance test suite derived from normative statements;
- an edition or versioning mechanism for intentional language evolution;
- a process for proposals, review, stabilization, deprecation, and removal.

Major features should progress through clearly marked stages such as experimental, preview, stable, and deprecated. Stable syntax or semantics may not change without the compatibility process defined by the project.

## Proposed repository structure

The repository should grow into a workspace with boundaries similar to the following. Exact names may change once the implementation strategy is chosen.

```text
/
|-- README.md                 # Product vision and top-level requirements
|-- CONTRIBUTING.md           # Contribution workflow and review standards
|-- CODE_OF_CONDUCT.md
|-- SECURITY.md               # Vulnerability reporting and support policy
|-- LICENSE
|-- CHANGELOG.md
|-- roadmap.md
|-- docs/
|   |-- specification/        # Normative language specification
|   |-- design/               # Proposals and design rationale
|   |-- adr/                  # Architecture decision records
|   |-- guides/               # User and implementation guides
|   `-- internals/            # Compiler/runtime documentation
|-- compiler/
|   |-- frontend/             # Lexer, parser, diagnostics, syntax trees
|   |-- semantics/            # Name resolution and type checking
|   |-- ir/                   # Intermediate representations
|   |-- optimizer/
|   |-- backend/              # Code generation and target integration
|   `-- driver/               # Compiler orchestration
|-- page/                     # PAGE hashing, artifacts, cache, and validation
|-- book/                     # Precompiled runbook format and reference resolver
|-- runtime/                  # Runtime support kept separate from compiler logic
|-- library/
|   |-- core/                 # Minimal privileged/freestanding library
|   `-- std/                  # Standard library
|-- tools/
|   |-- cli/
|   |-- formatter/
|   |-- linter/
|   |-- language-server/
|   |-- package-manager/
|   `-- debugger/
|-- packages/                 # Official packages outside the standard library
|-- tests/
|   |-- conformance/
|   |-- compile-pass/
|   |-- compile-fail/
|   |-- runtime/
|   |-- integration/
|   |-- compatibility/
|   |-- fuzz/
|   `-- fixtures/
|-- benchmarks/
|   |-- compiler/
|   |-- runtime/
|   `-- programs/
|-- examples/
|-- scripts/                  # Reproducible development and release automation
`-- .github/                  # CI, issue templates, and project automation
```

Repository rules:

- Architectural layers must have explicit dependency directions; circular dependencies are prohibited.
- The compiler frontend, semantic model, and diagnostics should not depend directly on a particular code-generation backend.
- Test fixtures and generated artifacts must be clearly separated from hand-authored sources.
- Generated files should not be committed unless doing so is required for bootstrapping, distribution, or reviewability.
- Each major component must document its invariants, public interfaces, ownership, and test strategy.
- Build and test entry points must work consistently in local development and CI.
- Bootstrapping must be reproducible and must never require an untracked binary.

## Quality requirements

### Correctness and testing

- Every stable language rule must have conformance coverage.
- Every bug fix must add a regression test where practical.
- Parser, type checker, package resolver, binary readers, and unsafe runtime surfaces must be fuzzed.
- Compile-fail tests must verify structured diagnostic codes, not only fragile full-text output.
- The suite must cover unit, integration, end-to-end, cross-platform, optimization, and compatibility behavior.
- Standard-library examples in documentation should compile and run as tests.
- Differential and property testing should be used where an independent oracle or invariant exists.
- Release candidates must pass the full suite from a clean, reproducible environment.

### Performance

- Benchmarks must record hardware, operating system, toolchain version, inputs, and variance.
- CI should detect statistically meaningful regressions without encouraging benchmark gaming.
- Compiler performance and generated-program performance must be measured separately.
- Debug builds must remain usable; optimization cannot be the only path to acceptable behavior.
- Performance-sensitive design claims require representative prototypes before stabilization.

### Security and robustness

- Inputs such as source, packages, object files, debug data, and protocol messages must be treated as untrusted.
- Compiler crashes, hangs, and uncontrolled resource consumption on valid or malformed input are defects.
- Dependency integrity must be cryptographically verifiable.
- Package publishing needs provenance, ownership recovery, yanking, and malicious-package response procedures.
- Build scripts and procedural extensions must have an explicit trust and isolation model.
- Releases must provide checksums, provenance metadata, a software bill of materials, and signed artifacts where supported.
- Security-sensitive functionality should reuse maintained, reviewed implementations instead of inventing new cryptography.

### Accessibility and documentation

- Core documentation must be usable without proprietary services.
- Diagnostics must not rely on color alone and should support screen-reader-friendly plain output.
- Terminology and syntax should avoid needless abbreviation and visually confusable constructs.
- A language tour, full reference, standard-library reference, cookbook, migration guides, and implementer guide are required for 1.0.

## Governance and design process

Substantial decisions should be proposed in writing. A proposal should state the problem, constraints, alternatives, safety and performance implications, compatibility risks, teaching impact, and a migration plan.

Use ADRs for implementation architecture and language proposals for user-visible semantics. Accepted decisions should remain in the repository even when superseded so that the reasoning is recoverable.

Before implementation begins, the project must resolve at least these foundational questions:

1. What are the initial use cases and explicit non-goals?
2. What implementation language will build the bootstrap compiler?
3. What execution model and backend will be used first?
4. What memory-management and resource-lifetime model will safe code use?
5. How powerful will the static type system and inference be?
6. What is the error model, and are exceptions part of it?
7. What concurrency model prevents data races while remaining practical?
8. What metaprogramming facilities are allowed, and when do they execute?
9. Which ABI, object format, linker, and C interoperability guarantees are required?
10. How will source evolution, editions, and long-term compatibility work?
11. Which platforms form the initial support matrix?
12. How will the project measure success against existing languages and workflows?
13. What exact row syntax opens and closes a named PAGE?
14. Which inputs form a PAGE's effective hash and which changes invalidate dependent pages?
15. What executable representation, interface metadata, and source maps does a page contain?
16. Are book references embedded, adjacent, cache-addressed, or supported in multiple distribution modes?
17. What are the trust, signing, sandboxing, and portability rules for pages and books?

## Delivery roadmap

### Phase 0: Requirements and experiments

- Define target users, use cases, non-goals, and measurable success criteria.
- Draft the lexical grammar, core syntax, semantic model, and representative example programs.
- Prototype the highest-risk choices: parser, type system, memory model, execution strategy, and FFI.
- Specify PAGE boundaries and prototype hashing, invalidation, package discovery, and book reference-table behavior.
- Establish ADR and language-proposal templates.
- Select the implementation stack only after experiments expose its tradeoffs.

### Phase 1: Minimal language

- Implement source loading, lexer, parser, syntax tree, diagnostics, name resolution, and type checking.
- Support functions, local state, control flow, basic data types, modules, and deterministic errors.
- Execute a deliberately small Turing-complete subset.
- Compile PAGEs into `.then`, recompile changed PAGEs safely, and runtime-compile loose source.
- Publish an executable specification and conformance tests for the subset.

### Phase 2: Usable toolchain

- Add the package/build workflow, formatter, test runner, documentation generator, and language server basics.
- Implement the selected memory/resource model and core concurrency foundations.
- Establish C interoperability and multi-platform CI.
- Add package-level page resolution and a first versioned book format with reproducible reference maps.
- Begin compatibility, fuzzing, and performance dashboards.

### Phase 3: Ecosystem preview

- Stabilize the module/package model and standard-library shape.
- Operate a preview package registry with security controls.
- Deliver debugger and profiler workflows, optimized builds, and reproducible distribution.
- Gather real-world feedback from nontrivial applications and libraries.

### Phase 4: 1.0 readiness

- Freeze and audit the stable specification and compatibility guarantees.
- Pass conformance, security, portability, performance, and documentation gates.
- Publish support lifetimes, governance, release cadence, and migration policy.
- Ship signed installers/toolchains, source distributions, and editor integrations.

## Definition of a complete 1.0 product

Version 1.0 is complete only when all of the following are true:

- the stable language is fully described by a reviewed specification;
- an independent implementation could be built from that specification;
- safe programs cannot invoke undefined behavior through stable language or library APIs;
- the compiler and standard library pass the published conformance suite;
- formatter output and package resolution are deterministic;
- PAGE invalidation is complete, minimal where promised, explainable, and covered by conformance tests;
- page and book formats are versioned, integrity-checked, safely parsed, and reproducibly generated;
- the CLI covers the full edit-build-run-test-debug-package workflow;
- supported platforms have automated testing and documented installation and debugging paths;
- representative programs meet published startup, compile-time, memory, and runtime targets;
- dependency integrity, vulnerability reporting, and security update processes operate end to end;
- compatibility rules and migration tooling are demonstrated across at least one language evolution;
- user, library-author, and implementer documentation are complete;
- releases can be reproduced, verified, and installed without relying on developer machines;
- at least several substantial applications validate that the language works beyond curated examples.

## Non-goals for the current phase

Until foundational decisions are recorded, this project will not:

- commit to surface syntax based only on aesthetic preference;
- promise a specific backend, garbage collector, ownership system, or self-hosting date;
- optimize benchmarks before semantics and correctness are stable;
- build a package registry before the package and trust models are designed;
- treat self-hosting as proof of completeness or product readiness;
- add features solely to match another language's checklist.

## Immediate next steps

1. Write `docs/design/use-cases.md` with primary users, representative programs, constraints, and explicit non-goals.
2. Add proposal and ADR templates plus a decision index.
3. Draft small example programs that exercise scripting, systems integration, data modeling, errors, concurrency, and foreign calls.
4. Compare candidate execution, memory, and type-system models against those programs and measurable goals.
5. Publish the first language proposal only after the use cases and evaluation criteria are accepted.

## Status

**Pre-implementation / requirements discovery.** The current README is a design charter and product checklist. Requirements will become more precise as proposals and experiments supply evidence.

## First syntax experiment

The first executable experiment uses `.the` source files, line-local `@labels`,
explicit `-> @label` jumps, and paired identical `PAGE name` rows. The
draft and its deliberately small primitive vocabulary are in
`docs/design/surface-syntax-0.md`.

PAGE regions are optional precompilation units. Source outside PAGEs is compiled
in memory when it runs. The source remains authoritative:

```text
then iters_and_strides.the    # precompile PAGEs into iters_and_strides.then
the iters_and_strides.the     # validate/reuse the asset and run the source
```

`the` does not require a compiled asset. The `.then` format is a portable,
versioned container with typed IR and optional target-native code slices; its
initial binary layout is drafted in `docs/design/then-format.md`.

Scheduled degradation is written only when fallbacks exist: `PAGE name 1 OF 3`.
Version 1 is preferred; later versions are capability fallbacks.
Color output renders scheduled titles on a green-to-red gradient.

### Surface operations

| Operation | Purpose |
|---|---|
| `PAGE name ... PAGE name` | Identical rows bound a named compilation page. |
| `PROC name` / `PROC name(args)` | Declares a procedure, The's function unit. |
| `RUN x through (a, b)` | Hits an inclusive integer range, including both endpoints. |
| `ITER x IN values` | Visits values supplied by an iterable. |
| `LOOP (condition)` | Repeats while a condition remains true. |
| `LIST[Type]` | Declares a contiguous typed list; `[]` is a list literal. |
| `OBJ name = value` | Creates a mutable local variable with an inferred type. |
| `OUT(values)` | Writes values to standard output. |
| `RETURN value` | Returns from the current procedure. |
| `IF (condition)` / `ELSE` | Selects a branch. |
| `MATCH (value)` | Performs exhaustive value selection. |
| `STOP` / `NEXT` | Stops a loop or advances to its next hit. |
| `USE name` | Imports a page or package interface. |
| `RAW [...]` | Opens an auditable low-level/unsafe region. |

Matched `()` and `[]` may be inline or expanded across lines. Newlines end only
complete statements; semicolons and JavaScript-style closing punctuation are not
required.

Build and run the dependency-free C11 structural linter with:

```text
cc -std=c11 -Wall -Wextra -Werror tools/linter/the_lint.c -o the-lint
./the-lint examples/prime_numbers.the
```

Pass `--color` to highlight PAGE boundaries, line labels, jumps, and comments.
This prototype validates PAGE, delimiter, operation, and line-reference structure. It does not yet
parse, type-check, compile, or execute The programs.
