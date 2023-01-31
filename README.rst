========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |github-actions|
        | |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/ocx-schema-parser/badge/?style=flat
    :target: https://ocx-schema-parser.readthedocs.io/
    :alt: Documentation Status

.. |github-actions| image:: https://github.com/ocastrup/ocx-schema-parser/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/ocastrup/ocx-schema-parser/actions

.. |codecov| image:: https://codecov.io/gh/ocastrup/ocx-schema-parser/branch/main/graphs/badge.svg?branch=main
    :alt: Coverage Status
    :target: https://codecov.io/github/ocastrup/ocx-schema-parser

.. |version| image:: https://img.shields.io/pypi/v/ocx-schema-parser.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/ocx-schema-parser

.. |wheel| image:: https://img.shields.io/pypi/wheel/ocx-schema-parser.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/ocx-schema-parser

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/ocx-schema-parser.svg
    :alt: Supported versions
    :target: https://pypi.org/project/ocx-schema-parser

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/ocx-schema-parser.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/ocx-schema-parser

.. |commits-since| image:: https://img.shields.io/github/commits-since/ocastrup/ocx-schema-parser/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/ocastrup/ocx-schema-parser/compare/v0.1.0...main



.. end-badges

A python XML parser for the Open Class 3D Exchange (OCX) schema

* Free software: MIT license

Installation
============

::

    pip install ocx-schema-parser

You can also install the in-development version with::

    pip install https://github.com/ocastrup/ocx-schema-parser/archive/main.zip


Documentation
=============


https://ocx-schema-parser.readthedocs.io/


Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
