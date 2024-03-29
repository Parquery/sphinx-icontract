"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""
import os

from setuptools import setup, find_packages

import sphinx_icontract_meta

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.rst'), encoding='utf-8') as fid:
    long_description = fid.read().strip()  # pylint: disable=invalid-name

setup(
    name=sphinx_icontract_meta.__title__,
    version=sphinx_icontract_meta.__version__,
    description=sphinx_icontract_meta.__description__,
    long_description=long_description,
    url=sphinx_icontract_meta.__url__,
    author=sphinx_icontract_meta.__author__,
    author_email=sphinx_icontract_meta.__author_email__,
    classifiers=[
        'Development Status :: 5 - Production/Stable', 'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License', 'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7', 'Programming Language :: Python :: 3.8'
    ],
    license='License :: OSI Approved :: MIT License',
    keywords='contracts sphinx extension icontract design-by-contract',
    packages=find_packages(exclude=['tests']),
    install_requires=['icontract>=2.4.0,<3', 'sphinx', 'asttokens>=2,<3'],
    extras_require={
        'dev': [
            'mypy==0.790', 'pylint==2.6.0', 'yapf==0.20.2', 'tox>=3.0.0', 'pyicontract-lint>=2.0.0,<3',
            'pydocstyle>=2.1.1,<3', 'coverage>=4.5.1,<5'
        ]
    },
    py_modules=['sphinx_icontract', 'sphinx_icontract_meta'],
    include_package_data=True,
    package_data={
        "packagery": ["py.typed"],
        '': ['LICENSE.txt', 'README.rst'],
    })
