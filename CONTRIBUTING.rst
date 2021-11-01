
.. highlight: console

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/ecmwf/magics-python/issues

If you are reporting a bug, please include:

* Your operating system name and version.
* Installation method and version of all dependencies.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug, including a sample file.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug"
and "help wanted" is open to whoever wants to implement a fix for it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Get Started!
------------

Ready to contribute? Here's how to set up ``magics-python`` for local development. Please note this documentation assumes
you already have `virtualenv` and `Git` installed and ready to go.

1. Fork the ``magics-python`` repo on GitHub.
2. Clone your fork locally::

    $ cd path_for_the_repo
    $ git clone https://github.com/YOUR_NAME/magics-python.git
    $ cd magics-python

3. Assuming you have virtualenv installed (If you have Python3.5 this should already be there), you can create a new environment for your local development by typing::

    $ virtualenv ../magics-python-env
    $ source ../magics-python-env/bin/activate

    This should change the shell to look something like
    (magics-python-env) $

4. Install program and dependencies as described in the README.rst file then install a known-good set of Python dependencies and the your local copy with::

    $ pip install --editable=.
    $ pip install -r tests/requirements.txt

5. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

6. The next step would be to run the test cases. ``magics-python`` uses py.test, you can run PyTest::

    # First, install some fixtures the test suite needs to run.
    $ git clone --depth 1 https://github.com/ecmwf/magics-test.git
    $ export MAGICS_PYTHON_TESTS=magics-test/test/gallery

    # Invoke test suite.
    export MAGPLUS_HOME=/usr/local/opt/magics-4.9.3
    $ pytest -vvv --flakes

7. Before raising a pull request you should also run tox. This will run the tests across different versions of Python::

    $ tox

9. If your contribution is a bug fix or new feature, you should add a test to the existing test suite.

10. Format your Python code with the Black auto-formatter, to ensure the code is uses the library's style. We use the default Black configuration (88 lines per character and `"` instead of `'` for string encapsulation)::

    $ black .

11. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

12. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.

2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.

3. The pull request should work for Python 2.7, 3.5, 3.6 and 3.7, and for PyPy2 and Pypy3. Check
   the tox results and make sure that the tests pass for all supported Python versions.
