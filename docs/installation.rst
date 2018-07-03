Installation
============

Requirements
------------

Supported Python versions: 2.7, 3.4, 3.5, 3.6, 3.7

Required Python Packages:

-  ``Request``, ``urllib3``, ``six``, ``certifi``, ``python-dateutil``, ``ipgetter``, ``psutil``
-  ``pip`` and ``setuptools``: For package installation
-  ``boto3`` (Optional): Required for AWS.
-  ``openstack`` (Optional): Required for OpenStack and OVH.
-  ``pycurl`` (Optional): Improve upload performance and file size limit.

Linux
~~~~~

On Linux, some extra packages are required:

-  *Pip* is required.

-  Depending on the Python version, host targeted and wheel format availability,
   a C/C++ compiler may also be required for install dependencies.
   In this case, ``GCC`` (Or another compatible compiler) & ``Python-dev`` packages are required.

-  *PycURL* needs ``libcurl-dev`` package to be build.
-  *PycURL* needs a SSL library (like ``openssl-dev``) to support HTTPS.
   ``PYCURL_SSL_LIBRARY`` environment variable need to be set to the selected SSL library before building.

Install is done with the package manager of your Linux distribution.

RHEL or CentOS 7:
^^^^^^^^^^^^^^^^^

``-dev`` package suffix is renamed ``-devel`` on RHEL/CentOS.

**Python 2:**

.. code-block:: bash

    sudo yum install gcc python-pip python-devel libcurl-devel openssl-devel
    export PYCURL_SSL_LIBRARY=openssl

**Python 3:**

Python 2.7 is the only Python version installed by default on RHEL/CentOS 7.

Debian or Ubuntu:
^^^^^^^^^^^^^^^^^

Pycurl is already packaged ``python-pycurl`` on Debian and don't need to be built from source.

**Python 2:**

.. code-block:: bash

    sudo apt-get install gcc python-pip python-dev python-pycurl

**Python 3:**

Python 3 packages are prefixed ``python3-`` instead of ``python-``.

.. code-block:: bash

    sudo apt-get install gcc python3-pip python3-dev python3-pycurl

Windows
~~~~~~~

Depending on the Python version, host targeted and wheel format
availability, a C/C++ compiler may also be required for install
dependencies.

-  see `Windows Compilers on Python documentation`_

Some modules, like ``PycURL``, can be found as precompiled wheels here if not available directly from PyPI:
`Unofficial Windows Binaries for Python Extension Packages`_.
Download the wheel file for the selected Python version and run pip on it:

.. code-block:: bash

    pip install pycurl‑7.43.1‑cp37‑cp37m‑win_amd64.whl

Setup
-----

Installation is done using PIP:

.. code-block:: bash

    pip install apyfal

All mandatory dependencies are automatically installed. It is possible
to install also optional dependencies passing following setuptools
extras:

-  ``all``: Install all extras.
-  ``AWS``: Requirements for AWS.
-  ``OpenStack``: Requirements for OpenStack.
-  ``OVH``: Requirements for OVH.
-  ``optional``: other optional requirements (ex ``pycurl``).

Example for installing the ``all`` extra:

.. code-block:: bash

    pip install apyfal[all]

Example for installing the ``OpenStack`` + ``optional`` extras:

.. code-block:: bash

    pip install apyfal[OpenStack,optional]

.. _Windows Compilers on Python documentation: https://wiki.python.org/moin/WindowsCompilers
.. _Unofficial Windows Binaries for Python Extension Packages: https://www.lfd.uci.edu/~gohlke/pythonlibs