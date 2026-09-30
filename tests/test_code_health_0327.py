import ast
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1] / 'quietwriter'


def _statement_lists(node):
    """Yield statement lists whose order has normal sequential semantics."""
    for field in ('body', 'orelse', 'finalbody'):
        value = getattr(node, field, None)
        if isinstance(value, list) and value:
            yield value
    for handler in getattr(node, 'handlers', ()) or ():
        if getattr(handler, 'body', None):
            yield handler.body


def test_no_unreachable_statements_after_return_or_raise():
    """Catch valid-Python dead code such as the 0.32.4 startup regression."""
    files = list(PACKAGE_ROOT.rglob('*.py'))
    assert files, f'No Python files found under {PACKAGE_ROOT}'

    failures = []
    for path in files:
        source = path.read_text(encoding='utf-8')
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            for statements in _statement_lists(node):
                for index, statement in enumerate(statements[:-1]):
                    if isinstance(statement, (ast.Return, ast.Raise)):
                        next_statement = statements[index + 1]
                        owner = next(
                            (parent for parent in ast.walk(tree)
                             if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef))
                             and statement in ast.walk(parent)),
                            None,
                        )
                        owner_name = owner.name if owner is not None else '<module>'
                        failures.append(
                            f'{path}:{getattr(owner, "lineno", statement.lineno)} {owner_name}: '
                            f'{type(statement).__name__} on line {statement.lineno} '
                            f'is followed by unreachable code on line {next_statement.lineno}'
                        )
    assert failures == [], '\n'.join(failures)
