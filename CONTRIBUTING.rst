============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

Bug reports
===========

When `reporting a bug <https://github.com/OCXStandard/ocx-schema-parser/issues>`_ please include:

    * Your operating system name and version.
    * Any details about your local setup that might be helpful in troubleshooting.
    * Detailed steps to reproduce the bug.

Documentation improvements
==========================

`ocx-schema-parser` could always use more documentation, whether as part of the
official `ocx-schema-parser` docs, in docstrings, or even on the web in blog posts,
articles, and such.

Feature requests and feedback
=============================

The best way to send feedback is to file an issue at https://github.com/OCXStandard/ocx-schema-parser/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that code contributions are welcome :)

Development
===========

To set up `ocx-schema-parser` for local development:

1. Fork `ocx-schema-parser <https://github.com/OCXStandard/ocx-schema-parser>`_
   (look for the "Fork" button).
2. Clone your fork locally::

    git clone git@github.com:YOURGITHUBNAME/ocx-schema-parser.git

3. Create a branch for local development::

    git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

4. When you're done making changes run all the checks and docs builder with `tox <https://tox.wiki/en/latest/>`_ one command::

    tox

5. Commit your changes and push your branch to GitHub::

    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature

6. Submit a pull request through the GitHub website.

Using Conda environment on Windows
-------------------------------------
It is possible to use the `Conda <https://conda.io/projects/conda/en/latest/index.html>`_ package manager for providing the required python
packages.
Conda can be installed from an `Anaconda or miniconda installation <https://conda.io/projects/conda/en/latest/user-guide/install/index.html>`_.

Create a bootstrap development environment with your python version and pip::

    conda create -n <name> python=<version> pip

This will create the environment with ``python=<version>`` and ``pip`` installed. Then install all the package requirements using the ``conda update`` command::

    conda env update -f environment.yaml


Conda will install the requirements in the ``environment.yaml`` file. You need to manually align the requirements between this file and the requirements in  ``setup.py``. Activate the environment using::

    conda activate <name>


Pull Request Guidelines
-----------------------

If you need some code review or feedback while you're developing the code just make the pull request.

For merging, you should:

1. Include passing tests (run ``tox``).
2. Update documentation when there's new API, functionality etc.
3. Add a note to ``CHANGELOG.rst`` about the changes.
4. Add yourself to ``AUTHORS.rst``.



Tips
----

To run a subset of tests::

    tox -e envname -- pytest -k test_myfeature

To run all the test environments in *parallel*::

    tox -p auto

