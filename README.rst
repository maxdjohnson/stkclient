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

Install the CI tools with Python 3.12, then run the same Nox sessions as CI:

.. code:: console

   $ python3.12 -m pip install -c .github/workflows/constraints.txt poetry poetry-plugin-export nox nox-poetry
   $ nox -s tests-3.12 mypy typeguard xdoctest docs-build pre-commit audit

CI tests Python 3.11 through 3.15 and runs the newest version on Linux, macOS,
and Windows. The minimum Python version follows the `Python support schedule`_.
Maintenance tools run on Python 3.12. The ``audit`` session checks locked runtime,
test, and development dependencies against the PyPI vulnerability database.
The documentation sessions install ``docs/requirements.txt``, the same
dependencies as Read the Docs. ``docs-build`` checks HTML, EPUB, and LaTeX output
with warnings treated as errors; HTML is written to ``docs/_build/html``.
Read the Docs additionally compiles the LaTeX output into a downloadable PDF.
To preview the HTML with live reloading, run ``nox -s docs``.

Pull requests also build the release distributions and retain them as the
``dist`` workflow artifact. Publishing remains limited to pushes to the main
branch.

.. _Python support schedule: https://devguide.python.org/versions/


Documentation and release maintenance
-------------------------------------

Read the Docs builds ``latest`` from ``main``. Check the `documentation build
history`_ for configuration errors if the docs badge turns red. The ``stable``
version follows the latest release tag, so fixes on ``main`` only reach it with
a new release. The old ``v0.1.1`` tag has no successful ``stable`` build; use
the `latest documentation`_ until a new release is published.

The release workflow publishes version bumps to PyPI and development versions
to TestPyPI. Development uploads run in a separate job so TestPyPI outages or
account problems do not block updates to the release-note draft. Upload failures
still fail the workflow.

Token-based publishing requires two-factor authentication on the account that
owns the token, separately on PyPI and TestPyPI. Enable it in each account's
settings and configure the repository secrets ``PYPI_TOKEN`` and
``TEST_PYPI_TOKEN`` with tokens authorized for ``stkclient``. A TestPyPI 403
reporting missing two-factor authentication must be fixed in the TestPyPI
account; changing workflow permissions cannot resolve it.

.. _documentation build history: https://app.readthedocs.org/projects/stkclient/builds/
.. _latest documentation: https://stkclient.readthedocs.io/en/latest/


Related Projects
----------------

`KindBeamer <https://github.com/jooray/kindbeamer>`__ a GUI application implementing the same protocol.


License
-------

Distributed under the terms of the `MIT license`_,
*Send To Kindle* is free and open source software.


Credits
-------

Project structure from `@cjolowicz`_'s `Hypermodern Python Cookiecutter`_ template.

.. _@cjolowicz: https://github.com/cjolowicz
.. _MIT license: https://opensource.org/licenses/MIT
.. _PyPI: https://pypi.org/
.. _Hypermodern Python Cookiecutter: https://github.com/cjolowicz/cookiecutter-hypermodern-python
.. _pip: https://pip.pypa.io/
