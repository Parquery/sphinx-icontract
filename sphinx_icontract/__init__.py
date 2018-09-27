"""Add contracts to the documentation."""
import ast
from typing import List, Callable, Any, Optional, Tuple

import icontract
import icontract.represent

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


def _format_condition(condition: Callable[..., bool]) -> str:
    """Format condition as reST."""
    lambda_inspection = icontract.represent.inspect_lambda_condition(condition=condition)

    if lambda_inspection is None:
        return ':py:func:`{}`'.format(condition.__name__)

    lambda_ast_node = lambda_inspection.node
    assert isinstance(lambda_ast_node, ast.Lambda)

    body_node = lambda_ast_node.body

    if isinstance(body_node, ast.BoolOp) and isinstance(body_node.op, ast.Or) and len(body_node.values) == 2 and \
            isinstance(body_node.values[0], ast.UnaryOp) and isinstance(body_node.values[0].op, ast.Not):
        text = ':code:`{}` ⇒ :code:`{}`'.format(
            lambda_inspection.atok.get_text(node=body_node.values[0].operand),
            lambda_inspection.atok.get_text(node=body_node.values[1]))
    else:
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


def _preconditions_postconditions(
        checker: Callable) -> Tuple[List[List[icontract._Contract]], List[icontract._Contract]]:
    """Collect the preconditions and postconditions from a contract checker of a function."""
    preconditions = getattr(checker, "__preconditions__", [])  # type: List[List[icontract._Contract]]

    assert all(isinstance(precondition_group, list) for precondition_group in preconditions)
    assert (all(
        isinstance(precondition, icontract._Contract) for precondition_group in preconditions
        for precondition in precondition_group))

    # Filter empty precondition groups ("require else" blocks)
    preconditions = [group for group in preconditions if len(group) > 0]

    postconditions = getattr(checker, "__postconditions__", [])  # type: List[icontract._Contract]

    assert all(isinstance(postcondition, icontract._Contract) for postcondition in postconditions)

    return preconditions, postconditions


@icontract.post(lambda result: all(not '\n' in line for line in result))
def _format_function_contracts(func: Callable, prefix: Optional[str] = None) -> List[str]:
    """
    Format the preconditions and postconditions of a function given its checker decorator.

    :param func: function whose contracts we are describing
    :param prefix: prefix to be prepended to the directives (such as ``:requires:``)
    :return: list of lines
    """
    checker = icontract._find_checker(func=func)
    if checker is None:
        return []

    preconditions, postconditions = _preconditions_postconditions(checker=checker)

    pre_block = _format_preconditions(preconditions=preconditions, prefix=prefix)
    post_block = _format_postconditions(postconditions=postconditions, prefix=prefix)

    return pre_block + post_block


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
