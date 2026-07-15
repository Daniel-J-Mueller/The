# Changelog

## 0.2.0

- Added the complete `The` dark color theme based on the project plum, slate,
  teal, cream, and crimson palette.
- Replaced borrowed language-theme colors with custom muted pastel derivatives.

## 0.1.8

- Colored `into` yellow, `at` orange, `intthrough` and `stridethrough` red, and
  `end`, `beginning`, and `value` green using distinct TextMate scopes.

## 0.1.7

- Moved iterator and placement words to the visible keyword scope used by `ITER`
  and `PUT`: `intthrough`, `stridethrough`, `into`, `at`, `end`, `beginning`,
  `value`, and `as`.

## 0.1.6

- Made standalone `||` rows unambiguous multiline comment boundaries.
- Added a separate rule for single-line `|| comment ||` blocks.

## 0.1.5

- Fixed continued-comment highlighting by matching TextMate's synthetic physical
  newline instead of the line-end position.
- Added an Oniguruma/TextMate tokenization verification for the continuation rule.

## 0.1.4

- Styled `PROCEND` with the same scope as `PROC`.
- Styled `PAGE` and `PAGEEND` with one brown constant scope.
- Corrected `..` comment continuation across Windows CRLF physical lines.
- Highlighted `into`, `at`, `end`, `beginning`, `value`, and `as` as word operators.

## 0.1.3

- Prioritized multiline highlighting for `|` comments continued with `..`.
- Renamed ITER forms to `intthrough` and `stridethrough`.
- Validated `PUT`, `into`, `at`, `end`, `beginning`, and `value` as one operation.

## 0.1.2

- Continued `|` comments across physical lines joined by `..`.
- Added an end-of-file diagnostic for unfinished line continuations.

## 0.1.1

- Added a repository-ready VS Code lint task and Problems-panel diagnostics.
- Added multi-file linting plus `--help` and `--version` CLI modes.
- Standardized the extension identity as `the-language.the-official-language`.

## 0.1.0

- Bundled the native Windows x64 structural linter.
- Added `.then` compiled-asset recognition.
- Added PAGE/PROC/ITER/PUT diagnostics through the `the-lint` problem matcher.

## 0.0.1

- Initial `.the` language registration, highlighting, folding, comments, and
  native-linter problem matcher.
- Added the complete The logo as the Marketplace icon.
