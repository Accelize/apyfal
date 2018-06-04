Building acceleratorAPI
=======================

Installing acceleratorAPI build environment
-------------------------------------------

Prepare Python environment
~~~~~~~~~~~~~~~~~~~~~~~~~~

Ensure that ``pip``, ``setuptools`` and ``wheel`` are installed and up
to date.

.. code-block:: bash

    pip install --upgrade setuptools pip wheel

Clone repository from Github
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

acceleratorAPI development version is hosted on github, to get it use
git clone:

.. code-block:: bash

    git clone https://github.com/Accelize/acceleratorAPI.git

Generating REST API client with Swagger-Codegen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

acceleratorAPI REST API client code (``acceleratorAPI._swagger_client``)
is not stored in repository but generated with *Swagger-Codegen*.

This code need to be generated before run acceleratorAPI in your
development environment.

   *Java* is required to perform this step.

To generate client code, run the following line in repository directory:

.. code-block:: bash

    ./setup.py swagger_codegen

Installing all acceleratorAPI requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install all package that are required to run acceleratorAPI, run the
following line in repository directory:

.. code-block:: bash

    pip install -e .[all]

Running tests
-------------

To run unittest, run the following line in repository directory:

.. code-block:: bash

    ./setup.py test

Generating documentation
------------------------

To generate Sphinx documentation, run the following line in repository
directory:

.. code-block:: bash

    ./setup.py build_sphinx

To see generated documentation open ``/build/sphinx/html/index.html``
with your navigator.

Generating wheel package
------------------------

To generate wheel package, run the following line in repository
directory:

.. code-block:: bash

    ./setup.py bdist_wheel

Generated wheel can be found in ``/dist``.