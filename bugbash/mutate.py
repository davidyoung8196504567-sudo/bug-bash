"""Bug injection: generate single-change mutants of a reference implementation.

Each mutant applies exactly one mutation operator at one site in the AST, so
every injected bug is small, local and individually identifiable.
"""
import ast
import copy
from dataclasses import dataclass

COMPARE_SWAPS = {
    ast.Lt: ast.LtE, ast.LtE: ast.Lt,
    ast.Gt: ast.GtE, ast.GtE: ast.Gt,
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
    ast.In: ast.NotIn, ast.NotIn: ast.In,
}
BINOP_SWAPS = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult}
BOOLOP_SWAPS = {ast.And: ast.Or, ast.Or: ast.And}


@dataclass
class Mutant:
    mutant_id: str
    operator: str
    line: int
    description: str
    source: str


def _sites(tree):
    """Yield (node, operator_name, apply_fn, description) for every mutation site."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for i, op in enumerate(node.ops):
                new = COMPARE_SWAPS.get(type(op))
                if new:
                    yield (node, "compare_swap",
                           lambda n, i=i, new=new: n.ops.__setitem__(i, new()),
                           f"{type(op).__name__} -> {new.__name__}")
        elif isinstance(node, ast.BinOp):
            new = BINOP_SWAPS.get(type(node.op))
            if new:
                yield (node, "binop_swap",
                       lambda n, new=new: setattr(n, "op", new()),
                       f"{type(node.op).__name__} -> {new.__name__}")
        elif isinstance(node, ast.BoolOp):
            new = BOOLOP_SWAPS.get(type(node.op))
            if new:
                yield (node, "boolop_swap",
                       lambda n, new=new: setattr(n, "op", new()),
                       f"{type(node.op).__name__} -> {new.__name__}")
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            yield (node, "drop_not", None, "remove 'not'")
        elif (isinstance(node, ast.Constant) and type(node.value) is int):
            for delta in (1, -1):
                yield (node, "const_off_by_one",
                       lambda n, d=delta: setattr(n, "value", n.value + d),
                       f"{node.value} -> {node.value + delta}")


class _DropNot(ast.NodeTransformer):
    """Replace one specific `not x` node with `x`."""

    def __init__(self, target):
        self.target = target

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        return node.operand if node is self.target else node


def generate_mutants(source: str, task_name: str = "task") -> list[Mutant]:
    tree = ast.parse(source)
    original_nodes = list(ast.walk(tree))
    sites = list(_sites(tree))
    mutants = []
    for k, (node, operator, apply_fn, desc) in enumerate(sites):
        mutated = copy.deepcopy(tree)
        # Locate the same node in the copy by walk order.
        target = list(ast.walk(mutated))[original_nodes.index(node)]
        if operator == "drop_not":
            mutated = _DropNot(target).visit(mutated)
        else:
            apply_fn(target)
        ast.fix_missing_locations(mutated)
        mutants.append(Mutant(
            mutant_id=f"BB-{task_name}-{k:03d}",
            operator=operator,
            line=getattr(node, "lineno", 0),
            description=desc,
            source=ast.unparse(mutated),
        ))
    return mutants
