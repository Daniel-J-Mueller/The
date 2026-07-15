#!/usr/bin/env python3
"""Experimental native AOT backend for The's integer benchmark subset."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from the_runtime import TheError, compile_source, python_expression


VCVARS = Path("C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Auxiliary/Build/vcvars64.bat")


def emit_nodes(nodes: list, indent: int, output: list[str], declared: set[str]) -> None:
    pad = "    " * indent
    for node in nodes:
        if node[0] == "iter":
            _, line, variable, kind, expression, body = node
            if kind.lower() != "intthrough":
                raise TheError(f"line {line}: native prototype supports intthrough only")
            parts = [python_expression(part.strip()) for part in expression.split(",")]
            start, end = f"_start_{line}", f"_end_{line}"
            output.append(f"{pad}int64_t {start} = {parts[0]}, {end} = {parts[1]};")
            output.append(f"{pad}int64_t _step_{line} = {end} >= {start} ? 1 : -1;")
            output.append(
                f"{pad}for (int64_t {variable} = {start}; "
                f"_step_{line} > 0 ? {variable} <= {end} : {variable} >= {end}; "
                f"{variable} += _step_{line}) {{"
            )
            nested = set(declared)
            nested.add(variable)
            emit_nodes(body, indent + 1, output, nested)
            output.append(f"{pad}}}")
            continue

        line, statement = node[1], node[2]
        assignment = re.match(r"(?:OBJ\s+)?(\w+)\s*=\s*(.+)$", statement)
        if assignment:
            name, expression = assignment.group(1), python_expression(assignment.group(2))
            prefix = "int64_t " if name not in declared else ""
            declared.add(name)
            output.append(f"{pad}{prefix}{name} = {expression};")
        elif statement.startswith("RETURN "):
            returned = statement[7:]
            expression, separator, _ = returned.rpartition(" as ")
            output.append(f"{pad}return {python_expression(expression if separator else returned)};")
        else:
            raise TheError(f"line {line}: native prototype does not support: {statement}")


def lower_to_c(program: dict) -> str:
    output = ["#include <inttypes.h>", "#include <stdint.h>", "#include <stdio.h>", ""]
    for name, body in program["procedures"].items():
        output.append(f"static int64_t _the_{name}(void) {{")
        emit_nodes(body, 1, output, set())
        output.append("}")
        output.append("")
    result_name = "result"
    for node in program["procedures"][program["entry"]]:
        if node[0] == "stmt" and node[2].startswith("RETURN "):
            _, separator, alias = node[2][7:].rpartition(" as ")
            if separator:
                result_name = alias
    output.append("int main(void) {")
    output.append(f"    int64_t {result_name} = _the_{program['entry']}();")
    for node in program["top"]:
        if node[0] == "stmt" and node[2].startswith("OUT "):
            output.append(f'    printf("%" PRId64 "\\n", (int64_t)({node[2][4:]}));')
    output.append("    return 0;")
    output.append("}")
    return "\n".join(output) + "\n"


def build(source: Path, destination: Path, keep_c: Path | None = None) -> None:
    program = compile_source(source.read_text(encoding="utf-8"), str(source))
    c_source = lower_to_c(program)
    if not VCVARS.is_file():
        raise TheError(f"MSVC environment script not found: {VCVARS}")
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        generated = Path(directory) / (source.stem + ".c")
        generated.write_text(c_source, encoding="utf-8")
        if keep_c:
            keep_c.parent.mkdir(parents=True, exist_ok=True)
            keep_c.write_text(c_source, encoding="utf-8")
        build_script = Path(directory) / "build.cmd"
        build_script.write_text(
            f'@call "{VCVARS}" >nul\n'
            '@if errorlevel 1 exit /b %errorlevel%\n'
            f'@cl /nologo /O2 /GL /W4 /Fe:"{destination}" "{generated}" /link /LTCG\n',
            encoding="utf-8",
        )
        completed = subprocess.run([os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", str(build_script)])
        if completed.returncode:
            raise TheError("native compiler failed")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="the-native")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--emit-c", type=Path)
    args = parser.parse_args(argv)
    try:
        build(args.source, args.output, args.emit_c)
    except (OSError, UnicodeError, SyntaxError, TheError) as exc:
        print(f"the-native: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
