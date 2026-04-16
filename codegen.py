# ─────────────────────────────────────────────────────────────────────────────
#  CODE GENERATOR  –  walks the AST and emits Python source code
# ─────────────────────────────────────────────────────────────────────────────
import re
from parser import (ProgramNode, DeclNode, AssignNode, PrintNode, ForNode,
                    IntLit, RealLit, StrLit, IdentRef)

TYPE_MAP  = {'INTEGER': 'int', 'REAL': 'float', 'STRING': 'str'}
INTERP_RE = re.compile(r'\[(\w+)\]')


class CodeGenError(Exception):
    pass


class CodeGenerator:
    def __init__(self):
        self._lines       = []
        self._indent      = 0
        self.symbol_table = {}   # name → {type, value, scope}
        self._scope       = 'global'

    # ── helpers ───────────────────────────────────────────────────────────

    def _emit(self, line=''):
        self._lines.append('    ' * self._indent + line)

    def _indent_in(self):  self._indent += 1
    def _indent_out(self): self._indent -= 1

    def generate(self, node: ProgramNode) -> str:
        self._gen_program(node)
        return '\n'.join(self._lines)

    # ── program ───────────────────────────────────────────────────────────

    def _gen_program(self, node: ProgramNode):
        for stmt in node.body:
            self._gen_stmt(stmt)

    # ── dispatch ──────────────────────────────────────────────────────────

    def _gen_stmt(self, node):
        if   isinstance(node, DeclNode):   self._gen_decl(node)
        elif isinstance(node, AssignNode): self._gen_assign(node)
        elif isinstance(node, PrintNode):  self._gen_print(node)
        elif isinstance(node, ForNode):    self._gen_for(node)
        else:
            raise CodeGenError(f"Unknown AST node: {type(node)}")

    # ── declaration ───────────────────────────────────────────────────────

    def _gen_decl(self, node: DeclNode):
        py_type = TYPE_MAP[node.dtype]
        default = {'int': '0', 'float': '0.0', 'str': '""'}[py_type]
        default_val = {'int': 0, 'float': 0.0, 'str': ''}[py_type]
        for name in node.names:
            # add to symbol table with default value
            self.symbol_table[name] = {
                'type':  node.dtype,
                'value': default_val,
                'scope': self._scope
            }
            self._emit(f'{name}: {py_type} = {default}  # {node.dtype}')

    # ── assignment ────────────────────────────────────────────────────────

    def _gen_assign(self, node: AssignNode):
        rhs = self._gen_expr(node.value)
        # update symbol table value
        if node.name in self.symbol_table:
            self.symbol_table[node.name]['value'] = node.value.value \
                if hasattr(node.value, 'value') else rhs
        else:
            # for loop variable (e.g. I) — infer type
            self.symbol_table[node.name] = {
                'type':  'INTEGER',
                'value': node.value.value if hasattr(node.value, 'value') else rhs,
                'scope': self._scope
            }
        self._emit(f'{node.name} = {rhs}')

    # ── print ─────────────────────────────────────────────────────────────

    def _gen_print(self, node: PrintNode):
        raw = node.value.value
        if INTERP_RE.search(raw):
            py_str = INTERP_RE.sub(r'{\1}', raw)
            self._emit(f'print(f"{py_str}")')
        else:
            self._emit(f'print("{raw}")')

    # ── for loop ──────────────────────────────────────────────────────────

    def _gen_for(self, node: ForNode):
        prev_scope   = self._scope
        self._scope  = f'for({node.var})'

        # register loop variable in symbol table
        start_val = node.start.value if hasattr(node.start, 'value') else '?'
        self.symbol_table[node.var] = {
            'type':  'INTEGER',
            'value': start_val,
            'scope': self._scope
        }

        start = self._gen_expr(node.start)
        stop  = self._gen_expr(node.stop)
        self._emit(f'for {node.var} in range({start}, {stop} + 1):')
        self._indent_in()
        for stmt in node.body:
            self._gen_stmt(stmt)
        self._indent_out()

        self._scope = prev_scope

    # ── expression ────────────────────────────────────────────────────────

    def _gen_expr(self, node) -> str:
        if   isinstance(node, IntLit):   return str(node.value)
        elif isinstance(node, RealLit):  return repr(node.value)
        elif isinstance(node, StrLit):   return f'"{node.value}"'
        elif isinstance(node, IdentRef): return node.name
        else:
            raise CodeGenError(f"Unknown expression node: {type(node)}")
