# ─────────────────────────────────────────────
#  LEXER  –  converts source text into tokens
# ─────────────────────────────────────────────
import re

# Token types
TT_KEYWORD   = 'KEYWORD'
TT_IDENT     = 'IDENT'
TT_INTEGER   = 'INTEGER'
TT_REAL      = 'REAL'
TT_STRING    = 'STRING'
TT_ASSIGN    = 'ASSIGN'    # :=
TT_COMMA     = 'COMMA'
TT_NEWLINE   = 'NEWLINE'
TT_EOF       = 'EOF'

KEYWORDS = {'BEGIN', 'END', 'PRINT', 'INTEGER', 'REAL', 'STRING', 'FOR', 'TO'}


class Token:
    def __init__(self, type_, value, line):
        self.type  = type_
        self.value = value
        self.line  = line

    def __repr__(self):
        return f'Token({self.type}, {self.value!r}, line={self.line})'


class LexerError(Exception):
    pass


class Lexer:
    """
    Hand-written lexer.  Scans the source character by character and
    emits a flat list of Token objects.
    """

    def __init__(self, source: str):
        self.source = source
        self.pos    = 0
        self.line   = 1
        self.tokens = []

    # ── helpers ──────────────────────────────────────────────────────────

    def current(self):
        return self.source[self.pos] if self.pos < len(self.source) else None

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
        return ch

    def peek(self, offset=1):
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else None

    # ── public entry point ────────────────────────────────────────────────

    def tokenize(self):
        while self.pos < len(self.source):
            ch = self.current()

            # skip spaces / tabs (but NOT newlines)
            if ch in (' ', '\t', '\r'):
                self.advance()

            # newline → logical line separator
            elif ch == '\n':
                self.tokens.append(Token(TT_NEWLINE, '\\n', self.line))
                self.advance()

            # assignment operator  :=
            elif ch == ':':
                if self.peek() == '=':
                    self.advance(); self.advance()
                    self.tokens.append(Token(TT_ASSIGN, ':=', self.line))
                else:
                    raise LexerError(f"Line {self.line}: unexpected ':' (did you mean ':='?)")

            # comma
            elif ch == ',':
                self.advance()
                self.tokens.append(Token(TT_COMMA, ',', self.line))

            # string literal  "..."
            elif ch == '"':
                self.tokens.append(self._read_string())

            # number  (integer or real, optional leading minus handled in parser)
            elif ch.isdigit():
                self.tokens.append(self._read_number())

            # minus sign that starts a number literal  e.g. -3.56E-8
            elif ch == '-' and self.peek() and self.peek().isdigit():
                self.tokens.append(self._read_number())

            # identifier or keyword
            elif ch.isalpha() or ch == '_':
                self.tokens.append(self._read_word())

            else:
                raise LexerError(f"Line {self.line}: unknown character {ch!r}")

        self.tokens.append(Token(TT_EOF, None, self.line))
        return self.tokens

    # ── private scanners ─────────────────────────────────────────────────

    def _read_string(self):
        """Scan a double-quoted string, supporting [var] interpolation markers."""
        line = self.line
        self.advance()          # consume opening "
        buf = []
        while self.current() is not None and self.current() != '"':
            if self.current() == '\n':
                raise LexerError(f"Line {line}: unterminated string literal")
            buf.append(self.advance())
        if self.current() != '"':
            raise LexerError(f"Line {line}: unterminated string literal")
        self.advance()          # consume closing "
        return Token(TT_STRING, ''.join(buf), line)

    def _read_number(self):
        """
        Scan integer or real.
        Supports: 42  -7  3.14  -3.56E-8  4.567
        Grammar:  [-] digits [. digits] [E [-] digits]
        """
        line = self.line
        buf  = []

        if self.current() == '-':
            buf.append(self.advance())

        # integer part
        while self.current() and self.current().isdigit():
            buf.append(self.advance())

        is_real = False

        # fractional part
        if self.current() == '.':
            is_real = True
            buf.append(self.advance())
            while self.current() and self.current().isdigit():
                buf.append(self.advance())

        # exponent part
        if self.current() in ('E', 'e'):
            is_real = True
            buf.append(self.advance())
            if self.current() in ('+', '-'):
                buf.append(self.advance())
            while self.current() and self.current().isdigit():
                buf.append(self.advance())

        raw = ''.join(buf)
        if is_real:
            return Token(TT_REAL, float(raw), line)
        else:
            return Token(TT_INTEGER, int(raw), line)

    def _read_word(self):
        """Scan an identifier; classify as KEYWORD if it matches the keyword set."""
        line = self.line
        buf  = []
        while self.current() and (self.current().isalnum() or self.current() == '_'):
            buf.append(self.advance())
        word = ''.join(buf)
        tt   = TT_KEYWORD if word.upper() in KEYWORDS else TT_IDENT
        return Token(tt, word.upper() if tt == TT_KEYWORD else word, line)
