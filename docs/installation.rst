Installation
============

Requirements
------------

Supported Python versions: 2.7, 3.4, 3.5, 3.6, 3.7

Python 3.5 or more is recommended.

Linux
~~~~~

On Linux, some extra packages are required:

-  *Pip* is required.

-  Depending on the Python version, host targeted and wheel format availability,
   a C/C++ compiler may also be required for install dependencies.
   In this case, ``GCC`` (Or another compatible compiler) & ``Python-dev``
   packages are required.

Use the package manager of the Linux distribution to install packages.

RHEL or CentOS 7:
^^^^^^^^^^^^^^^^^

The `EPEL repository`_ is required to install some packages.

``-dev`` package suffix is renamed ``-devel`` on RHEL/CentOS.

Python 2.7 is the only Python version installed by default on RHEL/CentOS 7.
But installation of Python 3.6 is possible.

**Python 3:**

The `Software Collections repository`_ is required to install Python 3.6
packages.

.. code-block:: bash

    sudo yum install gcc python36 python36-pip python36-devel -y

Use ``python36`` instead of ``python`` and ``pip36`` instead of ``pip`` to
call Python and Pip from this point on.

**Python 2:**

.. code-block:: bash

    sudo yum install gcc python-pip python-devel -y

Debian or Ubuntu:
^^^^^^^^^^^^^^^^^

**Python 3:** (*Debian 8 Jessie*/*Ubuntu 14.04 Trusty* and more)

Python 3 packages are prefixed ``python3-`` instead of ``python-``.

.. code-block:: bash

    sudo apt-get install gcc python3-pip python3-dev

Use ``python3`` instead of ``python`` and ``pip3`` instead of ``pip`` to call
Python and Pip from this point on.

**Python 2:**

.. code-block:: bash

    sudo apt-get install gcc python-pip python-dev

Windows
~~~~~~~

Python for Windows is available on the `Python Website`_.

Depending on the Python version, the host targeted, and wheel format
availability, a C/C++ compiler may also be required to install dependencies.

-  See `Windows Compilers on Python documentation`_ for more information.

Setup
-----

All installation is performed using PIP.

The base package with all features and AWS support can be installed with:

.. code-block:: bash

    pip install apyfal

Some extra host type are supported as optional components.

You can also install these optional extras:

-  ``all``: Install all extras.
-  ``Alibaba``: Requirements for Alibaba.
-  ``AWS``: Requirements for AWS (Installed by default).
-  ``OpenStack``: Requirements for OpenStack.
-  ``OVH``: Requirements for OVH.

Example for installing the ``all`` extra:

.. code-block:: bash

    pip install apyfal[all]

Example for installing the ``OpenStack`` + ``Alibaba`` extras:

.. code-block:: bash

    pip install apyfal[OpenStack,Alibaba]

.. _EPEL repository: https://fedoraproject.org/wiki/EPEL
.. _Software Collections repository: https://access.redhat.com/documentation/en-us/red_hat_software_collections/3/
.. _Python Website: https://www.python.org/downloads
.. _Windows Compilers on Python documentation: https://wiki.python.org/moin/WindowsCompilers
