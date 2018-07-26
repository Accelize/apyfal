Accelerator executable
======================

On its host, accelerator uses a the ``accelerator`` command to communicate with FPGA. It is possible to use this command
directly.

Accelerator CLI do not provides as features as Apyfal CLI, but it can help to reduce latency in some cases.

A configured host is required to use this command. Apyfal can be used to configure an instance and access it with SSH.
See :doc:`getting_started` for more information.

The accelerator command
-----------------------

The accelerator command path is: ``/opt/accelize/accelerator/accelerator``.

It needs to be run as ``root`` (or with ``sudo``)

It support following arguments:

- ``-m``: Accelerator mode. Possibles values are:
  ``0`` for configuration/start mode, ``1`` for process mode, ``2`` for stop mode.
  This is equivalent to ``apyfal.Accelerator`` ``start``, ``process`` and ``stop`` methods.
- ``-i``: Input local file path, used to pass ``datafile`` in configuration mode and ``file_in`` in process mode.
- ``-o``: Output local file path, used to pass ``file_out`` in process mode.
- ``-j``: JSON parameter local file path, used to pass a JSON parameters files like described in :doc:`advanced`.
- ``-p``: JSON output local file path, used to get some results in JSON format.
- ``-v``: Verbosity level. Possible values: from ``0`` (Full verbosity) to ``4`` (Less verbosity).

.. code-block:: bash

    # Configures accelerator with datafile and JSON parameters
    sudo /opt/accelize/accelerator/accelerator -m 0 -i ${datafile} -j ${parameters}

    # Processes file_in and save result to file_out
    sudo /opt/accelize/accelerator/accelerator -m 1 -i ${file_in} -o ${file_out}

Metering services
-----------------

For use accelerator command, metering services needs to be started. This should be the case by default.

Theses commands starts services:

.. code-block:: bash

    sudo systemctl start meteringsession
    sudo systemctl start meteringclient

Theses commands stops services:

.. code-block:: bash

    sudo systemctl stop meteringclient
    sudo systemctl stop meteringsession

In two cases, run order of commands is important.
