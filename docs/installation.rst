Installation
============

Requirements
------------

Supported Python versions: 2.7, 3.4, 3.5, 3.6

Required Python Packages:

-  ``Request``, ``urllib3``, ``six``, ``certifi``, ``python-dateutil``
-  ``pip`` and ``setuptools``: For package installation
-  ``aliyun-python-sdk-core`` (Optional): Required for Alibaba.
-  ``pyopenssl`` (Optional): Required for Alibaba.
-  ``boto3`` (Optional): Required for AWS.
-  ``openstack`` (Optional): Required for OVH.
-  ``pycurl`` (Optional): Improve upload performance and file size
   limit.

Linux
~~~~~

On Linux, some extra packages are required:

-  *Pip* is required (Package is named ``python-pip`` for Python 2 and
   ``python3-pip`` for Python 3).

-  Depending on the Python version, host targeted and wheel format
   availability, a C/C++ compiler may also be required for install
   dependencies. In this case, *GCC* (Or another compatible compiler) &
   *Python-dev* are required.

-  *PycURL* need ``curl`` package.

Install is done with the package manager of your Linux distribution.

**On RHEL or CentOS**:

*Python-dev* is named ``python-devel`` for Python2 and ``python3-devel``
for Python 3.

Python 2:

.. code-block:: bash

    bash sudo yum install gcc python-pip python-devel curl

Python 3:

.. code-block:: bash

    sudo yum install gcc python3-pip python3-devel curl

**On Debian or Ubuntu**:

*Python-dev* is named ``python-dev`` for Python2 and ``python3-dev`` for
Python 3.

Python 2:

.. code-block:: bash

    sudo apt-get install gcc python-pip python-dev curl

Python 3:

.. code-block:: bash

    sudo apt-get install gcc python3-pip python3-dev curl

Windows
~~~~~~~

Depending on the Python version, host targeted and wheel format
availability, a C/C++ compiler may also be required for install
dependencies.

-  see `Windows Compilers on Python documentation`_

Setup
-----

Installation is done using PIP:

.. code-block:: bash

    pip install apyfal

All mandatory dependencies are automatically installed. It is possible
to install also optional dependencies passing following setuptools
extras:

-  ``all``: Install all extras.
-  ``Alibaba``: Requirements for Alibaba.
-  ``AWS``: Requirements for AWS.
-  ``OVH``: Requirements for OVH.
-  ``optional``: other optional requirements (ex ``pycurl``).

Example for installing the ``all`` extra:

.. code-block:: bash

    pip install apyfal[all]

Example for installing the ``AWS`` + ``optional`` extras:

.. code-block:: bash

    pip install apyfal[AWS,optional]

.. _Windows Compilers on Python documentation: https://wiki.python.org/moin/WindowsCompilers