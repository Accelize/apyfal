Changelog
=========

2.0.0 (2019/XX)
---------------

Improvements:

- ``Apyfal.aws.AWSHost`` now support and use of spot instances by default.
  This can be disabled with the ``spot_instance=False`` parameter.
  Spot block duration can be specified using the ``spot_block_duration``
  parameter.

Deprecations:

- Python 3.4 support is deprecated.

1.2.7 (2019/04)
---------------

Deprecations:

- Deprecate OVH support (OVH stopped FPGA support).
- Warn about Python 3.4 pending deprecation.
- Remove links to the deprecated AccelStore (Move to the
  Accelize distribution platform)


1.2.6 (2019/02)
---------------

Improvements:

- ``Apyfal.aws.AWSHost``: Fix error with non existing EBS section in block
  devices.


1.2.5 (2019/01)
---------------

Improvements:

- ``Apyfal.aws.AWSHost`` now enable ``DeleteOnTermination`` on all instance
  block devices by default. This behavior can be disabled and reset to AWS
  default using the ``delete_volumes_on_termination=False`` argument.

1.2.4 (2018/12)
---------------

Improvements:

- ``Apyfal.host.Host`` now checks instance boot using port 22 instead of 80.
- ``Apyfal.host.Host`` can now be used to start a custom instance instead of an
  predefined accelerator instance more easily.

1.2.3 (2018/10)
---------------

Backward incompatible changes:

- The ``info_dict`` argument behavior was changed. Previously, using it changed
  the returned result of methods. To avoid this, ``info_dict`` now waits a
  ``dict`` to populate with extra information. This argument is mainly intended
  to get debug or profiling information.

  Previous behavior:

    .. code-block:: python

        # This return only the processing result
        my_accel.process(dst='data.dat')

        # This return a tuple containing the processing result and the
        # information dict.
        my_accel.process(dst='data.dat', info_dict=True)

  New behavior:

    .. code-block:: python

        # This return only the processing result
        my_accel.process(dst='data.dat')

        # This still return only the processing result.
        # Information are now stored in the "info" dict.
        info = dict()
        my_accel.process(dst='data.dat', info_dict=info)

- The ``info_dict`` argument from ``AcceleratorPoolExecutor.start``,
  ``AcceleratorPoolExecutor.stop``, ``AcceleratorPoolExecutor.process_map`` and
  ``Accelerator.process_map`` methods is replaced by ``info_list`` and wait a
  ``list`` to populate instead of a ``dict``.

1.2.2 (2018/10)
---------------

Fixes:

- Improve ``stop`` behavior depending if run by user or by garbage collector or
  ``with`` exit.

1.2.1 (2018/10)
---------------

Fixes:

- Fix broken input and output data on some accelerators when using cloud
  storage.
- ``Accelerator`` and ``AcceleratorPoolExecutor`` now waits completion of all
  asynchronous tasks (From ``process_submit`` or ``process_map``) before exiting
  using ``stop``.
  This avoid the accelerator or the host to be stopped before the end of tasks
  if ``with`` statement exited or Accelerator garbage collected when tasks
  are still running.
- Improve user public IP handling.

1.2.0 (2018/10)
---------------

New features

- Apyfal now fully support HTTPS between client and host.
- Apyfal can generate self signed certificates for generated hosts, theses
  certificates are verified by the client.
- Add of ``process_map`` and ``process_submit`` methods to the Accelerator class
  to performs ``process`` call asynchronously and improve performance on batch
  of processing tasks.
- Add the ``AcceleratorPoolExecutor`` that allow to perform processing tasks
  asynchronously over a pool of multiple accelerators hosts.

General improvements

- Apyfal CLI: ``create`` is now optional if can be called without any arguments,
  This is mainly intended to use local accelerator directly on host.
- It is now possible to use private IP instead of public IP as accelerator
  default URL. See ``use_private_ip`` parameter.
- Host instance have a new ``Apyfal`` tag/metadata with ``host_name_prefix``
  value.
- Add ``boto3`` as default dependency. Actually AWS is the only provider
  ready for production and is the most commonly used. Other providers are
  available using extra setup options.
- Change logging levels to show only minimal information with INFO,
  implementation and step detail is still available using the DEBUG level.
  This allow to show more relevant information when using Apyfal with CLI or
  running Accelerators examples.
- Minimum packages versions are set in setup based on packages changelog or
  date.
- Hosts instantiation now support passing custom arguments to their libraries.
  See each specific host documentation for more information.

REST client improvements

- Uses ``requests_toolbelt`` instead of ``PycURL`` to upload big files.
  This simplify the Apyfal installation by using a far more easier to install
  library.
- Uses ``requests`` instead of Swagger codegen generated client. This
  simplify the REST client, removes some dependencies remove extra build step.
- Improves exceptions handling to add more detailed information from
  server and handle HTTP errors correctly.

Fixes:

- Fix bad text formatting in some exception messages.
- Server side logging was improved.
- Apyfal CLI: Fixed parsing of numeric parameters.
- Apyfal CLI: Fixed result dict handling.
- Fix accelerator application stopped if client ``with`` exited or garbage
  collected.
- Fix instance still running warning shown twice.
- Fix ``stop_mode`` overridden by default accelerator value.
- Fix case handling in configuration file.
- The host server now checks the Apyfal version used as client and raise a
  proper exception if not compatible.
- The host server was updated to be compatible with Apyfal starting from 1.0.0
  instead of only 1.1.0.
- Apyfal now configures FPGA properly if run locally on a host no generated by
  Apyfal client (Ex: Host instance generated manually using accelerator image)
- Apyfal now runs the local accelerator if available even if a ``host_type`` is
  provided in configuration file.
- Fix Apyfal setup fail due to missing ``ipgetter`` package on PyPI
  (This package was removed by this author without notice).

Deprecations:

- The ``optional`` extra setup option is deprecated with the replacement of
  ``PycURL``.

Pending deprecations:

- ``file_in`` and ``file_out`` argument in ``process`` method are replaced by
  ``src`` and ``dst``. ``datafile`` argument in ``start`` method is replaced by
  ``src``. This name change allow us to provides a better input and output data
  support in next version (No only files).
  The backward compatibility is kept for old arguments names but will be removed
  a future version.

1.1.0 (2018/08)
---------------

New features

- Add support for cloud storage and more in ``apyfal.storage`` package using
  ``pycosio``.
- Add Apyfal CLI, this allow to use Apyfal from outside Python.
- Apyfal can now be used locally on host (as library or CLI).
- Add ``apyfal.iter_accelerator`` function to iterates over all existing
  accelerators for a configuration.
- Add Alibaba Cloud support.
- It is now possible to pass a SSL/TLS certificates to host instance to enable
  HTTPS.

General improvements

- Move OpenStack library from ``openstacksdk`` to ``python-novaclient`` and
  ``python-neutronclient``. This adds more precision over the OpenStach Nova
  host control and reduces the overall number of required dependencies.
- Accelerator, Host and clients now have a proper string representation.
- Speed up cloud host configuration.
- Host now support the ``init_script`` argument to pass a custom bash script
  on instance startup, and the ``init_config`` argument to pass a configuration
  file.
- Apyfal now accepts path-like objects as path/URL arguments.

Configuration improvements:

- Add subsection support in configuration file (ex: ``[host.host_type]``)
- Configuration file can be loaded from ``apyfal.storage`` URL.
- Configuration class is now a ``Mapping`` instead of ``ConfigParser`` subclass.
- Configuration file is now open with UTF-8 encoding.
- Add ``host_name_prefix`` in host section, This allow to add a custom
  prefix at the start of the created host name.

Fixes:

- Importing Apyfal from an unsupported Python version now raises
  ``ImportError``.
- Host ``stop_mode`` is now correctly loaded from configuration file.
- Fix available regions list in exception message when trying to use a non
  existing region.
- Apyfal don't wait until end of timeout if instance is in ``error`` status
  during instance provisioning.
- Instance now terminates correctly if both ``instance_id`` and ``host_ip`` are
  provided.
- ``stop`` ``stop_mode`` with OpenStack now pauses instance instead of
  terminates it.
- Exception on AWS IAM policy first creation.
- Using ``start`` is not still mandatory when connecting to an already existing
  instance.

Deprecations:

- ``exit_host_on_signal`` host parameter was removed due to side effects.
  Use accelerator with the ``with`` statement to automatically terminate
  instance after run.

1.0.0 (2018/06)
---------------

Created the new *apyfal* library based on legacy *acceleratorAPI*.

Apyfal keeps all the features from acceleratorAPI but was largely improved.
Apyfal is not backward compatible with acceleratorAPI (Read the documentation
to see how update code). Future version of Apyfal will be compatible with this
one.

Features of the 1.0.0 version:

- Accelerator start, process and stop in cloud environment.
- Accelerator configuration with arguments and/or configuration file.
- Support for *generic* OpenStack host.
- Support for AWS and OVH public host.
- Complete unittest for the core or the package.
- Full Sphinx documentation.
