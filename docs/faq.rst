FAQ and Troubleshooting
=======================

This page list some frequently asked questions and troubleshooting.

If you encounter technical issues not listed here, don't hesitate to
`open an issue on GitHub`_. For any other question, please `contact Accelize`_.


Apyfal installation
-------------------

I get errors when trying to install Apyfal with Pip, Host to fix this ?
    Theses kind of errors may appear on some outdated Python environment.
    Update Python environment is the recommended way to fix theses issues.

    Multiple answer are available:

    **Using a dedicated virtual environment:**

    This allows to have a separate environment for each use.

    To install and use a virtual environments, refer to following
    documentations:

    * On any Python versions with `Pipenv`_ (Equivalent to ``pip`` + ``venv`` in
      one command).
    * On Python 3 with `venv`_ standard library module.
    * On Python 2 with `Virtualenv`_ module.

    **Updating all dependencies packages on current environment:**

    Firstly upgrade Pip to the last version

    .. code-block:: bash

        python -m pip install -U pip

    Then, when installing (or updating) Apyfal add following arguments
    to the ``pip install`` command:

    * ``--upgrade --upgrade-strategy eager``: Upgrade all dependencies to the
      last version.
    * ``--ignore-installed``: Completely reinstall all packages.
      To use in case the previous arguments are not sufficient.

Cloud service providers
-----------------------

AWS: How to create access keys ?
    See "`Managing Access Keys for IAM Users`_" on AWS documentation.

AWS: How to run more Accelerator instances on AWS ?
    Request an adjustment of the limit of AWS EC2 F1 instances you can launch
    to `AWS support`_ (0 by default).

.. _contact Accelize: https://www.accelize.com/contact-us
.. _open an issue on Github: https://github.com/Accelize/apyfal/issues
.. _venv: https://docs.python.org/3/library/venv.html
.. _Virtualenv: https://virtualenv.pypa.io
.. _Pipenv: https://pipenv.readthedocs.io
.. _Managing Access Keys for IAM Users: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html
.. _AWS support: http://aws.amazon.com/contact-us/ec2-request
