"""Add contracts to the documentation."""
import ast
import inspect
from typing import List, Callable, Any, Optional

import asttokens
import icontract
import icontract._represent

import sphinx_icontract_meta

__title__ = sphinx_icontract_meta.__title__
__description__ = sphinx_icontract_meta.__description__
__url__ = sphinx_icontract_meta.__url__
__version__ = sphinx_icontract_meta.__version__
__author__ = sphinx_icontract_meta.__author__
__author_email__ = sphinx_icontract_meta.__author_email__
__license__ = sphinx_icontract_meta.__license__
__copyright__ = sphinx_icontract_meta.__copyright__

# Use protected methods from icontract and tightly couple with it. Making these specific methods "public" would
# rather add noise to the most clients of icontract library.
# pylint: disable=protected-access


def _negate_compare_text(atok: asttokens.ASTTokens, node: ast.Compare) -> str:
    """
    Generate the text representing the negation of the comparison node.

    :param atok:
        parsing obtained with ``asttokens`` so that we can access the last tokens of a node.

        The standard ``ast`` module provides only the first token of an AST node. In lack of concrete syntax tree,
        getting text from first to last token is currently the simplest approach.
    :param node: AST node representing the comparison in a condition
    :return: text representation of the node's negation
    """
    assert len(node.ops) == 1, "A single comparison expected, but got: {}".format(len(node.ops))
    assert len(node.comparators) == 1, "A single comparator expected, but got: {}".format(len(node.comparators))

    operator = node.ops[0]
    left = node.left
    right = node.comparators[0]

    left_text = atok.get_text(node=left)
    right_text = atok.get_text(node=right)

    text = ''

    if isinstance(operator, ast.Eq):
        text = '{} != {}'.format(left_text, right_text)

    elif isinstance(operator, ast.NotEq):
        text = '{} == {}'.format(left_text, right_text)

    elif isinstance(operator, ast.Lt):
        text = '{} >= {}'.format(left_text, right_text)

    elif isinstance(operator, ast.LtE):
        text = '{} > {}'.format(left_text, right_text)

    elif isinstance(operator, ast.Gt):
        text = '{} <= {}'.format(left_text, right_text)

    elif isinstance(operator, ast.GtE):
        text = '{} < {}'.format(left_text, right_text)

    elif isinstance(operator, ast.Is):
        text = '{} is not {}'.format(left_text, right_text)

    elif isinstance(operator, ast.IsNot):
        text = '{} is {}'.format(left_text, right_text)

    elif isinstance(operator, ast.In):
        text = '{} not in {}'.format(left_text, right_text)

    elif isinstance(operator, ast.NotIn):
        text = '{} in {}'.format(left_text, right_text)

    else:
        raise NotImplementedError("Unhandled comparison operator: {}".format(operator))

    return text


def _format_condition(condition: Callable[..., bool]) -> str:
    """Format condition as reST."""
    lambda_inspection = icontract._represent.inspect_lambda_condition(condition=condition)

    if lambda_inspection is None:
        return ':py:func:`{}`'.format(condition.__name__)

    lambda_ast_node = lambda_inspection.node
    assert isinstance(lambda_ast_node, ast.Lambda)

    body_node = lambda_ast_node.body

    text = None  # type: Optional[str]
    if isinstance(body_node, ast.BoolOp) and isinstance(body_node.op, ast.Or) and len(body_node.values) == 2:
        left, right = body_node.values

        if isinstance(left, ast.UnaryOp) and isinstance(left.op, ast.Not):
            # Handle the case: not A or B is transformed to A => B
            text = ':code:`{}` ⇒ :code:`{}`'.format(
                lambda_inspection.atok.get_text(node=left.operand), lambda_inspection.atok.get_text(node=right))

        elif isinstance(left, (ast.UnaryOp, ast.BinOp, ast.GeneratorExp, ast.IfExp)):
            text = ':code:`not ({})` ⇒ :code:`{}`'.format(
                lambda_inspection.atok.get_text(node=left), lambda_inspection.atok.get_text(node=right))

        elif isinstance(left, ast.Compare) and len(left.ops) == 1:
            text = ':code:`{}` ⇒ :code:`{}`'.format(
                _negate_compare_text(atok=lambda_inspection.atok, node=left),
                lambda_inspection.atok.get_text(node=right))

        elif isinstance(left, (ast.Call, ast.Attribute, ast.Name, ast.Subscript, ast.Index, ast.Slice, ast.ExtSlice,
                               ast.ListComp, ast.SetComp, ast.DictComp)):
            text = ':code:`not {}` ⇒ :code:`{}`'.format(
                lambda_inspection.atok.get_text(node=left), lambda_inspection.atok.get_text(node=right))

    elif isinstance(body_node, ast.IfExp) and isinstance(body_node.orelse, ast.NameConstant) and body_node.orelse.value:
        text = ':code:`{}` ⇒ :code:`{}`'.format(
            lambda_inspection.atok.get_text(node=body_node.test), lambda_inspection.atok.get_text(node=body_node.body))

    if text is None:
        # None of the previous reformatings worked, take the default approach.
        text = ':code:`{}`'.format(lambda_inspection.atok.get_text(node=body_node))

    return text


@icontract.pre(lambda prefix: prefix is None or prefix == prefix.strip())
@icontract.post(lambda preconditions, result: not preconditions or len(result) > 0)
@icontract.post(lambda result: all(not '\n' in line for line in result))
def _format_preconditions(preconditions: List[List[icontract._Contract]], prefix: Optional[str] = None) -> List[str]:
    """
    Format preconditions as reST.

    :param preconditions: preconditions of a function
    :param prefix: prefix of the ``:requires:`` and ``:requires else:`` directive
    :return: list of lines
    """
    if not preconditions:
        return []

    result = []  # type: List[str]
    for i, group in enumerate(preconditions):
        if i == 0:
            if prefix is not None:
                result.append(":{} requires:".format(prefix))
            else:
                result.append(":requires:")
        else:
            if prefix is not None:
                result.append(":{} requires else:".format(prefix))
            else:
                result.append(":requires else:")

        for precondition in group:
            condition = precondition.condition
            if precondition.description:
                text = "{} ({})".format(_format_condition(condition=condition), precondition.description)
            else:
                text = _format_condition(condition=condition)

            result.append("    * {}".format(text))

    return result


def _capture_as_text(capture: Callable[..., Any]) -> str:
    """Convert the capture function into its text representation by parsing the source code of the decorator."""
    if not icontract._represent._is_lambda(a_function=capture):
        signature = inspect.signature(capture)
        param_names = list(signature.parameters.keys())

        return "{}({})".format(capture.__qualname__, ", ".join(param_names))

    lines, lineno = inspect.findsource(capture)
    filename = inspect.getsourcefile(capture)
    decorator_inspection = icontract._represent.inspect_decorator(lines=lines, lineno=lineno, filename=filename)

    call_node = decorator_inspection.node

    capture_node = None  # type: Optional[ast.Lambda]

    if len(call_node.args) > 0:
        assert isinstance(call_node.args[0], ast.Lambda), \
            ("Expected the first argument to the snapshot decorator to be a condition as lambda AST node, "
             "but got: {}").format(type(call_node.args[0]))

        capture_node = call_node.args[0]

    elif len(call_node.keywords) > 0:
        for keyword in call_node.keywords:
            if keyword.arg == "capture":
                assert isinstance(keyword.value, ast.Lambda), \
                    "Expected lambda node as value of the 'capture' argument to the decorator."

                capture_node = keyword.value
                break

        assert capture_node is not None, "Expected to find a keyword AST node with 'capture' arg, but found none"
    else:
        raise AssertionError(
            "Expected a call AST node of a snapshot decorator to have either args or keywords, but got: {}".format(
                ast.dump(call_node)))

    capture_text = decorator_inspection.atok.get_text(capture_node.body)

    return capture_text


@icontract.pre(lambda prefix: prefix is None or prefix == prefix.strip())
@icontract.post(lambda snapshots, result: not snapshots or len(result) > 0)
@icontract.post(lambda result: all(not '\n' in line for line in result))
def _format_snapshots(snapshots: List[icontract._Snapshot], prefix: Optional[str] = None) -> List[str]:
    """
    Format snapshots as reST.

    :param snapshots: snapshots defined to capture the argument values of a function before the invocation
    :param prefix: prefix to be prepended to ``:OLD:`` directive
    :return: list of lines describing the snapshots
    """
    if not snapshots:
        return []

    result = []  # type: List[str]

    if prefix is not None:
        result.append(":{} OLD:".format(prefix))
    else:
        result.append(":OLD:")

    for snapshot in snapshots:
        text = _capture_as_text(capture=snapshot.capture)
        result.append("    * :code:`.{}` = :code:`{}`".format(snapshot.name, text))

    return result


@icontract.pre(lambda prefix: prefix is None or prefix == prefix.strip())
@icontract.post(lambda postconditions, result: not postconditions or len(result) > 0)
@icontract.post(lambda result: all(not '\n' in line for line in result))
def _format_postconditions(postconditions: List[icontract._Contract], prefix: Optional[str] = None) -> List[str]:
    """
    Format postconditions as reST.

    :param postconditions: postconditions of a function
    :param prefix: prefix to be prepended to ``:ensures:`` directive
    :return: list of lines describing the postconditions
    """
    if not postconditions:
        return []

    result = []  # type: List[str]

    if prefix is not None:
        result.append(":{} ensures:".format(prefix))
    else:
        result.append(":ensures:")

    for postcondition in postconditions:
        condition = postcondition.condition

        if postcondition.description:
            text = "{} ({})".format(_format_condition(condition=condition), postcondition.description)
        else:
            text = _format_condition(condition=condition)

        result.append("    * {}".format(text))

    return result


@icontract.post(lambda invariants, result: not invariants or len(result) > 0)
@icontract.post(lambda result: all(not '\n' in line for line in result))
def _format_invariants(invariants: List[icontract._Contract]) -> List[str]:
    """Format invariants as reST."""
    if not invariants:
        return []

    result = [":establishes:"]  # type: List[str]
    for invariant in invariants:
        condition = invariant.condition

        if invariant.description:
            text = "{} ({})".format(_format_condition(condition=condition), invariant.description)
        else:
            text = _format_condition(condition=condition)

        result.append("    * {}".format(text))

    return result


class _PrePostSnaps:
    """Represent preconditions, snapshots and postconditions associated with a contract checker."""

    def __init__(self, preconditions: List[List[icontract._Contract]], snapshots: List[icontract._Snapshot],
                 postconditions: List[icontract._Contract]) -> None:
        """Initialize with the given values."""
        self.preconditions = preconditions
        self.snapshots = snapshots
        self.postconditions = postconditions


def _preconditions_snapshots_postconditions(checker: Callable) -> _PrePostSnaps:
    """Collect the preconditions, snapshots and postconditions from a contract checker of a function."""
    preconditions = getattr(checker, "__preconditions__", [])  # type: List[List[icontract._Contract]]

    assert all(isinstance(precondition_group, list) for precondition_group in preconditions)
    assert (all(
        isinstance(precondition, icontract._Contract) for precondition_group in preconditions
        for precondition in precondition_group))

    # Filter empty precondition groups ("require else" blocks)
    preconditions = [group for group in preconditions if len(group) > 0]

    snapshots = getattr(checker, "__postcondition_snapshots__", [])  # type: List[icontract._Snapshot]
    assert all(isinstance(snap, icontract._Snapshot) for snap in snapshots)

    postconditions = getattr(checker, "__postconditions__", [])  # type: List[icontract._Contract]

    assert all(isinstance(postcondition, icontract._Contract) for postcondition in postconditions)

    return _PrePostSnaps(preconditions=preconditions, snapshots=snapshots, postconditions=postconditions)


@icontract.post(lambda result: all(not '\n' in line for line in result))
def _format_function_contracts(func: Callable, prefix: Optional[str] = None) -> List[str]:
    """
    Format the preconditions and postconditions of a function given its checker decorator.

    :param func: function whose contracts we are describing
    :param prefix: prefix to be prepended to the contract directives such as ``get`` or ``set``
    :return: list of lines
    """
    checker = icontract._find_checker(func=func)
    if checker is None:
        return []

    pps = _preconditions_snapshots_postconditions(checker=checker)

    pre_block = _format_preconditions(preconditions=pps.preconditions, prefix=prefix)
    old_block = _format_snapshots(snapshots=pps.snapshots, prefix=prefix)
    post_block = _format_postconditions(postconditions=pps.postconditions, prefix=prefix)

    return pre_block + old_block + post_block


@icontract.post(lambda result: all(not '\n' in line for line in result))
def _format_property_contracts(prop: property) -> List[str]:
    result = []  # type: List[str]
    for func, prefix in zip([prop.fget, prop.fset, prop.fdel], ['get', 'set', 'del']):
        result.extend(_format_function_contracts(func=func, prefix=prefix))

    return result


def _format_contracts(what: str, obj: Any) -> List[str]:
    """Format the contracts as reST."""
    if what in ['function', 'method', 'attribute']:
        if what == 'attribute':
            if not isinstance(obj, property):
                return []

            return _format_property_contracts(prop=obj)

        if what in ['function', 'method']:
            return _format_function_contracts(func=obj)

        raise NotImplementedError("Unhandled what: {}".format(what))

    elif what == 'class':
        invariants = getattr(obj, "__invariants__", [])  # type: List[icontract._Contract]
        assert isinstance(invariants, list)
        assert all(isinstance(inv, icontract._Contract) for inv in invariants)

        return _format_invariants(invariants=invariants)

    # Only properties, functions and classes have contracts.
    return []


def process_docstring(app, what, name, obj, options, lines):
    """React to a docstring event and append contracts to it."""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    lines.extend(_format_contracts(what=what, obj=obj))


def setup(app):
    """Set up the extension in Sphinx."""
    app.connect('autodoc-process-docstring', process_docstring)
    return dict(parallel_read_safe=True)
