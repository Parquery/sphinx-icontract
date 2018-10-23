#!/usr/bin/env python3
"""Test sphinx_icontract."""

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=no-member
# pylint: disable=no-self-use
# pylint: disable=unused-argument
import pathlib
import unittest
from typing import List, Any

import icontract

import sphinx_icontract


class TestFormatCondition(unittest.TestCase):
    def test_lambda(self):
        @icontract.pre(lambda x: x > 0)
        def some_func(x: int) -> bool:
            return True

        lines = sphinx_icontract._format_function_contracts(func=some_func)
        self.assertListEqual([':requires:', '    * :code:`x > 0`'], lines)

    def test_implies_with_not_or(self):
        @icontract.pre(lambda x: not (x > 0) or x < 100)
        def some_func(x: int) -> bool:
            return True

        lines = sphinx_icontract._format_function_contracts(func=some_func)
        self.assertListEqual([':requires:', '    * :code:`x > 0` ⇒ :code:`x < 100`'], lines)

    def test_implies_with_comparison_or(self):
        @icontract.pre(lambda x: x == 0 or x % 2 == 0)
        @icontract.pre(lambda x: x != 0 or x % 3 == 0)
        @icontract.pre(lambda x: x < 0 or x % 4 == 0)
        @icontract.pre(lambda x: x <= 0 or x % 5 == 0)
        @icontract.pre(lambda x: x > 0 or x % 6 == 0)
        @icontract.pre(lambda x: x >= 0 or x % 7 == 0)
        @icontract.pre(lambda x: x in [1, 2] or x % 8 == 0)
        @icontract.pre(lambda x: x not in [1, 2] or x % 9 == 0)
        @icontract.pre(lambda x: (x + 100 < 0) or x % 10 == 0)
        def some_func(x: int) -> bool:
            return True

        lines = sphinx_icontract._format_function_contracts(func=some_func)

        # yapf: disable
        self.assertListEqual(
            [
                ':requires:',
                '    * :code:`x + 100 >= 0` ⇒ :code:`x % 10 == 0`',
                '    * :code:`x in [1, 2]` ⇒ :code:`x % 9 == 0`',
                '    * :code:`x not in [1, 2]` ⇒ :code:`x % 8 == 0`',
                '    * :code:`x < 0` ⇒ :code:`x % 7 == 0`',
                '    * :code:`x <= 0` ⇒ :code:`x % 6 == 0`',
                '    * :code:`x > 0` ⇒ :code:`x % 5 == 0`',
                '    * :code:`x >= 0` ⇒ :code:`x % 4 == 0`',
                '    * :code:`x == 0` ⇒ :code:`x % 3 == 0`',
                '    * :code:`x != 0` ⇒ :code:`x % 2 == 0`'
            ], lines)

        # yapf: enable

        # Test is/is not
        @icontract.pre(lambda x, y: x is None or y == 1)
        @icontract.pre(lambda x, y: x is not None or y == 2)
        def another_func(x: int, y: int) -> None:
            return

        lines = sphinx_icontract._format_function_contracts(func=another_func)

        # yapf: disable
        self.assertListEqual(
            [
                ':requires:',
                '    * :code:`x is None` ⇒ :code:`y == 2`',
                '    * :code:`x is not None` ⇒ :code:`y == 1`'
            ], lines)
        # yapf: enable

    def test_implies_with_value_or(self):
        @icontract.pre(lambda x, y: x or y == 1)
        @icontract.pre(lambda x, y: x.some_attr or y == 2)
        @icontract.pre(lambda x, y: x.some_call() or y == 3)
        @icontract.pre(lambda x, y: x.some_call().another_attr or y == 4)
        @icontract.pre(lambda x, y: x.some_attr.another_call() or y == 5)
        @icontract.pre(lambda x, y: -x or y == 6)
        @icontract.pre(lambda x, y: x + 100 or y == 7)
        @icontract.pre(lambda x, y: (x if x > 0 else False) or y == 8)
        def some_func(x: Any, y: int) -> None:
            return

        lines = sphinx_icontract._format_function_contracts(func=some_func)

        # yapf: disable
        self.assertListEqual(
            [
                ':requires:',
                '    * :code:`not (x if x > 0 else False)` ⇒ :code:`y == 8`',
                '    * :code:`not (x + 100)` ⇒ :code:`y == 7`',
                '    * :code:`not (-x)` ⇒ :code:`y == 6`',
                '    * :code:`not x.some_attr.another_call()` ⇒ :code:`y == 5`',
                '    * :code:`not x.some_call().another_attr` ⇒ :code:`y == 4`',
                '    * :code:`not x.some_call()` ⇒ :code:`y == 3`',
                '    * :code:`not x.some_attr` ⇒ :code:`y == 2`',
                '    * :code:`not x` ⇒ :code:`y == 1`'
            ], lines)
        # yapf: enable

    def test_implies_not_or_and(self):
        @icontract.pre(lambda x: not (x > 0) or (x < 100 and x % 3 == 0))
        def some_func(x: int) -> bool:
            return True

        lines = sphinx_icontract._format_function_contracts(func=some_func)
        self.assertListEqual([':requires:', '    * :code:`x > 0` ⇒ :code:`x < 100 and x % 3 == 0`'], lines)

    def test_implies_with_if_else_true(self):
        @icontract.pre(lambda x, y: y == 1 if x in [1, 2] else True)
        def some_func(x: Any, y: int) -> None:
            return

        lines = sphinx_icontract._format_function_contracts(func=some_func)

        # yapf: disable
        self.assertListEqual(
            [
                ':requires:',
                '    * :code:`x in [1, 2]` ⇒ :code:`y == 1`'
            ], lines)
        # yapf: enable


class TestFormatContracts(unittest.TestCase):
    def test_function_wo_contracts(self):
        def some_func(x: int) -> int:
            return x

        lines = sphinx_icontract._format_contracts(what='function', obj=some_func)
        self.assertListEqual([], lines)

    def test_class_wo_contracts(self):
        class SomeClass:
            pass

        lines = sphinx_icontract._format_contracts(what='class', obj=SomeClass)
        self.assertListEqual([], lines)

    def test_pre(self):
        @icontract.pre(lambda x: x > 0)
        def some_func(x: int) -> int:
            return x

        lines = sphinx_icontract._format_contracts(what='function', obj=some_func)
        self.assertListEqual(
            [
                # yapf: disable
                ':requires:',
                '    * :code:`x > 0`',
                # yapf: enable
            ],
            lines)

    def test_post(self):
        @icontract.post(lambda x, result: result >= x)
        def some_func(x: int) -> int:
            return x

        lines = sphinx_icontract._format_contracts(what='function', obj=some_func)
        self.assertListEqual(
            [
                # yapf: disable
                ':ensures:',
                '    * :code:`result >= x`'
                # yapf: enable
            ],
            lines)

    def test_slow(self):
        # Test that the contract is retrieved based on enabled.
        # An example taken from https://github.com/Parquery/pypackagery

        assert icontract.SLOW, \
            "Slow contracts need to be enabled by setting the environment variable ICONTRACT_SLOW."

        @icontract.post(
            lambda initial_paths, result: all(pth in result for pth in initial_paths if pth.is_file()),
            "Initial files also in result",
            enabled=icontract.SLOW)
        def resolve_initial_paths(initial_paths: List[pathlib.Path]) -> List[pathlib.Path]:
            pass

        lines = sphinx_icontract._format_contracts(what='function', obj=resolve_initial_paths)

        self.assertListEqual(
            [
                # yapf: disable
                ':ensures:',
                '    * :code:`all(pth in result for pth in initial_paths if pth.is_file())` '
                '(Initial files also in result)'
                # yapf: enable
            ],
            lines)

    def test_pre_post(self):
        @icontract.pre(lambda x: x > 0)
        @icontract.post(lambda x, result: result >= x)
        def some_func(x: int) -> int:
            return x

        lines = sphinx_icontract._format_contracts(what='function', obj=some_func)
        self.assertListEqual(
            [
                # yapf: disable
                ':requires:',
                '    * :code:`x > 0`',
                ':ensures:',
                '    * :code:`result >= x`'
                # yapf: enable
            ],
            lines)

    def test_snapshot(self):
        # pylint: disable=unnecessary-lambda
        @icontract.snapshot(lambda lst: lst[:])
        @icontract.snapshot(capture=lambda lst: len(lst), name="len_lst")
        @icontract.post(lambda OLD, lst, value: OLD.len_lst + 1 == len(lst))
        @icontract.post(lambda OLD, lst, value: OLD.lst + [value] == lst)
        def some_func(lst: List[int], value: int) -> None:
            lst.append(value)

        lines = sphinx_icontract._format_contracts(what='function', obj=some_func)
        # yapf: disable
        self.assertListEqual(
            [
                ':OLD:',
                '    * :code:`.len_lst` = :code:`len(lst)`',
                '    * :code:`.lst` = :code:`lst[:]`'
                , ':ensures:',
                '    * :code:`OLD.lst + [value] == lst`',
                '    * :code:`OLD.len_lst + 1 == len(lst)`'
            ],
            lines)
        # yapf: enable

    def test_snapshot_with_function(self):
        def some_capture(lst: List[int]) -> List[int]:
            return lst[:]

        @icontract.snapshot(some_capture)
        @icontract.post(lambda OLD, lst, value: OLD.lst + [value] == lst)
        def some_func(lst: List[int], value: int) -> None:
            lst.append(value)

        lines = sphinx_icontract._format_contracts(what='function', obj=some_func)
        # yapf: disable
        self.assertListEqual(
            [
                ':OLD:',
                '    * :code:`.lst` = '
                ':code:`TestFormatContracts.test_snapshot_with_function.<locals>.some_capture(lst)`',
                ':ensures:',
                '    * :code:`OLD.lst + [value] == lst`'
            ],
            lines)
        # yapf: enable

    def test_pre_post_with_description(self):
        @icontract.pre(lambda x: x > 0, 'some precondition')
        @icontract.post(lambda x, result: result >= x, 'some postcondition')
        def some_func(x: int) -> int:
            return x

        lines = sphinx_icontract._format_contracts(what='function', obj=some_func)
        self.assertListEqual(
            [
                # yapf: disable
                ':requires:',
                '    * :code:`x > 0` (some precondition)',
                ':ensures:',
                '    * :code:`result >= x` (some postcondition)'
                # yapf: enable
            ],
            lines)

    def test_invariant_with_description(self):
        @icontract.inv(lambda self: self.some_getter() > 0, "some invariant")
        class SomeClass(icontract.DBC):
            """Represent some abstract class."""

            def some_getter(self) -> int:
                return 1

        lines = sphinx_icontract._format_contracts(what='class', obj=SomeClass)
        self.assertListEqual(
            [
                # yapf: disable
                ':establishes:',
                '    * :code:`self.some_getter() > 0` (some invariant)'
                # yapf: enable
            ],
            lines)

    def test_property(self):
        class SomeClass:
            def __init__(self) -> None:
                self.gets = 0
                self.sets = 0
                self.dels = 0

            @property
            @icontract.post(lambda result: result > 0)
            @icontract.snapshot(lambda self: self.gets, name="gets")
            @icontract.post(lambda OLD, self: OLD.gets == self.gets + 1)
            def some_property(self) -> int:
                """Describe some property."""
                self.gets += 1
                return 1

            @some_property.setter
            @icontract.pre(lambda some_value: some_value > 0)
            @icontract.snapshot(lambda self: self.sets, name="sets")
            @icontract.post(lambda OLD, self: OLD.sets == self.sets + 1)
            def some_property(self, some_value: int) -> None:
                """Set some property."""
                self.sets += 1

            @some_property.deleter
            @icontract.pre(lambda self: self.name != "")
            @icontract.snapshot(lambda self: self.dels, name="dels")
            @icontract.post(lambda OLD, self: OLD.dels == self.dels + 1)
            def some_property(self) -> None:
                """Delete some property."""
                self.dels += 1

        lines = sphinx_icontract._format_contracts(what='attribute', obj=SomeClass.some_property)
        # yapf: disable
        self.assertListEqual(
            [':get OLD:',
             '    * :code:`.gets` = :code:`self.gets`',
             ':get ensures:',
             '    * :code:`OLD.gets == self.gets + 1`',
             '    * :code:`result > 0`',
             ':set requires:',
             '    * :code:`some_value > 0`',
             ':set OLD:',
             '    * :code:`.sets` = :code:`self.sets`',
             ':set ensures:',
             '    * :code:`OLD.sets == self.sets + 1`',
             ':del requires:',
             '    * :code:`self.name != ""`',
             ':del OLD:',
             '    * :code:`.dels` = :code:`self.dels`',
             ':del ensures:',
             '    * :code:`OLD.dels == self.dels + 1`'],
            lines)
        # yapf: enable

    def test_inv_pre_post_with_class_hierarchy(self):
        @icontract.inv(lambda self: self.some_getter() > 0)
        class SomeAbstract(icontract.DBC):
            """Represent some abstract class."""

            def some_getter(self) -> int:
                return 1

            @icontract.pre(lambda x: x > 0)
            @icontract.pre(lambda x: x % 2 == 0)
            @icontract.post(lambda result: result > 0)
            def some_func(self, x: int) -> int:
                """
                Compute something.

                :param x: some input parameter
                :return: some result
                """
                return x

        @icontract.inv(lambda self: self.some_getter() < 100)
        class SomeClass(SomeAbstract):
            @icontract.pre(lambda x: x > -20)
            @icontract.pre(lambda x: x % 3 == 0)
            @icontract.post(lambda result: result > 10)
            def some_func(self, x: int) -> int:
                return x

        lines = sphinx_icontract._format_contracts(what='class', obj=SomeAbstract)
        self.assertListEqual([':establishes:', '    * :code:`self.some_getter() > 0`'], lines)

        lines = sphinx_icontract._format_contracts(what='class', obj=SomeClass)
        self.assertListEqual(
            [
                # yapf: disable
                ':establishes:',
                '    * :code:`self.some_getter() > 0`',
                '    * :code:`self.some_getter() < 100`'
                # yapf: enable
            ],
            lines)

        lines = sphinx_icontract._format_contracts(what='method', obj=SomeClass.some_func)

        self.assertListEqual(
            [
                # yapf: disable
                ':requires:',
                '    * :code:`x % 2 == 0`',
                '    * :code:`x > 0`',
                ':requires else:',
                '    * :code:`x % 3 == 0`',
                '    * :code:`x > -20`',
                ':ensures:',
                '    * :code:`result > 0`',
                '    * :code:`result > 10`'
                # yapf: enable
            ],
            lines)

    def test_snapshot_with_class_hierarchy(self):
        # pylint: disable=unnecessary-lambda
        class SomeBase(icontract.DBC):
            @icontract.snapshot(lambda lst: lst[:])
            @icontract.post(lambda OLD, lst, value: lst == OLD.lst + [value])
            def some_func(self, lst: List[int], value: int) -> None:
                lst.append(value)

        class SomeClass(SomeBase):
            @icontract.snapshot(lambda lst: len(lst), name="len_lst")
            @icontract.post(lambda OLD, lst: len(lst) == OLD.len_lst + 1)
            def some_func(self, lst: List[int], value: int) -> None:
                value = value * 1000  # do something to make the toy example meaningful
                super().some_func(lst, value)

        lines = sphinx_icontract._format_contracts(what='method', obj=SomeClass.some_func)

        # yapf: disable
        self.assertListEqual(
            [':OLD:',
             '    * :code:`.lst` = :code:`lst[:]`',
             '    * :code:`.len_lst` = :code:`len(lst)`',
             ':ensures:',
             '    * :code:`lst == OLD.lst + [value]`',
             '    * :code:`len(lst) == OLD.len_lst + 1`'
             ],
            lines)
        # yapf: enable


class TestError(unittest.TestCase):
    def test_condition_lambda_and_argless_error_lambda(self):
        @icontract.pre(lambda x: x > 0, error=lambda: ValueError("x positive"))
        def some_func(x: int) -> None:
            pass

        lines = sphinx_icontract._format_contracts(what='function', obj=some_func)

        # yapf: disable
        self.assertListEqual(
            [
                ':requires:',
                '    * :code:`x > 0` (x positive; raise :py:class:`ValueError`)'
            ],
            lines)
        # yapf: enable

    def test_condition_lambda_and_error_lambda_with_args(self):
        # Error message can not be inferred from the exception call since it involves more logic than a simple string
        # literal.
        @icontract.pre(lambda x: x > 0, error=lambda x: ValueError("x positive, but got: {}".format(x)))
        def some_func(x: int) -> None:
            pass

        lines = sphinx_icontract._format_contracts(what='function', obj=some_func)

        # yapf: disable
        self.assertListEqual(
            [
                ':requires:',
                '    * :code:`x > 0` (Raise :py:class:`ValueError`)'
            ],
            lines)
        # yapf: enable

    def test_condition_lambda_and_error_lambda_with_exception_keyword(self):
        @icontract.pre(lambda x: x > 0, error=lambda: ValueError(msg="x positive"))
        def some_func(x: int) -> None:
            pass

        lines = sphinx_icontract._format_contracts(what='function', obj=some_func)

        # yapf: disable
        self.assertListEqual(
            [
                ':requires:',
                '    * :code:`x > 0` (x positive; raise :py:class:`ValueError`)'
            ],
            lines)
        # yapf: enable

    def test_condition_function_and_error_lambda(self):
        def must_be_positive(x: int) -> bool:
            return x > 0

        @icontract.pre(must_be_positive, error=lambda: ValueError("x positive"))
        def some_func(x: int) -> None:
            pass

        lines = sphinx_icontract._format_contracts(what='function', obj=some_func)

        # yapf: disable
        self.assertListEqual(
            [
                ':requires:',
                '    * :py:func:`must_be_positive` (x positive; raise :py:class:`ValueError`)'
            ],
            lines)
        # yapf: enable

    def test_nested_error(self):
        class SomeClass:
            class SomeError(Exception):
                pass

        @icontract.pre(lambda x: x > 0, error=lambda: SomeClass.SomeError("x positive"))
        def some_func(x: int) -> None:
            pass

        lines = sphinx_icontract._format_contracts(what='function', obj=some_func)

        # yapf: disable
        self.assertListEqual(
            [
                ':requires:',
                '    * :code:`x > 0` (x positive; raise :py:class:`SomeClass.SomeError`)'
            ],
            lines)
        # yapf: enable

    def test_description_and_error_lambda(self):
        # The description and error differ; the descripion must be selected.
        @icontract.pre(lambda x: x > 0, description="x must be positive", error=lambda: ValueError("x positive"))
        def some_func(x: int) -> None:
            pass

        lines = sphinx_icontract._format_contracts(what='function', obj=some_func)

        # yapf: disable
        self.assertListEqual(
            [
                ':requires:',
                '    * :code:`x > 0` (x must be positive; raise :py:class:`ValueError`)'
            ],
            lines)
        # yapf: enable

    def test_error_as_class(self):
        @icontract.pre(lambda x: x > 0, error=ValueError)
        def some_func(x: int) -> None:
            pass

        lines = sphinx_icontract._format_contracts(what='function', obj=some_func)

        # yapf: disable
        self.assertListEqual(
            [
                ':requires:',
                '    * :code:`x > 0` (Raise :py:class:`ValueError`)'
            ],
            lines)
        # yapf: enable

    def test_condition_function_and_error_as_class(self):
        def must_be_positive(x: int) -> bool:
            return x > 0

        @icontract.pre(must_be_positive, error=ValueError)
        def some_func(x: int) -> None:
            pass

        lines = sphinx_icontract._format_contracts(what='function', obj=some_func)

        # yapf: disable
        self.assertListEqual(
            [
                ':requires:',
                '    * :py:func:`must_be_positive` (Raise :py:class:`ValueError`)'
            ],
            lines)
        # yapf: enable

    def test_decorator_with_no_keyword_args(self):
        @icontract.pre(lambda x: x > 0, "x must be positive", None, icontract.aRepr, True,
                       lambda: ValueError("x positive"))
        def some_func(x: int) -> None:
            pass

        lines = sphinx_icontract._format_contracts(what='function', obj=some_func)

        # yapf: disable
        self.assertListEqual(
            [
                ':requires:',
                '    * :code:`x > 0` (x must be positive; raise :py:class:`ValueError`)'
            ],
            lines)
        # yapf: enable


if __name__ == '__main__':
    unittest.main()
