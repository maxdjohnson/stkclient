Send To Kindle
==============

.. badges-start

|PyPI| |Status| |Python Version| |License|

|Read the Docs| |Tests| |Codecov|

.. |PyPI| image:: https://img.shields.io/pypi/v/stkclient.svg
   :target: https://pypi.org/project/stkclient/
   :alt: PyPI
.. |Status| image:: https://img.shields.io/pypi/status/stkclient.svg
   :target: https://pypi.org/project/stkclient/
   :alt: Status
.. |Python Version| image:: https://img.shields.io/pypi/pyversions/stkclient
   :target: https://pypi.org/project/stkclient
   :alt: Python Version
.. |License| image:: https://img.shields.io/pypi/l/stkclient
   :target: https://opensource.org/licenses/MIT
   :alt: License
.. |Read the Docs| image:: https://img.shields.io/readthedocs/stkclient/latest.svg?label=Read%20the%20Docs
   :target: https://stkclient.readthedocs.io/
   :alt: Read the documentation at https://stkclient.readthedocs.io/
.. |Tests| image:: https://github.com/maxdjohnson/stkclient/workflows/Tests/badge.svg
   :target: https://github.com/maxdjohnson/stkclient/actions?workflow=Tests
   :alt: Tests
.. |Codecov| image:: https://codecov.io/gh/maxdjohnson/stkclient/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/maxdjohnson/stkclient
   :alt: Codecov

.. badges-end


``stkclient`` implements a client for amazon's "Send to Kindle" service. It allows python programs to
send files to a kindle device without the 10mb limit that applies to email files.

Features
--------

* OAuth-based authorization
* Send large (>10MB) files to Kindle devices


Installation
------------

Python 3.11 or later is required. You can install *Send To Kindle* via pip_ from PyPI_:

.. code:: console

   $ pip install stkclient


Creating a Client
-----------------

To create a client, you must authenticate the user. Currently the only supported authentication mechanism is OAuth2:

.. code:: python

   import stkclient

   a = stkclient.OAuth2()
   signin_url = a.get_signin_url()
   # Open `signin_url` in a browser, sign in and authorize the application, pass
   # the final redirect_url below
   client = a.create_client(redirect_url)

Once a client is created, it can be serialized and deserialized using ``Client.load`` / ``Client.loads`` and ``client.dump`` / ``client.dumps``

.. code:: python

   with open('client.json', 'w') as f:
       client.dump(f)
   with open('client.json', 'r') as f:
       client = stkclient.Client.load(f)


Sending a File
--------------

Once you have a Client object, you can list devices and send files to specified devices.

.. code:: python

   devices = client.get_owned_devices()
   destinations = [d.device_serial_number for d in devices]
   client.send_file(filepath, destinations, author=author, title=title, format="epub")

The ``format`` argument describes the input file. PDFs are delivered with their
original page layout by default. To convert a PDF to Kindle format, set
``force_convert=True``:

.. code:: python

   client.send_file(
       filepath, destinations, author=author, title=title,
       format="pdf", force_convert=True,
   )


Development
-----------

Install uv_ 0.13.0 or later, then create the development environment and run the
tools directly. The checked-in ``.python-version`` selects Python 3.12; uv
downloads it automatically if needed.

.. code:: console

   $ uv sync --locked
   $ uv run --locked pytest
   $ uv run --locked mypy --pretty src tests docs/conf.py
   $ uv run --locked pytest --typeguard-packages=stkclient
   $ uv run --locked python -m xdoctest --modname=stkclient --command=all
   $ uv run --locked pre-commit run --all-files --show-diff-on-failure

GitHub Actions owns the Python and operating-system test matrix in
``.github/workflows/tests.yml``. To test a specific Python version locally,
select it explicitly and install only the test dependency group:

.. code:: console

   $ uv run --locked --no-default-groups --group test --no-editable --python 3.11 pytest

To collect and report coverage locally:

.. code:: console

   $ uv run --locked coverage run -m pytest
   $ uv run --locked coverage report

Build the same documentation formats as CI with warnings treated as errors:

.. code:: bash

   for builder in html epub latex; do
     uv run --locked sphinx-build -W --keep-going -b "$builder" \
       -d "docs/_build/doctrees/$builder" docs "docs/_build/$builder"
   done

Use ``uv run --locked sphinx-autobuild --open-browser docs docs/_build/html``
to preview the documentation with live reloading.

Audit all locked runtime, test, and development dependencies against the PyPI
vulnerability database:

.. code:: bash

   requirements=$(mktemp)
   uv export --locked --all-groups --no-emit-project --output-file "$requirements" > /dev/null
   uv run --locked pip-audit --strict --disable-pip --no-deps -r "$requirements"
   rm "$requirements"

Dependencies live in ``pyproject.toml`` and their resolved versions in
``uv.lock``. Commit both files when dependencies change. Use ``uv add`` for
runtime dependencies, ``uv add --group test --bounds exact`` for test dependencies,
and ``uv lock --upgrade-package NAME`` for targeted updates. Purpose-specific
groups keep CI environments small; the default ``dev`` group includes all
development tools. For example, ``uv sync --locked --no-default-groups --group
test --python 3.11`` installs only the package and test tools on Python 3.11.

Build distributions with ``uv build --no-sources``. Update the package version
with ``uv version --bump patch`` (or ``minor`` / ``major``), committing the
updated ``pyproject.toml`` and ``uv.lock`` together.

Pre-commit runs Ruff for Python linting, import sorting, syntax
upgrades, and formatting. Its configuration lives in ``pyproject.toml`` and checks
for unused or invalid ``noqa`` comments. Install the Git hooks with
``uv run --locked pre-commit install``. Local hooks invoke uv directly, so the
environment does not need to be activated when committing.

CI tests Python 3.11 through 3.15 and runs the newest version on Linux, macOS,
and Windows. The minimum Python version follows the `Python support schedule`_.
Maintenance tools run on Python 3.12. Pull requests also build the
release distributions; publishing remains limited to pushes to the main branch.

.. _Python support schedule: https://devguide.python.org/versions/
.. _uv: https://docs.astral.sh/uv/getting-started/installation/


Related Projects
----------------

`KindBeamer <https://github.com/jooray/kindbeamer>`__ a GUI application implementing the same protocol.


License
-------

Distributed under the terms of the `MIT license`_,
*Send To Kindle* is free and open source software.

.. _MIT license: https://opensource.org/licenses/MIT
.. _PyPI: https://pypi.org/
.. _pip: https://pip.pypa.io/
