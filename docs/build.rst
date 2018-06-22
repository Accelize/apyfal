Building apyfal
=======================

Installing apyfal build environment
-------------------------------------------

Prepare Python environment
~~~~~~~~~~~~~~~~~~~~~~~~~~

Ensure that ``pip``, ``setuptools`` and ``wheel`` are installed and up
to date.

.. code-block:: bash

    pip install --upgrade setuptools pip wheel

Clone repository from Github
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

apyfal development version is hosted on github, to get it use
git clone:

.. code-block:: bash

    git clone https://github.com/Accelize/apyfal.git

Generating REST API client with OpenApi
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

apyfal REST API client code (``apyfal.client.rest._openapi``)
is not stored in repository but generated from OpenApi.

This code need to be generated before run apyfal in your
development environment.

   *Java* is required to perform this step.

To generate client code, run the following line in repository directory:

.. code-block:: bash

    ./setup.py swagger_codegen

Installing all apyfal requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install all package that are required to run apyfal, run the
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