"""Add contracts to the documentation."""

from typing import List, Callable, Any

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


def format_condition(condition: Callable[..., bool]) -> str:
    """Format condition as reST."""
    lambda_inspection = icontract.represent.inspect_lambda_condition(condition=condition)

    if lambda_inspection is None:
        return ':py:func:`{}`'.format(condition.__name__)

    text = icontract.represent.condition_as_text(condition=condition, lambda_inspection=lambda_inspection)
    return ':code:`{}`'.format(text)


@icontract.post(lambda preconditions, result: not preconditions or len(result) > 0)
def _format_preconditions(preconditions: List[List[icontract._Contract]]) -> List[str]:
    """Format preconditions as reST."""
    if not preconditions:
        return []

    result = []  # type: List[str]
    for i, group in enumerate(preconditions):
        if i == 0:
            result.extend([":requires:"])
        else:
            result.extend([":requires else:"])

        for precondition in group:
            condition = precondition.condition
            if precondition.description:
                text = "{} ({})".format(format_condition(condition=condition), precondition.description)
            else:
                text = format_condition(condition=condition)

            result.append("    * {}".format(text))

    return result


@icontract.post(lambda postconditions, result: not postconditions or len(result) > 0)
def _format_postconditions(postconditions: List[icontract._Contract]) -> List[str]:
    """Format postconditions as reST."""
    if not postconditions:
        return []

    result = [":ensures:"]  # type: List[str]
    for postcondition in postconditions:
        condition = postcondition.condition

        if postcondition.description:
            text = "{} ({})".format(format_condition(condition=condition), postcondition.description)
        else:
            text = format_condition(condition=condition)

        result.append("    * {}".format(text))

    return result


@icontract.post(lambda invariants, result: not invariants or len(result) > 0)
def _format_invariants(invariants: List[icontract._Contract]) -> List[str]:
    """Format invariants as reST."""
    if not invariants:
        return []

    result = [":establishes:"]  # type: List[str]
    for invariant in invariants:
        condition = invariant.condition

        if invariant.description:
            text = "{} ({})".format(format_condition(condition=condition), invariant.description)
        else:
            text = format_condition(condition=condition)

        result.append("    * {}".format(text))

    return result


def _format_contracts(what: str, obj: Any) -> List[str]:
    """Format the contracts as reST."""
    if what in ['function', 'method']:
        checker = icontract._find_checker(func=obj)
        if checker is not None:
            preconditions = getattr(checker, "__preconditions__", [])  # type: List[List[icontract._Contract]]

            assert all(isinstance(precondition_group, list) for precondition_group in preconditions)
            assert (all(
                isinstance(precondition, icontract._Contract) for precondition_group in preconditions
                for precondition in precondition_group))

            # Filter empty precondition groups ("require else" blocks)
            preconditions = [group for group in preconditions if len(group) > 0]

            postconditions = getattr(checker, "__postconditions__", [])  # type: List[icontract._Contract]

            assert all(isinstance(postcondition, icontract._Contract) for postcondition in postconditions)

            pre_block = _format_preconditions(preconditions=preconditions)
            post_block = _format_postconditions(postconditions=postconditions)

            return pre_block + post_block

    elif what == 'class':
        invariants = getattr(obj, "__invariants__", [])  # type: List[icontract._Contract]
        return _format_invariants(invariants=invariants)

    # Only functions and classes have contracts.
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
