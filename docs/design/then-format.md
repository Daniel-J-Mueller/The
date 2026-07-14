# `.then` compiled asset format

Status: format draft 0. This draft supersedes the earlier assumption that a page
is itself a standalone file.

## Commands and files

```text
then program.the    -> program.then
the program.the     -> run program, reusing program.then when valid
```

`.the` is authoritative UTF-8 source. `.then` is a derived binary asset containing
compiled PAGE regions from that source. It is safe to delete because it can be
reconstructed. Source outside PAGE regions is not stored as a reusable compiled
page and is compiled in memory when `the` runs the program.

`then` compiles every PAGE it can resolve and publishes the resulting `.then`
atomically. `the` does not require a `.then` file. When one exists, it validates
each page independently, uses valid compatible pages, and runtime-compiles missing
or stale pages. A stale asset is never executed merely because its filename
matches.

## Representation decision

`.then` is a versioned container, not a raw executable, shared library, object
file, bytecode stream, archive of host objects, or memory dump. It can carry:

1. target-independent typed IR for portability;
2. zero or more target-native code slices for immediate execution;
3. public interfaces, dependencies, capabilities, and source maps required to
   validate and link either representation.

Native slices provide the C-class path. Typed IR provides a fallback when a
compatible native slice is absent. A distribution may omit IR when it deliberately
targets specific machines, but the container must then reject unsupported targets
cleanly.

## File header

All integers use fixed-width little-endian encoding. Readers must not map structs
directly over untrusted bytes.

```text
offset  size  field
0       8     magic: 54 48 45 4e 0d 0a 1a 0a  ("THEN" + guards)
8       2     container major version
10      2     container minor version
12      4     header size
16      8     complete file size
24      8     section-directory offset
32      4     section count
36      4     format flags
40      32    BLAKE3 digest of canonical container content
72      8     reserved; must be zero
```

For hashing, the digest field is treated as 32 zero bytes. Draft 0 uses a 32-byte
cryptographic digest field. BLAKE3 is proposed for fast content hashing;
stabilization requires a reviewed canonicalization specification
and maintained implementation. Unknown major versions are rejected. Unknown minor
sections may be skipped only when they are marked noncritical.

## Section directory

Each directory entry contains a section kind, flags, byte offset, stored size,
expanded size, alignment, and digest. Every range must be bounds-checked before
use. Sections may not overlap. Decompression and allocation have configured
limits.

Required logical sections are:

| Section | Contents |
|---|---|
| `MANIFEST` | source identity, edition, compiler compatibility, build profile |
| `STRINGS` | deduplicated length-prefixed UTF-8 strings; no implicit terminators |
| `PAGES` | stable PAGE identities and per-page effective-input hashes |
| `INTERFACES` | typed imports, exports, calling contracts, capabilities |
| `DEPENDENCIES` | page graph and interface/implementation dependency kinds |
| `IR` | versioned target-independent typed IR, when included |
| `NATIVE` | target-keyed code, constants, relocations, and unwind information |
| `SOURCEMAP` | instruction/IR offsets to `.the` source spans |

Optional sections may contain debug data, profiling maps, documentation, and a
signature envelope. Executable code is never accepted from an unknown section.

## Page identity and validity

A PAGE record contains:

- package and source identity;
- canonical PAGE name and stable identifier;
- normalized opening metadata;
- effective-input hash;
- interface hash;
- dependency records;
- scheduled-degradation position and capability predicate, when present;
- offsets to IR, native slices, source maps, and initialization metadata.

The stable identifier is not the current prototype's FNV hash. The final identity
must be namespace-qualified and collision-safe. A fast short identifier may index
the file, but it must be verified against the full canonical identity before use.

A page is reusable only when its effective inputs match. Private implementation
changes do not invalidate dependents that use only an unchanged interface. Native
inlining or embedded constants create implementation dependencies and must be
recorded.

## Native slices

A native slice is selected by architecture, ABI, object convention, endianness,
pointer width, required CPU capabilities, and compilation profile—not by an OS
name alone. It contains position-independent code where supported, explicit
relocations, constant data, stack/unwind metadata, and entry offsets.

The loader validates capabilities before making code executable. Writable and
executable permissions must never coexist. Unsupported relocations, malformed
unwind data, hash failures, or interface mismatches reject the slice and fall back
to compatible IR or source compilation.

## Runtime selection

For every referenced PAGE, `the` selects in this order:

```text
valid compatible native slice
  -> valid compatible typed IR compiled for this target
  -> current PAGE source compiled for this run
  -> error when no valid representation is available
```

Loose source always takes the runtime-compilation path. Implementations may cache
its machine code in memory for the process, but do not persist it as a page unless
the user places it inside PAGE boundaries and runs `then`.

Runtime compilation and precompilation must produce identical observable
semantics. The selected path must be available through diagnostics so performance
and stale-cache behavior are explainable.

## Publication and trust

Writers create a complete temporary asset, flush it, validate it, then atomically
replace the destination. A failed compile never damages the last valid asset.
Concurrent writers use target-directory coordination and content validation rather
than trusting timestamps.

`.then` files are untrusted executable inputs. All arithmetic, offsets, counts,
recursion, allocation, decompression, relocations, signatures, and native code
must be validated under explicit limits. Signed distribution can be added without
making signatures mandatory for local builds.
