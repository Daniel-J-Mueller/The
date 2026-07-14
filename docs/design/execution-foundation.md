# Execution foundation

Status: experimental architecture constraint.

## Objective

The must permit C-class control over representation, allocation, calling
convention, vectorization, and machine code while retaining a compact scripting
surface. Convenience may select a library operation; it may not conceal an
unbounded allocation, copy, lock, system call, or fallback.

"Fast by default" means the ordinary spelling selects the lowest-cost valid
implementation known for the compilation target and proven runtime capabilities.
It does not mean every target has equal performance or that source annotations
replace measurement.

## Compilation layers

The initial implementation should keep these boundaries:

```text
.the source
  -> target-independent typed IR
  -> target-specific lowered IR
  -> machine code / object file
  -> platform linker and ABI
```

Precompiled PAGEs store their interfaces and reusable representations in the
versioned `.then` container described by `then-format.md`. Loose source enters the
same pipeline at runtime without being persisted as a compiled page.

- C is a required interoperability boundary, not the semantic definition of The.
- Assembly is a supported implementation layer for scheduled operations and the
  runtime, isolated by architecture and calling convention.
- A portable low-level implementation must exist wherever an assembly
  implementation exists unless a package explicitly restricts its targets.
- The compiler must be able to emit objects without routing program semantics
  through generated C. A C backend may exist as a bootstrap or portability tool.
- Target-independent semantics must not depend on host endianness, integer width,
  C undefined behavior, operating-system names, or assembler syntax.

## Capability selection

Scheduled degradation on PAGE titles is resolved by predicates over a target capability model,
not broad platform labels. Examples include:

- architecture and instruction extensions;
- vector register width;
- required alignment;
- atomic widths and memory-order support;
- operating environment facilities;
- ABI and calling-convention constraints.

Static capabilities are resolved at compile or link time. Runtime CPU dispatch is
allowed only when explicitly represented in the page and included in its effective
input. The chosen version must be inspectable in compiler diagnostics and books.

Each scheduled version requires:

1. the same public type and observable semantics;
2. an explicit capability predicate;
3. a strictly broader fallback after it, or a diagnostic explaining overlap;
4. conformance tests shared by every version;
5. representative benchmarks supporting its order;
6. a final baseline or an explicit unsupported-target result.

The scheduler chooses the lowest numbered satisfied version. It never retries a
slower implementation after a semantic failure. Degradation concerns machine
availability and cost, not error recovery.

## Costs

Operations should eventually expose a compiler-readable cost shape: possible
allocation, copy, blocking, synchronization, system interaction, and complexity
class. The linter may color these costs separately from scheduled degradation.
Combining measured speed, algorithmic complexity, and fallback position into one
color would be misleading, so experiment 0 colors only the declared schedule.

## Portability

Platform agnosticism means identical specified behavior across supported targets,
with target-specific lowering behind capability predicates. It does not mean
discarding native facilities. Exact-width numeric types, byte order conversions,
layout rules, overflow, floating-point modes, atomics, and ABI crossings must all
be explicit in the specification.
