Getting Started
===============

This section explains how to use Apyfal with Python to run accelerators.

All of these examples require you to first install the Apyfal and to have an Accelize account
(the ``accelize_client_id`` and ``accelize_secret_id`` parameters in following examples).

See :doc:`installation` and :doc:`configuration` for more information.

You also need the name of the accelerator you want to use (The ``accelerator`` parameter in following example)

See `AccelStore <https://accelstore.accelize.com>`_ for more information.

*The examples below use configuration by arguments for clarity,
but you can also set them using the configuration file.*

*You can enable the Apyfal logger to see more details about each step
that’s running. This is particularly useful for when running tests or going through
examples:*

.. code-block:: python

    import apyfal
    apyfal.get_logger(True)

Running an accelerator remotely on a cloud instance host
--------------------------------------------------------

This tutorial will describe how to create a simple accelerator and process a file using a
Cloud Service Provider (*CSP*) as a host.

The parameters required in this case may depend on the CSP used, but will
always include:

-  ``host_type``: CSP name
-  ``region``: CSP region name (a region that supports FPGA is required).
-  ``client_id`` and ``secret_id``: CSP account details

See :doc:`api_host` for information about potential parameters of the targeted CSP.

See your CSP documentation for information about how to obtain these values.

.. code-block:: python

    # Import the accelerator module.
    import apyfal

    # Choose an accelerator to use and configure it.
    with apyfal.Accelerator(
            # Accelerator parameters
            accelerator='my_accelerator',
            # host parameters
            host_type='my_provider', region='my_region',
            client_id='my_client_id', secret_id='my_secret_id',
            # Accelize parameters
            accelize_client_id='my_accelize_client_id',
            accelize_secret_id='my_accelize_secret_id') as myaccel:

        # Start the accelerator:
        # A new cloud instance will be created and your account details passed to
        # Accelerator as host
        # Note: This step can take some minutes, depending on the CSP
        myaccel.start()

        # Process data:
        # Define which file to process and where they should be stored.
        myaccel.process(file_in='/path/myfile1.dat', file_out='/path/result1.dat')
        myaccel.process(file_in='/path/myfile2.dat', file_out='/path/result2.dat')
        # ... It is possible to process any number of file

    # The accelerator is automatically closed  on "with" exit.
    # In this case, the default stop_mode ('term') is used:
    # the previously created host will be deleted and all its content lost.

Keeping host running
~~~~~~~~~~~~~~~~~~~~

Starting a host takes a long time, so it may be a good idea to keep it running for later
use.

You can do this using the ``stop_mode`` parameter.

*Depending on your CSP, additional fees may apply based on the host running
time. Don’t forget to terminate your cloud instance after use.*

.. code-block:: python

   import apyfal

   with apyfal.Accelerator(
           accelerator='my_accelerator',
           host_type='my_provider', region='my_region',
           client_id='my_client_id', secret_id='my_secret_id',
           accelize_client_id='my_accelize_client_id',
           accelize_secret_id='my_accelize_secret_id') as myaccel:

       # We can start the accelerator in &quot;keep&quot; stop mode to keep the host running
       myaccel.start(stop_mode='keep')

       myaccel.process(file_in='/path/myfile.dat', file_out='/path/result.dat')

       # We can get and store the host IP and instance ID for later use
       my_host_instance_id = myaccel.host.instance_id
       my_host_ip = myaccel.host.public_ip

   # This time the host is not deleted and will stay running when the accelerator is closed.

Reusing an Existing Host
~~~~~~~~~~~~~~~~~~~~~~~~

With host instance ID and full host access
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With ``instance_id``, depending on your CSP, you can reuse an already existing host
without providing the ``client_id`` and ``secret_id``.

An accelerator started with ``instance_id`` keeps control of the host and can stop it at any
time.

.. code-block:: python

   import apyfal

   # We select the host to use on Accelerator instantiation
   # with its instance ID stored previously
   with apyfal.Accelerator(
           accelerator='my_accelerator',
           host_type='my_provider', region='my_region',
           # Use 'instance_id' and removed 'client_id' and 'secret_id'
           instance_id='my_host_instance_id',
           accelize_client_id='my_accelize_client_id',
           accelize_secret_id='my_accelize_secret_id') as myaccel:

       myaccel.start()

       myaccel.process(file_in='/path/myfile.dat', file_out='/path/result.dat')


With Host IP with Accelerator-Only Access
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With ``host_ip``, you can reuse an already existing host without providing any other host
information.

An accelerator started with ``host_ip`` has no control over the host and can’t stop it.

.. code-block:: python

   import apyfal

   # We also can select the host to use on Accelerator instantiation
   # with its IP address stored previously
   with apyfal.Accelerator(
           accelerator='my_accelerator',
           # Use 'host_ip' and removed any other host parameter
           host_ip='my_host_ip',
           accelize_client_id='my_accelize_client_id',
           accelize_secret_id='my_accelize_secret_id') as myaccel:

       myaccel.start()

       myaccel.process(file_in='/path/myfile.dat', file_out='/path/result.dat')


Running an Accelerator Locally
------------------------------

This tutorial describes using an accelerator locally on an already-configured FPGA host.

Requirements
~~~~~~~~~~~~

An already-configured host is required to use this feature.

You can easily create a cloud instance using *Apyfal* and keep the host running using
the ``stop_mode='keep'``; parameter. See above for more information.

*Don’t forget to terminate the cloud instance after use to avoid additional fees.*

You connect to your host using SSH:

- ``key_pair`` is the key pair name that can be obtained with ``myaccel.host.key_pair``.
  The related private key file in ``.pem`` format is generally stored in the ``.ssh`` sub folder of user home.
- ``host_ip`` is the IP address of the instance and can be obtained with ``myaccel.host.public_ip``.

**Linux:**

.. code-block:: bash

    ssh -Yt -i ~/.ssh/${key_pair}.pem centos@${host_ip}

**Windows:**

On Windows, you can use `Putty <https://www.chiark.greenend.org.uk/~sgtatham/putty/>`_
to connect with SSH. The private key file needs to be in ``.ppk`` format
(``puttygen.exe``, supplied with Putty, can convert ``.pem`` to ``.ppk``).

.. code-block:: batch

    putty.exe -ssh centos@%host_ip% 22 -i %userprofile%\.ssh\%key_pair%.ppk

Running Apyfal
~~~~~~~~~~~~~~

Running Apyfal in this case is straightforward as the accelerator is preconfigured:

- By default, the ``accelize_client_id`` and ``accelize_secret_id`` values are those used when creating an instance.
  You can change them by passing other values.
- ``accelerator`` value is the one used when creating an instance and cannot be changed.
- Host related arguments are not required and don’t have any effect (``stop_mode``, ``host_ip``, etc)

.. code-block:: python

   import apyfal

   with apyfal.Accelerator() as myaccel:

       myaccel.start()

       myaccel.process(file_in='/path/myfile.dat', file_out='/path/result.dat')


Configuring accelerators
------------------------

Some accelerators require configuration before being run. An accelerator is configured
using the ``start`` and ``process`` methods.

Configuration step: the ``start`` method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parameters passed to ``start`` apply to every ``process`` calls that follows.

You can call ``start`` again to change parameters.

The ``start`` parameters is divided in two parts:

- The ``datafile`` argument: Some accelerators may require a data file to run; this argument is
  simply the path to this file. Read the accelerator documentation to see the file format to use.
- The ``**parameters`` argument(s): Parameters are *specific configuration parameters* that are
  passed as keyword arguments. See the accelerator documentation for more information
  about possible *specific configuration parameters*. Any value passed to this argument
  overrides the default configuration values.

.. code-block:: python

   import apyfal

   with apyfal.Accelerator(accelerator='my_accelerator') as myaccel:

       # The parameters are passed to "start" to configure the accelerator; theses parameters are:
       # - datafile: The path to "datafile1.dat" file.
       # - parameter1, parameter2: Keywords parameters are passed to "**parameters" arguments.
       myaccel.start(datafile='/path/datafile1.dat',
                     parameter1='my_parameter_1', parameter2='my_parameter_2')

       # Every "process" call after start uses the previously specified parameters
       # to perform processing
       myaccel.process(file_in='/path/myfile1.dat', file_out='/path/result1.dat')
       myaccel.process(file_in='/path/myfile2.dat', file_out='/path/result2.dat')
       # ...

       # It is possible to re-call "start" method with other parameters
       myaccel.start(datafile='/path/datafile2.dat')

       # The following "process" will use new parameters.
       myaccel.process(file_in='/path/myfile3.dat', file_out='/path/result3.dat')
       # ...


Process step: the ``process`` method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parameters passed to ``process`` applies only to this ``process`` call.

The ``process`` method accept the following arguments:

- ``file_in``: Path to the input file. Check the accelerator documentation to see if an input file is required.
- ``file_out``: Path to the output file. Check the accelerator documentation to see if an output file is required.
- The ``**parameters`` argument(s): Parameters are *specific configuration parameters* that are
  passed as keyword arguments. See the accelerator documentation for more information
  about possible *specific configuration parameters*. Any value passed to this argument
  overrides the default configuration values.

.. code-block:: python

   import apyfal

   with apyfal.Accelerator(accelerator='my_accelerator') as myaccel:
       myaccel.start()

       # The parameters are passed to "process" to configure it; theses parameters are:
       # - parameter1, parameter2: Keywords parameters are passed to "**parameters" arguments.
       myaccel.process(file_in='/path/myfile1.dat', file_out='/path/result1.dat',
                       parameter1='my_parameter_1', parameter2='my_parameter_2')

Metering information
--------------------

Using Accelerators consumes “coins” based on the amount of processed data.
You can access your metering information via your `AccelStore account <https://accelstore.accelize.com/user/applications>`_.
