Configuration
=============

*Warning: do not use credentials on untrusted environments. You are
responsible for the secure use of your account.*

What is needed to configure an accelerator ?
--------------------------------------------

Two main configuration steps must be performed before running an accelerator

Accelize account
~~~~~~~~~~~~~~~~

The first part is your Accelize account details (login
and password), which are required to unlock the accelerator:

-  `Accelize credential`_

Your `AccelStore account`_ also provides metering information about your accelerator
use

Host configuration
~~~~~~~~~~~~~~~~~~

Accelerator needs an host with FPGA device that needs to be configured to
run.

See :doc:`getting_started` to see examples of possible cases.

Accelerator configuration
-------------------------

The accelerator can be configured either by using the configuration
file or by passing parameter information to the API directly.

Using the configuration File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use ``accelerator.conf`` file to provide parameters to run your
accelerator.

.. NOTE: "configuration_file.rst" is dynamically generated from "accelerator.conf".
   Update directly documentation in "accelerator.conf" if needed.

For more information on the configuration file, see:

.. toctree::
   :maxdepth: 2

   configuration_file

This file is automatically loaded by the API if found in the current
working directory or current user home directory. A custom path can
also be passed as an argument to the API.

:download:`accelerator.conf example file <../apyfal/accelerator.conf>`.

Passing Parameters to Apyfal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The use of the configuration file is not mandatory; all parameters can
be passed directly to the API as arguments. Please read the API documentation for
more information.

See :doc:`api` for more information.

If both the configuration file and arguments are used to configure an accelerator,
configuration by arguments override configuration file values.

.. _Accelize credential: https://accelstore.accelize.com/user/applications
.. _AccelStore account: https://accelstore.accelize.com/user/metering
