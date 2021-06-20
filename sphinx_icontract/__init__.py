"""Add contracts to the documentation."""
import ast
import inspect
import re
import textwrap
from typing import List, Callable, Any, Optional, Tuple, Sequence, cast, overload, Union, Iterator

import asttokens
import icontract
import icontract._checkers
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


class Lines(icontract.DBC):
    """Represent a sequence of text lines."""

    # yapf: disable
    @icontract.require(
        lambda lines:
        all(
            '\n' not in line and '\r' not in line
            for line in lines
        )
    )
    # yapf: enable
    def __new__(cls, lines: Sequence[str]) -> "Lines":
        r"""
        Ensure the properties on the ``lines``.

        Please make sure that you transfer the "ownership" immediately to Lines
        and don't modify the original list of strings any more:

        .. code-block: python

            ##
            # OK
            ##

            lines = Lines(some_text.splitlines())

            ##
            # Not OK
            ##

            some_lines = some_text.splitlines()
            lines = Lines(some_lines)
            # ... do something assuming ``lines`` is immutable ...

            some_lines[0] = "This will break \n your logic"
            # ERROR! lines[0] now contains a new-line which is unexpected!

        """
        return cast(Lines, lines)

    def __add__(self, other: "Lines") -> "Lines":
        """Concatenate two list of lines."""
        raise NotImplementedError("Only for type annotations")

    # pylint: disable=function-redefined

    @overload
    def __getitem__(self, index: int) -> str:
        """Get the item at the given integer index."""
        pass

    @overload
    def __getitem__(self, index: slice) -> "Lines":
        """Get the slice of the lines."""
        pass

    def __getitem__(self, index: Union[int, slice]) -> Union[str, "Lines"]:
        """Get the line(s) at the given index."""
        raise NotImplementedError("Only for type annotations")

    def __len__(self) -> int:
        """Return the number of the lines."""
        raise NotImplementedError("Only for type annotations")

    def __iter__(self) -> Iterator[str]:
        """Iterate over the lines."""
        raise NotImplementedError("Only for type annotations")


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


def _condition_as_text(lambda_inspection: icontract._represent.ConditionLambdaInspection) -> Lines:
    """Format condition lambda function as reST lines."""
    lambda_ast_node = lambda_inspection.node
    assert isinstance(lambda_ast_node, ast.Lambda)

    body_node = lambda_ast_node.body

    is_multiline_condition = '\n' in lambda_inspection.text

    if not is_multiline_condition:
        # Pretty-print single-line implications
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

        elif (isinstance(body_node, ast.IfExp) and isinstance(body_node.orelse, ast.NameConstant)
              and body_node.orelse.value):
            text = ':code:`{}` ⇒ :code:`{}`'.format(
                lambda_inspection.atok.get_text(node=body_node.test),
                lambda_inspection.atok.get_text(node=body_node.body))
        else:
            # None of the patterns matched.
            assert text is None
            pass

        if text is not None:
            return Lines([text])

    # None of the previous re-formats worked, take the default approach.
    if not is_multiline_condition:
        result = [':code:`{}`'.format(lambda_inspection.atok.get_text(node=body_node))]
    else:
        result = ['.. code-block:: python', '']

        dedented_body_lines = _smart_dedent_multi_line_lambda_condition(Lines(lambda_inspection.text.splitlines()))

        for line in dedented_body_lines:
            result.append('  {}'.format(line))

        result.append('')

    return Lines(result)


def _error_type_and_message(
        decorator_inspection: icontract._represent.DecoratorInspection) -> Tuple[Optional[str], Optional[str]]:
    """
    Inspect the error argument of a contract and infer the error type and the message if the error is given as a lambda.

    If the error argument is not given or if it is not given as a lambda function, return immediately.

    The error message is inferred as the single string-literal argument to a single call in the lambda body.

    :param decorator_inspection: inspection of a contract decorator
    :return: error type (None if not inferrable), error message (None if not inferrable)
    """
    call_node = decorator_inspection.node

    error_arg_node = None  # type: Optional[ast.AST]
    for keyword in call_node.keywords:
        if keyword.arg == 'error':
            error_arg_node = keyword.value

    if error_arg_node is None and len(call_node.args) == 5:
        error_arg_node = call_node.args[4]

    if not isinstance(error_arg_node, ast.Lambda):
        return None, None

    body_node = error_arg_node.body

    # The body of the error lambda needs to be a callable, since it needs to return an instance of Exception
    if not isinstance(body_node, ast.Call):
        return None, None

    error_type = decorator_inspection.atok.get_text(node=body_node.func)

    error_message = None  # type: Optional[str]
    if len(body_node.args) == 1 and len(body_node.keywords) == 0:
        if isinstance(body_node.args[0], ast.Str):
            error_message = body_node.args[0].s

    elif len(body_node.args) == 0 and len(body_node.keywords) == 1:
        if isinstance(body_node.keywords[0].value, ast.Str):
            error_message = body_node.keywords[0].value.s

    else:
        # The error message could not be inferred.
        pass

    return error_type, error_message


def _format_contract(contract: icontract._Contract) -> Lines:
    """Format the contract as reST."""
    # pylint: disable=too-many-branches
    decorator_inspection = None  # type: Optional[icontract._represent.DecoratorInspection]

    ##
    # Parse condition
    ##

    if not icontract._represent.is_lambda(a_function=contract.condition):
        condition_lines = Lines([':py:func:`{}`'.format(contract.condition.__name__)])
    else:
        # We need to extract the source code corresponding to the decorator since inspect.getsource() is broken with
        # lambdas.

        # Find the line corresponding to the condition lambda
        lines, condition_lineno = inspect.findsource(contract.condition)
        filename = inspect.getsourcefile(contract.condition)
        if filename is None:
            filename = "<filename unavailable>"

        decorator_inspection = icontract._represent.inspect_decorator(
            lines=lines, lineno=condition_lineno, filename=filename)

        lambda_inspection = icontract._represent.find_lambda_condition(decorator_inspection=decorator_inspection)
        assert lambda_inspection is not None, \
            "Expected non-None lambda inspection with the condition: {}".format(contract.condition)

        condition_lines = _condition_as_text(lambda_inspection=lambda_inspection)

    ##
    # Parse error
    ##

    error_type = None  # type: Optional[str]

    # Error message is set only for an error of a contract given as a lambda that takes no arguments and returns
    # a result of a call on a string literal (*e.g.*, ``error=ValueError("some message")``.
    error_msg = None  # type: Optional[str]

    if contract.error is not None:
        if isinstance(contract.error, type):
            error_type = contract.error.__qualname__
        elif callable(contract.error) and icontract._represent.is_lambda(a_function=contract.error):
            if decorator_inspection is None:
                lines, condition_lineno = inspect.findsource(contract.error)
                filename = inspect.getsourcefile(contract.error)
                if filename is None:
                    filename = "<filename unavailable>"

                decorator_inspection = icontract._represent.inspect_decorator(
                    lines=lines, lineno=condition_lineno, filename=filename)

            error_type, error_msg = _error_type_and_message(decorator_inspection=decorator_inspection)
        else:
            # Error type could not be inferred
            pass

    ##
    # Format
    ##

    description = None  # type: Optional[str]
    if contract.description:
        description = contract.description
    elif error_msg is not None:
        description = error_msg
    else:
        # Description could not be inferred.
        pass

    doc = None  # type: Optional[str]
    if description and error_type:
        if description.strip()[-1] in [".", "!", "?"]:
            doc = "{} Raise :py:class:`{}`".format(description, error_type)
        elif description.strip()[-1] in [",", ";"]:
            doc = "{} raise :py:class:`{}`".format(description, error_type)
        else:
            doc = "{}; raise :py:class:`{}`".format(description, error_type)

    elif not description and error_type:
        doc = "Raise :py:class:`{}`".format(error_type)

    elif description and not error_type:
        doc = description

    else:
        # No extra documentation can be generated since the error type could not be inferred and
        # no contract description was given.
        doc = None

    if doc is not None:
        result = condition_lines + Lines(["", "({})".format(doc)])
    else:
        result = condition_lines

    return result


def _make_bullet(lines: Lines) -> Lines:
    """
    Indent the lines and put the bullet point in front.

    >>> _make_bullet(Lines(['x', '', '  y']))
    ['    * x', '', '        y']
    """
    result = []  # type: List[str]
    for i, line in enumerate(lines):
        if i == 0:
            result.append('    * {}'.format(line))
        else:
            if len(line.strip()) > 0:
                result.append('      {}'.format(line))
            else:
                result.append('')

    return Lines(result)


_WHITESPACE_PREFIX_RE = re.compile(r'^\s+')


def _smart_dedent_multi_line_lambda_condition(lines: Lines) -> Lines:
    """
    Try to dedent multi-line lambda condition for better aesthetics.

    The first line is usually not indented, while the following lines are
    (since we inspect the source code).
    """
    if len(lines) == 0:
        return lines

    # If the first line is already indented, try to dedent it as a block
    if _WHITESPACE_PREFIX_RE.match(lines[0]):
        return Lines(textwrap.dedent('\n'.join(lines)).splitlines())

    dedented = textwrap.dedent('\n'.join(lines[1:]))
    dedented_lines = dedented.splitlines()

    return Lines([lines[0]] + dedented_lines)


@icontract.require(lambda prefix: prefix is None or prefix == prefix.strip())
@icontract.ensure(lambda preconditions, result: not preconditions or len(result) > 0)
def _format_preconditions(preconditions: List[List[icontract._Contract]], prefix: Optional[str] = None) -> Lines:
    """
    Format preconditions as reST.

    :param preconditions: preconditions of a function
    :param prefix: prefix of the ``:requires:`` and ``:requires else:`` directive
    :return: list of lines
    """
    if not preconditions:
        return Lines([])

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
            contract_bullet_point = _make_bullet(_format_contract(contract=precondition))
            result.extend(contract_bullet_point)

    return Lines(result)


def _capture_as_text(capture: Callable[..., Any]) -> Lines:
    """Convert the capture function into its text representation by parsing the source code of the decorator."""
    if not icontract._represent.is_lambda(a_function=capture):
        signature = inspect.signature(capture)
        param_names = list(signature.parameters.keys())

        return Lines(["{}({})".format(capture.__qualname__, ", ".join(param_names))])

    lines, lineno = inspect.findsource(capture)
    filename = inspect.getsourcefile(capture)
    if filename is None:
        filename = "<filename unavailable>"

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

    dedented_capture = _smart_dedent_multi_line_lambda_condition(capture_text.splitlines())

    return dedented_capture


@icontract.require(lambda prefix: prefix is None or prefix == prefix.strip())
@icontract.ensure(lambda snapshots, result: not snapshots or len(result) > 0)
def _format_snapshots(snapshots: List[icontract._Snapshot], prefix: Optional[str] = None) -> Lines:
    """
    Format snapshots as reST.

    :param snapshots: snapshots defined to capture the argument values of a function before the invocation
    :param prefix: prefix to be prepended to ``:OLD:`` directive
    :return: list of lines describing the snapshots
    """
    if not snapshots:
        return Lines([])

    result = []  # type: List[str]

    if prefix is not None:
        result.append(":{} OLD:".format(prefix))
    else:
        result.append(":OLD:")

    for snapshot in snapshots:
        capture_lines = _capture_as_text(capture=snapshot.capture)

        if len(capture_lines) == 1:
            result.append("    * :code:`.{}` = :code:`{}`".format(snapshot.name, capture_lines[0]))
        else:
            capture_point = [':code:`.{}` ='.format(snapshot.name), '', '.. code-block: python', '']  # type: List[str]
            capture_point.extend(capture_lines)
            capture_point.append('')

            result.extend(_make_bullet(Lines(capture_point)))

    return Lines(result)


@icontract.require(lambda prefix: prefix is None or prefix == prefix.strip())
@icontract.ensure(lambda postconditions, result: not postconditions or len(result) > 0)
def _format_postconditions(postconditions: List[icontract._Contract], prefix: Optional[str] = None) -> Lines:
    """
    Format postconditions as reST.

    :param postconditions: postconditions of a function
    :param prefix: prefix to be prepended to ``:ensures:`` directive
    :return: list of lines describing the postconditions
    """
    if not postconditions:
        return Lines([])

    result = []  # type: List[str]

    if prefix is not None:
        result.append(":{} ensures:".format(prefix))
    else:
        result.append(":ensures:")

    for postcondition in postconditions:
        contract_bullet_point = _make_bullet(_format_contract(contract=postcondition))
        result.extend(contract_bullet_point)

    return Lines(result)


@icontract.ensure(lambda invariants, result: not invariants or len(result) > 0)
def _format_invariants(invariants: List[icontract._Contract]) -> Lines:
    """Format invariants as reST."""
    if not invariants:
        return Lines([])

    result = [":establishes:"]  # type: List[str]
    for invariant in invariants:
        contract_bullet_point = _make_bullet(_format_contract(contract=invariant))
        result.extend(contract_bullet_point)

    return Lines(result)


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


def _format_function_contracts(func: Callable, prefix: Optional[str] = None) -> Lines:
    """
    Format the preconditions and postconditions of a function given its checker decorator.

    :param func: function whose contracts we are describing
    :param prefix: prefix to be prepended to the contract directives such as ``get`` or ``set``
    :return: list of lines
    """
    checker = icontract._checkers.find_checker(func=func)
    if checker is None:
        return Lines([])

    pps = _preconditions_snapshots_postconditions(checker=checker)

    pre_block = _format_preconditions(preconditions=pps.preconditions, prefix=prefix)
    old_block = _format_snapshots(snapshots=pps.snapshots, prefix=prefix)
    post_block = _format_postconditions(postconditions=pps.postconditions, prefix=prefix)

    return pre_block + old_block + post_block


def _format_property_contracts(prop: property) -> Lines:
    result = []  # type: List[str]
    for func, prefix in zip([prop.fget, prop.fset, prop.fdel], ['get', 'set', 'del']):
        result.extend(_format_function_contracts(func=func, prefix=prefix))  # type: ignore

    return Lines(result)


def _format_contracts(what: str, obj: Any) -> Lines:
    """Format the contracts as reST."""
    if what in ['function', 'method', 'attribute']:
        if what == 'attribute':
            if not isinstance(obj, property):
                return Lines([])

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
    return Lines([])


def process_docstring(app, what, name, obj, options, lines):
    """React to a docstring event and append contracts to it."""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments
    lines.extend(_format_contracts(what=what, obj=obj))


def setup(app):
    """Set up the extension in Sphinx."""
    app.connect('autodoc-process-docstring', process_docstring)
    return dict(parallel_read_safe=True)
