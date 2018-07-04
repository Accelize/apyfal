Getting Started
===============

This section explains how to use Apyfal with Python to run accelerators.

All of theses examples requires that you first install the
Apyfal and get configuration requirements like at least your
Accelize credentials (``accelize_client_id`` and ``accelize_secret_id``
parameters in following examples).

See :doc:`installation` and :doc:`configuration` for more information.

You also needs the name (``accelerator`` parameter in following example)
of the accelerator you want to use.

See `AccelStore <https://accelstore.accelize.com>`_ for more information.

*Examples below uses configuration as arguments to be more explicit,
but you can also set them with configuration file.*

*For testing and examples, it is possible to enable apyfal
logger to see more details on running steps:*

.. code-block:: python

    import apyfal
    apyfal.get_logger(True)

Running an accelerator remotely on a cloud instance host
--------------------------------------------------------

This tutorial will cover creating a simple accelerator and
process a file using a Cloud Service Provider (*CSP*) as host.

Parameters required in this case may depends on the CSP used, but it
need always at least:

-  ``host_type``: CSP name
-  ``region``: CSP region name, need a region that support FPGA.
-  ``client_id`` and ``secret_id``: CSP credentials

See :doc:`api_host` for information on possibles parameters of the targeted CSP.

See your CSP documentation to know how obtains theses values.

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
        # In this case a new cloud instance will be provisioned credential passed to
        # Accelerator as host
        # Note: This step can take some minutes depending your CSP
        myaccel.start()

        # Process data:
        # Define witch file you want to process and where they should be stored.
        myaccel.process(file_in='/path/myfile1.dat', file_out='/path/result1.dat')
        myaccel.process(file_in='/path/myfile2.dat', file_out='/path/result2.dat')
        # ... It is possible to process any number of file

    # The accelerator is automatically closed  on "with" exit.
    # In this case, the default stop_mode ('term') is used:
    # the previously created host will be deleted and all its content lost.

Keeping host running
~~~~~~~~~~~~~~~~~~~~

Starting host take long time, so it may be a good idea to keeping it
running for reusing it later.

This is done with the ``stop_mode`` parameter.

*Depending the used CSP, additional fees may apply based on host running time.*
*Don't forget to terminate cloud instance after use*

.. code-block:: python

   import apyfal

   with apyfal.Accelerator(
           accelerator='my_accelerator',
           host_type='my_provider', region='my_region',
           client_id='my_client_id', secret_id='my_secret_id',
           accelize_client_id='my_accelize_client_id',
           accelize_secret_id='my_accelize_secret_id') as myaccel:

       # We can start accelerator with "keep" stop mode to keep host running
       myaccel.start(stop_mode='keep')

       myaccel.process(file_in='/path/myfile.dat', file_out='/path/result.dat')

       # We can get and store host IP and instance ID for later use
       my_host_instance_id = myaccel.host.instance_id
       my_host_ip = myaccel.host.public_ip

   # This time host is not deleted and will stay running when accelerator is close.

Reusing existing host
~~~~~~~~~~~~~~~~~~~~~

With host instance ID and full host access
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With ``instance_id``, depending your CSP, your can reuse an already
existing host without providing ``client_id`` and ``secret_id``.

An accelerator started with ``instance_id`` keep control on this
host an can stop it.

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


With host IP with accelerator only access
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With ``host_ip``, your can reuse an already existing host
without providing any other host information.

An accelerator started with ``host_ip`` have no control over this
host and can't stop it.

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


Running an accelerator locally
------------------------------

This tutorial will cover the use of an accelerator on an already configured FPGA host locally.

Requirements
~~~~~~~~~~~~

An already configured host is required to use this feature.

It is possible to easily create a cloud instance using *Apyfal* and keeping the host running
(Using ``stop_mode='keep'``, See above for more information).

*Don't forget to terminate cloud instance after use to avoid additional fees*

And then connect to it with SSH :

* ``key_pair`` is key pair name that can be get with ``myaccel.host.key_pair``.
  The related private key file in ``.pem`` format is generally stored in the ``.ssh`` sub folder of user home.
* ``host_ip`` is the IP address of the instance and can be get with ``myaccel.host.public_ip``.

**Linux:**

.. code-block:: bash

    ssh -Yt -i ~/.ssh/${key_pair}.pem centos@${host_ip}

**Windows:**

On Windows, `Putty <https://www.chiark.greenend.org.uk/~sgtatham/putty/>`_
can be used to connect with SSH. The private key file needs to be in ``.ppk`` format
(``puttygen.exe``, bundled with Putty, can convert ``.pem`` to ``.ppk``).

.. code-block:: batch

    putty.exe -ssh centos@%host_ip% 22 -i %userprofile%\.ssh\%key_pair%.ppk

Running Apyfal
~~~~~~~~~~~~~~

The use of Apyfal in this case is straightforward since accelerator is preconfigured:

* By default, ``accelize_client_id`` and ``accelize_secret_id`` values are those used to when creating instance.
  It is still possible to change them by passing other values.
* ``accelerator`` value is the one used when creating instance and can not be changed.
* Host related arguments are not required and don't have any effect (``stop_mode``, ``host_ip``...)

.. code-block:: python

   import apyfal

   with apyfal.Accelerator() as myaccel:

       myaccel.start()

       myaccel.process(file_in='/path/myfile.dat', file_out='/path/result.dat')


Configuring accelerators
------------------------

Some accelerators requires to be configured to run. Accelerator
configuration is done with ``start`` and ``process`` methods.

Configuration step: the ``start`` method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parameters passed to ``start`` applies to every ``process`` calls that
follows.

It is possible to call ``start`` a new time to change parameters.

The ``start`` parameters is divided in two parts:

-  The ``datafile`` argument: Some accelerator may require a data file
   to run, this argument is simply the path to this file. Read the
   accelerator documentation to see the file format to use.
-  The ``**parameters`` argument(s): Parameters are *specific
   configuration parameters*, they are passed as keyword arguments. Read
   the accelerator documentation to see possible *specific configuration
   parameters*. Any value passed to this argument overrides default
   configuration values.

.. code-block:: python

   import apyfal

   with apyfal.Accelerator(accelerator='my_accelerator') as myaccel:

       # The parameters are passed to "start" to configure accelerator, parameters are:
       # - datafile: The path to "datafile1.dat" file.
       # - parameter1, parameter2: Keywords parameters passed to "**parameters" arguments.
       myaccel.start(datafile='/path/datafile1.dat',
                     parameter1='my_parameter_1', parameter2='my_parameter_2')

       # Every "process" call after start use the previously specified parameters
       # to perform processing
       myaccel.process(file_in='/path/myfile1.dat', file_out='/path/result1.dat')
       myaccel.process(file_in='/path/myfile2.dat', file_out='/path/result2.dat')
       # ...

       # It is possible to re-call "start" method with other parameters
       myaccel.start(datafile='/path/datafile2.dat')

       # Following "process" will use new parameters.
       myaccel.process(file_in='/path/myfile3.dat', file_out='/path/result3.dat')
       # ...


Process step: the ``process`` method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parameters passed to ``process`` applies only to this ``process`` call.

The ``process`` method accept the following arguments:

-  ``file_in``: Path to the input file. Read the accelerator
   documentation to see if input file is needed.
-  ``file_out``: Path to the output file. Read the accelerator
   documentation to see if an output file is needed.
-  The ``**parameters`` argument(s): Parameters are *specific process
   parameters*, they are passed as keyword arguments. Read the
   accelerator documentation to see possible *specific process
   parameters*. Any value passed to this argument overrides default
   configuration values.

.. code-block:: python

   import apyfal

   with apyfal.Accelerator(accelerator='my_accelerator') as myaccel:
       myaccel.start()

       # The parameters are passed to "process" to configure it, parameters are:
       # - parameter1, parameter2: Keywords parameters passed to "**parameters" arguments.
       myaccel.process(file_in='/path/myfile1.dat', file_out='/path/result1.dat',
                       parameter1='my_parameter_1', parameter2='my_parameter_2')

Metering information
--------------------

Using Accelerators consumes "Coins" based on amount of processed data.

You can access to your metering information on your
`AccelStore account <https://accelstore.accelize.com/user/applications>`_.
