# ─────────────────────────────────────────────────────────────────────────────
#  PARSER  –  recursive-descent parser that builds an AST
# ─────────────────────────────────────────────────────────────────────────────
from lexer import (Token, TT_KEYWORD, TT_IDENT, TT_INTEGER, TT_REAL,
                   TT_STRING, TT_ASSIGN, TT_COMMA, TT_NEWLINE, TT_EOF)

# ── AST node classes ──────────────────────────────────────────────────────────

class ProgramNode:
    """Root node: BEGIN … END"""
    def __init__(self, body):
        self.body = body          # list of statement nodes

class DeclNode:
    """INTEGER A, B, C  /  REAL D, E  /  STRING X, Y"""
    def __init__(self, dtype, names):
        self.dtype = dtype        # 'INTEGER' | 'REAL' | 'STRING'
        self.names = names        # list of str

class AssignNode:
    """A := expr"""
    def __init__(self, name, value):
        self.name  = name         # str
        self.value = value        # IntLit | RealLit | StrLit

class PrintNode:
    """PRINT "…" """
    def __init__(self, value):
        self.value = value        # StrLit (may contain [var] markers)

class ForNode:
    """FOR I := start TO end  …body…  END"""
    def __init__(self, var, start, stop, body):
        self.var   = var          # str
        self.start = start        # IntLit | RealLit
        self.stop  = stop
        self.body  = body         # list of statement nodes

# literal value wrappers
class IntLit:
    def __init__(self, v): self.value = v
class RealLit:
    def __init__(self, v): self.value = v
class StrLit:
    def __init__(self, v): self.value = v
class IdentRef:
    def __init__(self, name): self.name = name


# ── Parser ────────────────────────────────────────────────────────────────────

class ParseError(Exception):
    pass


class Parser:
    """
    Recursive-descent parser.

    Grammar (simplified):
        program     ::= BEGIN stmts END
        stmts       ::= stmt*
        stmt        ::= decl | assign | print | for_stmt
        decl        ::= ('INTEGER'|'REAL'|'STRING') IDENT (',' IDENT)*
        assign      ::= IDENT ':=' expr
        print       ::= PRINT STRING
        for_stmt    ::= FOR IDENT ':=' expr TO expr stmts END
        expr        ::= INTEGER | REAL | STRING | IDENT
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0

    # ── token navigation ──────────────────────────────────────────────────

    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, offset=1) -> Token:
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def skip_newlines(self):
        while self.current().type == TT_NEWLINE:
            self.advance()

    def expect(self, type_=None, value=None) -> Token:
        self.skip_newlines()
        tok = self.current()
        if type_  and tok.type  != type_:
            raise ParseError(f"Line {tok.line}: expected type {type_!r}, got {tok.type!r} ({tok.value!r})")
        if value  and tok.value != value:
            raise ParseError(f"Line {tok.line}: expected {value!r}, got {tok.value!r}")
        return self.advance()

    # ── entry point ───────────────────────────────────────────────────────

    def parse(self) -> ProgramNode:
        self.skip_newlines()
        self.expect(TT_KEYWORD, 'BEGIN')
        body = self._parse_stmts(stop_at={'END'})
        self.expect(TT_KEYWORD, 'END')
        self.skip_newlines()
        if self.current().type != TT_EOF:
            raise ParseError(f"Line {self.current().line}: unexpected token after END")
        return ProgramNode(body)

    # ── statement list ────────────────────────────────────────────────────

    def _parse_stmts(self, stop_at: set) -> list:
        stmts = []
        while True:
            self.skip_newlines()
            tok = self.current()
            if tok.type == TT_EOF:
                break
            if tok.type == TT_KEYWORD and tok.value in stop_at:
                break
            stmts.append(self._parse_stmt())
        return stmts

    # ── single statement ──────────────────────────────────────────────────

    def _parse_stmt(self):
        self.skip_newlines()
        tok = self.current()

        if tok.type == TT_KEYWORD:
            if tok.value in ('INTEGER', 'REAL', 'STRING'):
                return self._parse_decl()
            elif tok.value == 'PRINT':
                return self._parse_print()
            elif tok.value == 'FOR':
                return self._parse_for()
            else:
                raise ParseError(f"Line {tok.line}: unexpected keyword {tok.value!r}")

        elif tok.type == TT_IDENT:
            return self._parse_assign()

        else:
            raise ParseError(f"Line {tok.line}: unexpected token {tok.value!r}")

    # ── declaration ───────────────────────────────────────────────────────

    def _parse_decl(self) -> DeclNode:
        dtype = self.advance().value          # INTEGER / REAL / STRING
        names = []
        names.append(self.expect(TT_IDENT).value)
        while self.current().type == TT_COMMA:
            self.advance()                    # consume comma
            names.append(self.expect(TT_IDENT).value)
        return DeclNode(dtype, names)

    # ── assignment ────────────────────────────────────────────────────────

    def _parse_assign(self) -> AssignNode:
        name = self.advance().value           # identifier
        self.expect(TT_ASSIGN)
        value = self._parse_expr()
        return AssignNode(name, value)

    # ── print ─────────────────────────────────────────────────────────────

    def _parse_print(self) -> PrintNode:
        self.advance()                        # consume PRINT
        tok = self.expect(TT_STRING)
        return PrintNode(StrLit(tok.value))

    # ── for loop ──────────────────────────────────────────────────────────

    def _parse_for(self) -> ForNode:
        self.advance()                        # consume FOR
        var   = self.expect(TT_IDENT).value
        self.expect(TT_ASSIGN)
        start = self._parse_expr()
        self.expect(TT_KEYWORD, 'TO')
        stop  = self._parse_expr()
        body  = self._parse_stmts(stop_at={'END'})
        self.expect(TT_KEYWORD, 'END')
        return ForNode(var, start, stop, body)

    # ── expression (right-hand side value) ───────────────────────────────

    def _parse_expr(self):
        self.skip_newlines()
        tok = self.current()
        if tok.type == TT_INTEGER:
            self.advance()
            return IntLit(tok.value)
        elif tok.type == TT_REAL:
            self.advance()
            return RealLit(tok.value)
        elif tok.type == TT_STRING:
            self.advance()
            return StrLit(tok.value)
        elif tok.type == TT_IDENT:
            self.advance()
            return IdentRef(tok.value)
        else:
            raise ParseError(f"Line {tok.line}: expected expression, got {tok.type!r} ({tok.value!r})")
