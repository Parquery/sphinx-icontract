sphinx-icontract
================

.. image:: https://api.travis-ci.com/Parquery/sphinx-icontract.svg?branch=master
    :target: https://api.travis-ci.com/Parquery/sphinx-icontract.svg?branch=master
    :alt: Build Status

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
* Doctests are executed using the Python `doctest module <https://docs.python.org/3.5/library/doctest.html>`_.

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
