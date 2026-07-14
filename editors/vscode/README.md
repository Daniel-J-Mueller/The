# The

VS Code language support for `.the` source files.

## Features

- syntax highlighting for PAGEs, PROCs, ITERs, operations, values, and comments;
- folding and indentation for PAGE/PROC/ITER/IF/LOOP regions;
- bracket pairing for `()`, `[]`, and `{}`;
- `|` line comments and `||` block comments;
- highlighting for the `..` visual line continuation;
- a `the-lint` problem matcher for native linter diagnostics.

The extension contains no extension-host runtime code. Language presentation is
declarative; linting remains in the native C tool.
