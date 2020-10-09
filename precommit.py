#!/usr/bin/env python3
"""Run precommit checks on the repository."""
import argparse
import os
import pathlib
import subprocess
import sys


def main() -> int:
    """"
    Main routine
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite",
        help="Overwrite the unformatted source files with the well-formatted code in place. "
        "If not set, raise an exception if any of the files do not conform to the style guide.",
        action='store_true')

    args = parser.parse_args()

    overwrite = bool(args.overwrite)

    repo_root = pathlib.Path(__file__).parent

    print("YAPF'ing...")
    if overwrite:
        subprocess.check_call(
            [
                "yapf", "--in-place", "--style=style.yapf", "--recursive", "tests", "sphinx_icontract", "setup.py",
                "precommit.py"
            ],
            cwd=str(repo_root))
    else:
        subprocess.check_call(
            [
                "yapf", "--diff", "--style=style.yapf", "--recursive", "tests", "sphinx_icontract", "setup.py",
                "precommit.py"
            ],
            cwd=str(repo_root))

    print("Mypy'ing...")
    subprocess.check_call(["mypy", "sphinx_icontract", "tests"], cwd=str(repo_root))

    print("Pyicontract-lint'ing...")
    subprocess.check_call(["pyicontract-lint", "tests", "sphinx_icontract"], cwd=str(repo_root))

    print("Pylint'ing...")
    subprocess.check_call(["pylint", "--rcfile=pylint.rc", "tests", "sphinx_icontract"], cwd=str(repo_root))

    print("Pydocstyle'ing...")
    subprocess.check_call(["pydocstyle", "sphinx_icontract"], cwd=str(repo_root))

    print("Testing...")
    env = os.environ.copy()
    env['ICONTRACT_SLOW'] = 'true'

    subprocess.check_call(
        ["coverage", "run", "--source", "sphinx_icontract", "-m", "unittest", "discover", "tests"],
        cwd=str(repo_root),
        env=env)

    subprocess.check_call(["coverage", "report"])

    print("Doctesting...")
    subprocess.check_call([sys.executable, "-m", "doctest", str(repo_root / "README.rst")])
    for pth in (repo_root / "sphinx_icontract").glob("**/*.py"):
        subprocess.check_call([sys.executable, "-m", "doctest", str(pth)])

    return 0


if __name__ == "__main__":
    sys.exit(main())
