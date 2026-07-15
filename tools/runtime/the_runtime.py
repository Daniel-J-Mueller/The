#!/usr/bin/env python3
"""Small reference runtime and .then compiler for The's syntax experiment."""

from __future__ import annotations

import argparse
import ast
import hashlib
import marshal
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

FORMAT = b"THEBC001"
VERSION = 2
HOST_TAG = bytes(sys.version_info[:2])


class TheError(Exception):
    pass


def logical_lines(text: str) -> list[tuple[int, str]]:
    physical = text.splitlines()
    joined: list[tuple[int, str]] = []
    i = 0
    while i < len(physical):
        number, line = i + 1, physical[i]
        while line.rstrip().endswith("..") and i + 1 < len(physical):
            line = line.rstrip()[:-2] + physical[i + 1].lstrip()
            i += 1
        joined.append((number, line))
        i += 1

    result: list[tuple[int, str]] = []
    in_block = False
    for number, line in joined:
        out, p = [], 0
        while p < len(line):
            if line.startswith("||", p):
                in_block = not in_block
                p += 2
            elif in_block:
                p += 1
            elif line[p] == "|":
                break
            else:
                out.append(line[p])
                p += 1
        value = "".join(out).strip()
        if value:
            result.append((number, value.rstrip(":")))
    if in_block:
        raise TheError("unterminated || comment")
    return result


def compile_source(text: str, source_name: str) -> dict:
    lines = logical_lines(text)
    procedures: dict[str, list] = {}
    entry = None
    top: list = []
    current = top
    stack: list[tuple[str, list]] = []
    page = None

    for line_no, line in lines:
        if line.startswith("PAGE "):
            if page is not None:
                raise TheError(f"{source_name}:{line_no}: nested PAGE")
            page = line[5:].split()[0]
            continue
        if line.startswith("PAGEEND "):
            name = line[8:].strip()
            if name != page:
                raise TheError(f"{source_name}:{line_no}: PAGEEND {name} does not match {page}")
            page = None
            continue
        if line.startswith("PROC "):
            name = line[5:].split("(", 1)[0].strip()
            body: list = []
            procedures[name] = body
            stack.append(("PROC", current))
            current = body
            continue
        if line == "PROCEND":
            if not stack or stack[-1][0] != "PROC":
                raise TheError(f"{source_name}:{line_no}: PROCEND without PROC")
            current = stack.pop()[1]
            continue
        if line.startswith("ENTRY "):
            entry = line[6:].strip()
            continue
        m = re.match(r"ITER\s+(\w+)\s+(?:IN\s+(.+)|(intthrough|stridethrough)\s*\((.*)\))$", line, re.I)
        if m:
            node = ["iter", line_no, m.group(1), m.group(3) or "in", m.group(4) or m.group(2), []]
            current.append(node)
            stack.append(("ITER", current))
            current = node[5]
            continue
        if line == "ITEREND":
            if not stack or stack[-1][0] != "ITER":
                raise TheError(f"{source_name}:{line_no}: ITEREND without ITER")
            current = stack.pop()[1]
            continue
        current.append(["stmt", line_no, line])
    if stack or page is not None:
        raise TheError(f"{source_name}: unclosed block")
    if not entry:
        raise TheError(f"{source_name}: missing ENTRY")
    if entry not in procedures:
        raise TheError(f"{source_name}: ENTRY procedure {entry!r} is not defined")
    return {"entry": entry, "procedures": procedures, "top": top}


class SafeEval(ast.NodeVisitor):
    allowed = (ast.Expression, ast.Constant, ast.Name, ast.List, ast.Tuple, ast.BinOp,
               ast.UnaryOp, ast.BoolOp, ast.Compare, ast.Load, ast.Add, ast.Sub,
               ast.Mult, ast.Div, ast.Mod, ast.USub, ast.UAdd, ast.Eq, ast.NotEq,
               ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.And, ast.Or, ast.Not)

    def generic_visit(self, node):
        if not isinstance(node, self.allowed):
            raise TheError(f"unsupported expression: {ast.dump(node, include_attributes=False)}")
        super().generic_visit(node)


@lru_cache(maxsize=256)
def compile_expression(expr: str):
    expr = re.sub(r"\bTRUE\b", "True", expr, flags=re.I)
    expr = re.sub(r"\bFALSE\b", "False", expr, flags=re.I)
    expr = re.sub(r"\bOPEN\.(\w+)\b", r"\1", expr)
    tree = ast.parse(expr, mode="eval")
    SafeEval().visit(tree)
    return compile(tree, "<the-expression>", "eval", optimize=2)


def evaluate(expr: str, local: dict, global_: dict):
    names = dict(global_)
    names.update(local)
    try:
        return eval(compile_expression(expr), {"__builtins__": {}}, names)
    except (NameError, TypeError, ZeroDivisionError) as exc:
        raise TheError(str(exc)) from exc


def python_expression(expr: str) -> str:
    expr = re.sub(r"\bTRUE\b", "True", expr, flags=re.I)
    expr = re.sub(r"\bFALSE\b", "False", expr, flags=re.I)
    return re.sub(r"\bOPEN\.(\w+)\b", r"\1", expr)


def emit_nodes(nodes: list, indent: int, output: list[str]) -> None:
    pad = "    " * indent
    for node in nodes:
        if node[0] == "iter":
            _, _, variable, kind, expression, body = node
            if kind.lower() == "in":
                iterable = python_expression(expression)
            elif kind.lower() == "intthrough":
                parts = [python_expression(part.strip()) for part in expression.split(",")]
                iterable = f"_intthrough({parts[0]}, {parts[1]})"
            else:
                parts = [python_expression(part.strip()) for part in expression.split(",")]
                iterable = f"_stride({parts[0]}, {parts[1]}, {parts[2]})"
            output.append(f"{pad}for {variable} in {iterable}:")
            emit_nodes(body, indent + 1, output)
            continue
        statement = node[2]
        assignment = re.match(r"(?:OBJ\s+)?(\w+)\s*=\s*(.+)$", statement)
        if assignment:
            output.append(f"{pad}{assignment.group(1)} = {python_expression(assignment.group(2))}")
        elif statement.startswith("OUT(") and statement.endswith(")"):
            expressions = [python_expression(x.strip()) for x in statement[4:-1].split(",")]
            output.append(f"{pad}print(' '.join(_render(x) for x in [{', '.join(expressions)}]))")
        elif statement.startswith("OUT "):
            output.append(f"{pad}print(_render({python_expression(statement[4:])}))")
        elif statement.startswith("PUT "):
            match = re.match(r"PUT\s+(.+?)\s+into\s+(\w+)(?:\s+at\s+(end|beginning|value))?$", statement)
            if not match:
                raise TheError(f"line {node[1]}: malformed PUT")
            value, target, position = python_expression(match.group(1)), match.group(2), match.group(3) or "end"
            if position == "end": output.append(f"{pad}{target}.append({value})")
            elif position == "beginning": output.append(f"{pad}{target}.insert(0, {value})")
            else: output.append(f"{pad}{target}.insert(next((i for i, x in enumerate({target}) if x > {value}), len({target})), {value})")
        elif statement.startswith("RETURN "):
            returned = statement[7:]
            expression, separator, _ = returned.rpartition(" as ")
            output.append(f"{pad}return {python_expression(expression if separator else returned)}")
        else:
            raise TheError(f"line {node[1]}: native backend does not support: {statement}")


def lower_to_host_bytecode(program: dict, source_name: str):
    output = ["# generated host-bytecode input"]
    for name, body in program["procedures"].items():
        output.append(f"def {name}():")
        emit_nodes(body, 1, output)
        if not body: output.append("    pass")
    top_outputs = []
    for node in program["top"]:
        if node[0] == "stmt" and node[2].startswith("OUT "):
            top_outputs.append(node)
        else:
            emit_nodes([node], 0, output)
    return_name = None
    for node in program["procedures"][program["entry"]]:
        if node[0] == "stmt" and node[2].startswith("RETURN "):
            _, separator, return_name = node[2][7:].rpartition(" as ")
            if not separator: return_name = None
    call = f"{program['entry']}()"
    output.append(f"{return_name} = {call}" if return_name else call)
    emit_nodes(top_outputs, 0, output)
    return compile("\n".join(output) + "\n", source_name, "exec", optimize=2)


@dataclass
class Returned:
    value: object
    name: str | None


def render(value):
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return format(value, ".15g")
    if isinstance(value, list):
        return "[" + ", ".join(render(v) for v in value) + "]"
    return str(value)


def run_block(nodes, local, global_):
    for node in nodes:
        if node[0] == "iter":
            _, line_no, variable, kind, expression, body = node
            if kind.lower() == "in":
                values = evaluate(expression, local, global_)
            else:
                parts = [p.strip() for p in expression.split(",")]
                nums = [evaluate(p, local, global_) for p in parts]
                start, end = nums[0], nums[1]
                step = 1 if kind == "intthrough" else nums[2]
                values = stride(start, end, step)
            for value in values:
                local[variable] = value
                result = run_block(body, local, global_)
                if result:
                    return result
            continue

        _, line_no, statement = node
        m = re.match(r"(?:OBJ\s+)?(\w+)\s*=\s*(.+)$", statement)
        if m:
            local[m.group(1)] = evaluate(m.group(2), local, global_)
        elif statement.startswith("OUT(") and statement.endswith(")"):
            values = [evaluate(x.strip(), local, global_) for x in statement[4:-1].split(",")]
            print(" ".join(render(v) for v in values))
        elif statement.startswith("OUT "):
            print(render(evaluate(statement[4:], local, global_)))
        elif statement.startswith("PUT "):
            m = re.match(r"PUT\s+(.+?)\s+into\s+(\w+)(?:\s+at\s+(end|beginning|value))?$", statement)
            if not m:
                raise TheError(f"line {line_no}: malformed PUT")
            value, target, position = evaluate(m.group(1), local, global_), m.group(2), m.group(3) or "end"
            sequence = local[target]
            if position == "beginning": sequence.insert(0, value)
            elif position == "end": sequence.append(value)
            else:
                index = next((i for i, item in enumerate(sequence) if item > value), len(sequence))
                sequence.insert(index, value)
        elif statement.startswith("RETURN "):
            returned = statement[7:]
            expression, separator, name = returned.rpartition(" as ")
            if not separator:
                expression, name = returned, None
            return Returned(evaluate(expression, local, global_), name)
        else:
            raise TheError(f"line {line_no}: unsupported statement: {statement}")
    return None


def execute(program: dict):
    global_: dict = {}
    before_entry = [node for node in program["top"] if not (node[0] == "stmt" and node[2].startswith("OUT "))]
    run_block(before_entry, global_, global_)
    result = run_block(program["procedures"][program["entry"]], {}, global_)
    if result and result.name:
        global_[result.name] = result.value
    # Statements after ENTRY remain top-level and observe the entry result.
    for node in program["top"]:
        if node[0] == "stmt" and node[2].startswith("OUT "):
            run_block([node], global_, global_)


def stride(first, last, step):
    if step == 0:
        raise TheError("stride step cannot be zero")
    step = abs(step) * (1 if last >= first else -1)
    if step > 0:
        while first <= last:
            yield first
            first += step
    else:
        while first >= last:
            yield first
            first += step


def intthrough(first, last):
    step = 1 if last >= first else -1
    return range(first, last + step, step)


def execute_bytecode(code):
    exec(code, {"_render": render, "_stride": stride, "_intthrough": intthrough})


def asset_path(source: Path) -> Path:
    return source.with_suffix(".then")


def make_asset(source: Path) -> Path:
    data = source.read_bytes()
    text = data.decode("utf-8")
    program = compile_source(text, str(source))
    code = lower_to_host_bytecode(program, str(source))
    payload = FORMAT + HOST_TAG + hashlib.sha256(data).digest() + marshal.dumps(code)
    destination = asset_path(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=destination.name + ".", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, destination)
    finally:
        if os.path.exists(temp_name): os.unlink(temp_name)
    return destination


def load_program(source: Path):
    data = source.read_bytes()
    asset = asset_path(source)
    if asset.exists():
        try:
            payload = asset.read_bytes()
            if payload[:8] == FORMAT and payload[8:10] == HOST_TAG and payload[10:42] == hashlib.sha256(data).digest():
                return marshal.loads(payload[42:])
        except (OSError, ValueError, EOFError, TypeError):
            pass
    program = compile_source(data.decode("utf-8"), str(source))
    return lower_to_host_bytecode(program, str(source))


def main(argv=None):
    parser = argparse.ArgumentParser(prog=Path(sys.argv[0]).name)
    parser.add_argument("mode", choices=("run", "compile"))
    parser.add_argument("source", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.source.suffix != ".the": raise TheError("expected a .the source file")
        if args.mode == "compile":
            print(make_asset(args.source))
        else:
            compiled = load_program(args.source)
            execute_bytecode(compiled) if isinstance(compiled, type(compile("", "", "exec"))) else execute(compiled)
    except (OSError, UnicodeError, SyntaxError, TheError) as exc:
        print(f"{parser.prog}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
