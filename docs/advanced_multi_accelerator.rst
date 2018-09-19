Managing multiple accelerators
==============================

This chapter explain how to manage multiples accelerators.

The Accelerator iterator
------------------------

The accelerator iterator allows to iterate over all already running
accelerators. It can found every host defined in the configuration file.

The iterated accelerators can normally performs all operations provided by the
accelerator class.

The following example shows how to stop all existing accelerators:

.. code-block:: python

   import apyfal

   for accelerator in apyfal.iter_accelerators():
       accelerator.stop('term')

The iterator also provides filters to select accelerators to iterates based on
any accelerator property.

This example shows how to list all accelerator IP address of a specific host
type.

.. code-block:: python

   import apyfal

   addresses = [accelerator.public_ip for accelerator
                in apyfal.iter_accelerators(host_type='my_provider')]

The Accelerator pool executor
-----------------------------

The ``apyfal.AcceleratorPoolExecutor`` is an object inspired by
``concurrent.futures`` that allows to submit processing task to a pool of
multiple accelerator.

It works like the ``apyfal.Accelerator`` in asynchronous mode and provides the
same ``process_submit`` and ``process_map`` methods. The difference is the use
of a pool of accelerator instead of only one accelerator.

Tasks are submitted between accelerators in order to balance the load.

All accelerators in a pool are identical and are created using the same
parameters.

Unlike the single accelerator, the pool executor allows to perform the
hardware accelerated processing in parallel.

.. code-block:: python

   import apyfal

   files = ['/path/myfile1', '/path/myfile2', '/path/myfile3']

   # Instantiates all accelerators in parallel
   with apyfal.AcceleratorPoolExecutor(accelerator='my_accelerator') as executor:

       # Starts all accelerators in parallel with same parameters
       executor.start()

       # Submits tasks between to the accelerator pools
       results = executor.process_map(files_in=files)
