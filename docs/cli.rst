Apyfal CLI
==========

Apyfal CLI is a command line interface to use Apyfal directly in shell without
the need to use Python.

Apyfal CLI commands
-------------------

Apyfal CLI provides help using ``-h`` or ``--help`` arguments:

.. code-block:: bash

    apyfal -h

Apyfal CLI needs to be run with a command, following command are available:

* ``create``: Create accelerator and configure host. Equivalent to
  ``apyfal.Accelerator`` instantiation. Calling ``create`` is optional if called
  without arguments (By example when run locally on an already configured host).
* ``start``: Start and configure Accelerator. Equivalent to
  ``apyfal.Accelerator.start`` method.
* ``process``: Process with Accelerator. Equivalent to
  ``apyfal.Accelerator.process`` method.
* ``stop``: Stop accelerator. Equivalent to ``apyfal.Accelerator.stop`` method.
* ``copy``: Copy Apyfal Storage URL. Equivalent to ``apyfal.storage.copy``
  function.
* ``clear``: Clear cached accelerators. New command, specific to CLI mode
  (detailed below).

Each command accept the sames parameters as its ``apyfal`` library equivalent.
Keywords arguments names needs to be prefixed with ``--``.

.. code-block:: bash

    # Values can be passed after argument separated with space or equal:
    apyfal create --accelerator=my_accelerator --host_type=my_provider

    # Is equivalent to
    apyfal create --accelerator my_accelerator --host_type my_provider

    # Some arguments proposes also short aliases prefixed by ``-``
    apyfal create -a my_accelerator --host_type my_provider

Apyfal CLI provides command specific help. Uses it for more information.

.. code-block:: bash

    apyfal create -h


Full commands documentation:

.. toctree::
   :maxdepth: 2

   cli_help

Using accelerator with Apyfal CLI
---------------------------------

The use of accelerator with CLI is the same as the library,
see :doc:`getting_started` for more information

This example show the basic use of an accelerator using Apyfal CLI :

.. code-block:: bash

    # Accelerator instantiation
    apyfal create --accelerator my_accelerator

    # Accelerator start
    apyfal start

    # Accelerator process
    apyfal process --file_in /path/myfile.dat --file_out /path/result.dat

    # Accelerator stop
    # Do not forget this step, this is not automatically handled with CLI
    apyfal stop

Specific start and process arguments are passed like others:

.. code-block:: bash

    apyfal process --file_in /path/myfile.dat --specific1 1 --specific2 2


Using multiple accelerators
~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to use multiple accelerators at the same time by naming them with
different names using the ``--name`` argument:

.. code-block:: bash

    # Instantiate accelerator and name it
    apyfal create --accelerator my_accelerator --name myaccel

    # Run "start" on "myaccel"
    apyfal start --name myaccel

    # Run "process" on "myaccel"
    apyfal process --name myaccel --file_in /path/myfile.dat --file_out /path/result.dat

    # Run "stop" on "myaccel"
    # Do not forget this step, this is not automatically handled with CLI
    apyfal stop --name myaccel

It is possible to clear all previously existing accelerator with the ``clear``
command. Warning: This don't stop accelerators.

.. code-block:: bash

    apyfal clear
