# The

> The language is a new general-purpose programming and scripting language.

This repository will develop a language from its specification and lowest-level runtime foundations through a complete, production-ready toolchain. The language should be fast, extensible, Turing complete, safe by default, precise in its behavior, and pleasant to read and write.

The project is currently in the **requirements and design phase**. Nothing in this document should be read as a claim that an implementation already exists. Decisions that affect compatibility must be documented before code makes them accidental.

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

## Delivery roadmap

### Phase 0: Requirements and experiments

- Define target users, use cases, non-goals, and measurable success criteria.
- Draft the lexical grammar, core syntax, semantic model, and representative example programs.
- Prototype the highest-risk choices: parser, type system, memory model, execution strategy, and FFI.
- Establish ADR and language-proposal templates.
- Select the implementation stack only after experiments expose its tradeoffs.

### Phase 1: Minimal language

- Implement source loading, lexer, parser, syntax tree, diagnostics, name resolution, and type checking.
- Support functions, local state, control flow, basic data types, modules, and deterministic errors.
- Execute a deliberately small Turing-complete subset.
- Publish an executable specification and conformance tests for the subset.

### Phase 2: Usable toolchain

- Add the package/build workflow, formatter, test runner, documentation generator, and language server basics.
- Implement the selected memory/resource model and core concurrency foundations.
- Establish C interoperability and multi-platform CI.
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
