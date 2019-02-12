Starting a custom host
======================

This section explain how to customize the Accelerator host to run.

Overriding specific host parameters
-----------------------------------

Some hosts provides the ability to override some parameters of the lower level
libraries used to run them.

For each host class, overriding parameters are represented by arguments of the
``dict`` type with a name that finish by ``kwargs``.

The content of theses dict are specific to each case and their description can
be found in the target library documentation.

Example with AWS EC2.
    The AWS host provides some ``dict`` arguments to customize the ``boto3``
    client used to run AWS instances:

    * ``boto3_session_kwargs``:
      Overrides arguments of the `boto3.session.Session`_ class.
    * ``boto3_client_kwargs``:
      Overrides arguments of the `boto3.session.Session.client`_ method.
    * ``boto3_create_instances_kwargs``: Overrides arguments of the
      `boto3.session.Session.resource('ec2').create_instances`_ method.

    With this it is by example possible to change billing options when creating
    the instance. Example with the use of AWS spot instance:

    .. code-block:: python

       import apyfal

        # Based on AWS documentation, create a dict containing arguments to pass
        # to the "create_instances" method.
        use_spot_instance = {
            'InstanceMarketOptions': {
                'MarketType': 'spot',
                'SpotOptions': {
                    'SpotInstanceType': 'one-time',
                    'InstanceInterruptionBehavior': 'terminate',
                    }
                },
            'InstanceInitiatedShutdownBehavior': 'terminate',
        }

       # On Accelerator instantiation, pass the dict to the
       # "boto3_create_instances_kwargs" argument.
       with apyfal.Accelerator(
               accelerator='my_accelerator', host_type='AWS',
               boto3_create_instances_kwargs=use_spot_instance) as myaccel:

           # Continue the use of the accelerator as normal.
           myaccel.start()

Starting host manually
----------------------

The following explain how start an host without the use of Apyfal.

This is not the recommended way to instantiate an accelerator, but, this allow
to use a more custom host configuration.

Getting host requirements
~~~~~~~~~~~~~~~~~~~~~~~~~

The host configuration differ depending the target host.
It is possible to get the configuration to use with Apyfal.

.. code-block:: python

   import apyfal

   # Load Apyfal "accelerator.conf" configuration file
   config = apyfal.configuration.Configuration()

   # Configuration file needs at least Accelize access keys, if not present in
   # file, it is possible to add it programmatically:
   config['accelize']['client_id'] = 'my_client_id'
   config['accelize']['secret_id'] = 'my_secret_id'

   # Get configuration from Accelize server
   host_config = config.get_host_requirements(
       host_type='my_provider', accelerator='my_accelerator')

The ``host_config`` is a dictionary that contain all required information
to configure the host. Depending the ``host_type``, this dictionary may contain
sub-dictionaries representing sub-categories like the CSP ``region``.

Following values may be found inside it (Depending the ``host_type``):

* ``image``: Host virtual machine image to use on CSP.
* ``instancetype``: The type/flavor of instance to use on CSP.
* ``fpgaimage``: The FPGA device bitstream image. This value may be ignored and
  will be configured automatically in following steps.

Instantiating host
~~~~~~~~~~~~~~~~~~

The host can now be instantiated and started using previously retrieved
parameters. This step is different for each ``host_type`` and will not be
explained here. Read your host provider documentation for more information.

Configuring accelerator on host
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once the host is started and ready to use, connect to it using SSH:

.. code-block:: bash

    ssh -Yt -i ~/.ssh/${key_pair}.pem centos@${host_ip}

Create the ``/home/centos/accelerator.conf`` file and complete it with at least:

 * ``client_id`` and ``secret_id`` in ``accelize`` section
 * ``host_type`` and ``region`` in ``host`` section.

Then, run Apyfal CLI to set initial configuration of the FPGA device:

.. code-block:: bash

    apyfal create --accelerator my_accelerator
    apyfal start

The Accelerator is now ready to use.

.. _boto3.session.Session: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html
.. _boto3.session.Session.client: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html#boto3.session.Session.client
.. _boto3.session.Session.resource('ec2').create_instances: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.ServiceResource.create_instances
