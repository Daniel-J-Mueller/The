# Surface syntax experiment 0

Status: experimental.

## Source and layout

The source extension is `.the`; text is UTF-8. Matched `()` and `[]` may be
collapsed onto one line or expanded across many without changing meaning.
Statement terminators are not required. A newline ends a statement only when all
delimiters are balanced and the expression is complete.

```the
OBJ point = (2, 4)

OBJ point = (
    2,
    4
)
```

Both forms are identical. Blank and comment-only lines have no execution effect.

`|` begins a line comment. `||` opens and closes a comment block:

```the
OUT(value) | visible until the line ends

||
This entire region is commentary.
||
```

## Pages

A page is bounded by two byte-identical title rows, excluding line-ending
encoding. Each title begins with exactly `PAGE ` at column one:

```the
PAGE count
PROC count(start INT) INT
[
    RETURN start
]
PAGE count
```

The first title opens the page; the next identical title closes it. Pages cannot
nest. The name is an ASCII identifier matching `[A-Za-z_][A-Za-z0-9_]*`. The
toolchain converts it to a stable 64-bit identifier. Duplicate names, mismatched
titles, invalid names, and identifier collisions are errors.

## Procedures and control

`PROC` declares The's function unit. Parameters are omitted when there are none.
Calls use `()`. Executable bodies and control bodies use `[]`.

```the
PROC choose(ready BOOL) INT
[
    IF (ready) [RETURN 1]
    ELSE [RETURN 0]
]
```

`RUN name through (first, last)` hits every integer from the first endpoint
through the last endpoint, inclusive. Direction is inferred:

```the
RUN x through (1, 7) [OUT(x)]   | 1 2 3 4 5 6 7
RUN x through (7, 1) [OUT(x)]   | 7 6 5 4 3 2 1
```

An optional third value is a nonzero step. Its sign must move toward the last
endpoint. Bounds and step are evaluated once. Overflow is checked.

`ITER item IN values` consumes an iterable. `LOOP (condition)` repeats while a
condition is true. `STOP` exits and `NEXT` advances to the next hit.

Line labels remain an experimental low-level facility. `@name` labels the next
executable line, `-> @name` jumps, and `? condition -> @name` jumps conditionally.
Labels are page-local and every reference must resolve.

## Initial operations

| Form | Denotation |
|---|---|
| `PROC name` / `PROC name(args)` | procedure declaration |
| `f(a, b)` | call with two arguments |
| `LIST[Type] values = []` | typed list and empty literal |
| `OBJ name = value` | mutable local variable with inferred type |
| `RUN x through (a, b)` | inclusive integer traversal |
| `ITER x IN values` | iterable traversal |
| `OUT(values)` | standard output |
| `LOOP (condition)` | conditional repetition |
| `IF (condition)` / `ELSE` | branch |
| `MATCH (value)` | exhaustive selection |
| `RETURN value` | procedure return |
| `STOP` / `NEXT` | loop exit / next hit |
| `USE name` | import an interface |
| `RAW [...]` | explicit low-level/unsafe region |

Operator precedence, types, ownership, overflow, and error semantics remain to be
specified before stabilization.

## Scheduled degradation

Fallback positions appear only when an operation has multiple implementations.
`1 OF 3` is preferred; later versions admit fewer machine requirements and may
cost more:

```the
PAGE bytes_equal_vector 1 OF 3
PAGE bytes_equal_vector 1 OF 3

PAGE bytes_equal_words 2 OF 3
PAGE bytes_equal_words 2 OF 3

PAGE bytes_equal_bytes 3 OF 3
PAGE bytes_equal_bytes 3 OF 3
```

All versions require identical public types and observable behavior. Selection is
by declared machine capabilities, never source order or OS name. Benchmarks must
verify the preference order. The linter colors PAGE titles by
`(version - 1) / (count - 1)` on a green-to-red gradient. A PAGE without an
actual fallback set has no schedule annotation and is neutral.
