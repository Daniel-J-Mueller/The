# The

![The logo](images/The-Icon.png)

Language support for The (`.the`, `.then`).

## Features

- syntax highlighting for PAGEs, PROCs, ITERs, operations, values, and comments;
- folding and indentation for PAGE/PROC/ITER/IF/LOOP regions;
- bracket pairing for `()`, `[]`, and `{}`;
- `|` line comments and `||` block comments;
- highlighting for the `..` visual line continuation;
- a `the-lint` problem matcher for native linter diagnostics.

## Linter

The Windows x64 package includes `bin/win32-x64/the-lint.exe`. Configure a VS
Code task with:

```json
{
  "label": "Lint The",
  "type": "process",
  "command": "${extensionInstallFolder:the-language.the-official-language}/bin/win32-x64/the-lint.exe",
  "args": ["${file}"],
  "problemMatcher": "$the-lint"
}
```

The extension contains no extension-host runtime code. Language presentation is
declarative; linting remains in the native C tool.
