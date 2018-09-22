#!/usr/bin/env python3
"""Test sphinx_icontract."""

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=no-member
# pylint: disable=no-self-use
# pylint: disable=unused-argument

import unittest

import icontract

import sphinx_icontract


class TestFormatCondition(unittest.TestCase):
    def test_function(self):
        def some_func() -> bool:
            return True

        text = sphinx_icontract.format_condition(condition=some_func)

        self.assertEqual(':py:func:`some_func`', text)

    def test_lambda(self):
        text = sphinx_icontract.format_condition(condition=lambda x: x > 0)

        self.assertEqual(':code:`x > 0`', text)


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

    def test_class_hierarchy(self):
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


if __name__ == '__main__':
    unittest.main()
