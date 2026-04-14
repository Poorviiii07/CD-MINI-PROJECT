#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
#  MAIN  –  ties all compiler phases together
#
#  Usage:
#      python main.py sample.txt              # compile + run
#      python main.py sample.txt --emit       # compile + print generated code
# ─────────────────────────────────────────────────────────────────────────────
import sys
import argparse

from lexer   import Lexer,   LexerError
from parser  import Parser,  ParseError
from codegen import CodeGenerator, CodeGenError


def compile_source(source: str) -> str:
    """Full pipeline: source text → generated Python code string."""

    lexer  = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast    = parser.parse()
    gen    = CodeGenerator()
    code   = gen.generate(ast)

    return code


def main():
    ap = argparse.ArgumentParser(description='MiniLang Compiler')
    ap.add_argument('source', help='Source file to compile')
    ap.add_argument('--emit', action='store_true',
                    help='Print generated Python code instead of running it')
    args = ap.parse_args()

    try:
        with open(args.source, 'r') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: file {args.source!r} not found.")
        sys.exit(1)

    try:
        code = compile_source(source)
    except LexerError  as e: print(f"\nLexer error:  {e}");  sys.exit(1)
    except ParseError  as e: print(f"\nParser error: {e}");  sys.exit(1)
    except CodeGenError as e: print(f"\nCodeGen error: {e}"); sys.exit(1)

    if args.emit:
        print("\n" + "─" * 60)
        print("Generated Python code:")
        print("─" * 60)
        print(code)
        print("─" * 60)
    else:
        print("\nProgram Output:")
        print("─" * 60)
        exec(compile(code, '<generated>', 'exec'), {})


if __name__ == '__main__':
    main()
