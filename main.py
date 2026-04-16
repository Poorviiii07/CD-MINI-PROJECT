#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
#  MAIN  –  MiniLang Compiler
#  Usage:  python main.py sample.txt
# ─────────────────────────────────────────────────────────────────────────────
import sys

from lexer   import Lexer,   LexerError
from parser  import Parser,  ParseError
from codegen import CodeGenerator, CodeGenError


# ── Table printing helpers ────────────────────────────────────────────────────

def print_table(headers, rows):
    """Print a plain-text table given headers and rows (list of lists)."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    fmt = "|" + "|".join(f" {{:<{w}}} " for w in col_widths) + "|"

    print(sep)
    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        print(fmt.format(*[str(c) for c in row]))
    print(sep)


def print_parse_tree(node, indent=0):
    """Recursively print the AST as an indented parse tree."""
    from parser import (ProgramNode, DeclNode, AssignNode, PrintNode, ForNode,
                        IntLit, RealLit, StrLit, IdentRef)
    prefix = "    " * indent
    branch = "└── " if indent > 0 else ""

    if isinstance(node, ProgramNode):
        print(f"{prefix}Program")
        for child in node.body:
            print_parse_tree(child, indent + 1)

    elif isinstance(node, DeclNode):
        print(f"{prefix}{branch}Declare ({node.dtype})")
        for name in node.names:
            print(f"{'    ' * (indent+1)}└── Identifier: {name}")

    elif isinstance(node, AssignNode):
        print(f"{prefix}{branch}Assign: {node.name}")
        print_parse_tree(node.value, indent + 1)

    elif isinstance(node, PrintNode):
        print(f"{prefix}{branch}Print")
        print_parse_tree(node.value, indent + 1)

    elif isinstance(node, ForNode):
        print(f"{prefix}{branch}For: {node.var}")
        print(f"{'    ' * (indent+1)}└── Start:")
        print_parse_tree(node.start, indent + 2)
        print(f"{'    ' * (indent+1)}└── Stop:")
        print_parse_tree(node.stop, indent + 2)
        print(f"{'    ' * (indent+1)}└── Body:")
        for child in node.body:
            print_parse_tree(child, indent + 2)

    elif isinstance(node, IntLit):
        print(f"{prefix}{branch}IntLit: {node.value}")
    elif isinstance(node, RealLit):
        print(f"{prefix}{branch}RealLit: {node.value}")
    elif isinstance(node, StrLit):
        print(f"{prefix}{branch}StrLit: \"{node.value}\"")
    elif isinstance(node, IdentRef):
        print(f"{prefix}{branch}IdentRef: {node.name}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <source_file>")
        sys.exit(1)

    source_file = sys.argv[1]
    try:
        with open(source_file, 'r') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: file {source_file!r} not found.")
        sys.exit(1)

    # ── Phase 1: Lexical Analysis ─────────────────────────────────────────
    try:
        lexer  = Lexer(source)
        tokens = lexer.tokenize()
    except LexerError as e:
        print(f"Lexer error: {e}")
        sys.exit(1)

    print("=" * 60)
    print(" 1. TOKENS")
    print("=" * 60)
    visible = [t for t in tokens if t.type not in ('NEWLINE', 'EOF')]
    rows = [[i+1, t.type, repr(t.value), t.line] for i, t in enumerate(visible)]
    print_table(["#", "Type", "Value", "Line"], rows)

    # ── Phase 2: Parsing ──────────────────────────────────────────────────
    try:
        parser = Parser(tokens)
        ast    = parser.parse()
    except ParseError as e:
        print(f"Parser error: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(" 2. PARSE TREE")
    print("=" * 60)
    print_parse_tree(ast)

    # ── Phase 3: Code Generation + Symbol Table ───────────────────────────
    try:
        gen  = CodeGenerator()
        code = gen.generate(ast)
    except CodeGenError as e:
        print(f"CodeGen error: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(" 3. SYMBOL TABLE")
    print("=" * 60)
    sym_rows = []
    for name, info in gen.symbol_table.items():
        sym_rows.append([name, info['type'], info['value'], info['scope']])
    print_table(["Name", "Type", "Value", "Scope"], sym_rows)

    # ── Phase 4: Program Output ───────────────────────────────────────────
    print("\n" + "=" * 60)
    print(" 4. FINAL OUTPUT")
    print("=" * 60)
    exec(compile(code, '<generated>', 'exec'), {})


if __name__ == '__main__':
    main()
