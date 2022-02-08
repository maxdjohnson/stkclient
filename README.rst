Send To Kindle
==============

|PyPI| |Status| |Python Version| |License|

|Read the Docs| |Tests| |Codecov|

|pre-commit| |Black|

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
.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
.. |Black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Black


``stkclient`` implements a client for amazon's "Send to Kindle" service. It allows python programs to
send files to a kindle device without the 10mb limit that applies to email files.

Features
--------

* OAuth-based authorization
* Send large (>10MB) files to Kindle devices


Requirements
------------

* TODO


Installation
------------

You can install *Send To Kindle* via pip_ from PyPI_:

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
   destinations = [d.device_serial_number for d in devices.owned_devices]
   client.send_file(filepath, destinations, author=author, title=title)


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
