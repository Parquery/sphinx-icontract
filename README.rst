sphinx-icontract
================

.. image:: https://github.com/Parquery/sphinx-icontract/workflows/CI/badge.svg
    :target: https://github.com/Parquery/sphinx-icontract/actions?query=workflow%3ACI
    :alt: Continuous integration

.. image:: https://coveralls.io/repos/github/Parquery/sphinx-icontract/badge.svg?branch=master
    :target: https://coveralls.io/github/Parquery/sphinx-icontract?branch=master
    :alt: Coverage

.. image:: https://badge.fury.io/py/sphinx-icontract.svg
    :target: https://pypi.org/project/sphinx-icontract/
    :alt: PyPi

.. image:: https://img.shields.io/pypi/pyversions/sphinx-icontract.svg
    :alt: PyPI - Python Version

Sphinx-icontract extends Sphinx to include icontracts of classes and functions in the documentation.

Usage
=====
Sphinx-icontract is based on the `sphinx.ext.autodoc` module. You need to specify both modules in
``extensions`` of your Sphinx configuration file (``conf.py``).

Here is an example excerpt:

.. code-block:: python

    # Add any Sphinx extension module names here, as strings. They can be
    # extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
    # ones.
    extensions = [
        'sphinx.ext.autodoc',
        'sphinx_icontract'
    ]

Implications
------------
Sphinx-icontract tries to infer the implications from the conditions and render them as implication (``... ⇒ ...``).
We implemented a rule-based matching that covers most of the practical use cases:

* ``not A or B`` is translated to ``A ⇒ B``.
* Expressions are negated, so ``x < y or B`` is translated to ``x >= y ⇒ B``. More general expressions are negated with
  ``not``: from ``x.y() or B`` to ``not x.y() ⇒ B``.
* If-Expressions are translated from ``B if A else True`` to ``A ⇒ B``.

We found implications in form of if-expressions to be confusing when read in source code and encourage programmers
to use disjunction form instead.

Custom Errors
-------------
If you specify custom errors in the contract, sphinx-icontract will try to include the error in the documentation.

The error type will be inferred from the contract's ``error`` argument. If the error message is given
as a string literal and there is no contract description, the error message will be used to describe the contract
so that you do not have to specify the description twice (once in the description of the contract and once
in the error message).

For example:

.. code-block:: python

        @icontract.require(
            lambda x: x > 0, 
            error=lambda: ValueError("x positive"))
        def some_func(x: int) -> None:
            pass

will be documented as:

.. code-block:: reStructuredText

    :requires:
                            * :code:`x > 0` (x positive; raise :py:class:`ValueError`)

If both the description and the error message are given, only the description will be included:

.. code-block:: python

        @icontract.require(
            lambda x: x > 0, 
            description="x must be positive", 
            error=lambda: ValueError("x positive"))
        def some_func(x: int) -> None:
            pass

will be rendered as:

.. code-block:: reStructuredText

    :requires:
        * :code:`x > 0` (x must be positive; raise :py:class:`ValueError`)

.. danger::
    Be careful when you write contracts with custom errors which are included in the documentation. This might
    lead the caller to (ab)use the contracts as a control flow mechanism.

    In that case, the user will expect that the contract is *always* enabled and not only during debug or test.
    (For example, whenever you run `python` interpreter with ``-O`` or ``-OO``, ``__debug__`` will be `False`.
    If you passed ``__debug__`` to your contract's ``enabled`` argument, the contract will *not* be verified in
    ``-O`` mode.)

Installation
============

* Install sphinx-icontract with pip:

.. code-block:: bash

    pip3 install sphinx-icontract

Development
===========

* Check out the repository.

* In the repository root, create the virtual environment:

.. code-block:: bash

    python3 -m venv venv3

* Activate the virtual environment:

.. code-block:: bash

    source venv3/bin/activate

* Install the development dependencies:

.. code-block:: bash

    pip3 install -e .[dev]

We use tox for testing and packaging the distribution:

.. code-block:: bash

    tox

Pre-commit Checks
-----------------
We provide a set of pre-commit checks that lint and check code for formatting.

Namely, we use:

* `yapf <https://github.com/google/yapf>`_ to check the formatting.
* The style of the docstrings is checked with `pydocstyle <https://github.com/PyCQA/pydocstyle>`_.
* Static type analysis is performed with `mypy <http://mypy-lang.org/>`_.
* Various linter checks are done with `pylint <https://www.pylint.org/>`_.
* Contracts are linted with `pyicontract-lint <https://github.com/Parquery/pyicontract-lint>`_.
* Doctests are executed using the Python `doctest module <https://docs.python.org/3.8/library/doctest.html>`_.

Run the pre-commit checks locally from an activated virtual environment with development dependencies:

.. code-block:: bash

    ./precommit.py

* The pre-commit script can also automatically format the code:

.. code-block:: bash

    ./precommit.py  --overwrite


Versioning
==========
We follow `Semantic Versioning <http://semver.org/spec/v1.0.0.html>`_. The version X.Y.Z indicates:

* X is the major version (backward-incompatible),
* Y is the minor version (backward-compatible), and
* Z is the patch version (backward-compatible bug fix).
