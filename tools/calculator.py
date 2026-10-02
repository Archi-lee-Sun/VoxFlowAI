"""A small, safe arithmetic calculator for VoxFlow AI."""

import ast
import math
import operator


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_FUNCTIONS = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
}


def _evaluate(node: ast.AST) -> int | float:
    """Evaluate only the explicitly supported arithmetic AST nodes."""
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value

    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("Exponent is too large.")
        return _BINARY_OPERATORS[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate(node.operand))

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _FUNCTIONS
        and not node.keywords
    ):
        return _FUNCTIONS[node.func.id](*(_evaluate(arg) for arg in node.args))

    raise ValueError("Expression contains an unsupported operation.")


def calculate(expression: str) -> str:
    """Calculate a basic arithmetic expression and return its result as text.

    Supports ``+``, ``-``, ``*``, ``/``, ``//``, ``%``, ``**``, parentheses,
    unary signs, and the ``sqrt``, ``abs``, and ``round`` functions.
    """
    if not isinstance(expression, str) or not expression.strip():
        return "Error: Please provide a math expression."

    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _evaluate(tree.body)
        if isinstance(result, float) and not math.isfinite(result):
            return "Error: Result is not a finite number."
        return str(result)
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError, OverflowError) as error:
        message = str(error) or "Invalid math expression."
        return f"Error: {message}"
