Installation
============

Requirements
------------

Supported Python versions: 2.7, 3.4, 3.5, 3.6, 3.7

Required Python Packages:

-  ``Request``, ``urllib3``, ``six``, ``certifi``, ``python-dateutil``, ``ipgetter``, ``psutil``, ``cryptography``
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
   The ``PYCURL_SSL_LIBRARY`` environment variable need to be set to the selected SSL library before building.

Use the package manager of the Linux distribution to install packages.

RHEL or CentOS 7:
^^^^^^^^^^^^^^^^^

The `EPEL repository`_ is required to install some packages.

``-dev`` package suffix is renamed ``-devel`` on RHEL/CentOS.

Python 2.7 is the only Python version installed by default on RHEL/CentOS 7. But installation of Python 3.6 is possible.

**Python 3:**

The `IUS repository`_ is required to install Python 3.6 packages.

.. code-block:: bash

    sudo yum install gcc python36u python36u-pip python36u-devel libcurl-devel openssl-devel -y
    export PYCURL_SSL_LIBRARY=openssl

Use ``python3.6`` instead of ``python`` and ``pip3.6`` instead of ``pip`` to call Python and Pip from this point on.

**Python 2:**

.. code-block:: bash

    sudo yum install gcc python-pip python-devel libcurl-devel openssl-devel -y
    export PYCURL_SSL_LIBRARY=openssl

Debian or Ubuntu:
^^^^^^^^^^^^^^^^^

Pycurl is already packaged ``python-pycurl`` on Debian and doesn’t need to be built from source.

**Python 3:** (*Debian 8 Jessie*/*Ubuntu 14.04 Trusty* and more)

Python 3 packages are prefixed ``python3-`` instead of ``python-``.

.. code-block:: bash

    sudo apt-get install gcc python3-pip python3-dev python3-pycurl

Use ``python3`` instead of ``python`` and ``pip3`` instead of ``pip`` to call Python and Pip from this point on.

**Python 2:**

.. code-block:: bash

    sudo apt-get install gcc python-pip python-dev python-pycurl

Windows
~~~~~~~

Python for Windows is available on the `Python Website`_.

Depending on the Python version, the host targeted, and wheel format availability,
a C/C++ compiler may also be required to install dependencies.

-  See `Windows Compilers on Python documentation`_ for more information.

Some modules, like ``PycURL``, can be found as precompiled wheels here if not available directly from PyPI:
`Unofficial Windows Binaries for Python Extension Packages`_.
Download the wheel file for the selected Python version and run pip on it:

.. code-block:: bash

    pip install pycurl‑7.43.1‑cp37‑cp37m‑win_amd64.whl

Setup
-----

Installation is performed using PIP:

.. code-block:: bash

    pip install apyfal

All mandatory dependencies are automatically installed.
You can also install these optional extras:

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

.. _EPEL repository: https://fedoraproject.org/wiki/EPEL
.. _IUS repository: https://ius.io/GettingStarted/#subscribing-to-the-ius-repository
.. _Python Website: https://www.python.org/downloads
.. _Windows Compilers on Python documentation: https://wiki.python.org/moin/WindowsCompilers
.. _Unofficial Windows Binaries for Python Extension Packages: https://www.lfd.uci.edu/~gohlke/pythonlibs