Changelog
=========

1.2.0 (2018/09)
---------------

Hosts improvements

- Speed up instance configuration.
- Move OpenStack library from ``openstacksdk`` to ``python-novaclient`` and
  ``python-neutronclient``. This adds more precision over the OpenStach Nova
  host control and reduces the overall number of required dependencies.

Storage improvements

- ``apyfal.storage`` was improved using ``pycosio``, this improves
  performance, adds support for huge cloud objects and allows
  ``apyfal.storage.open`` to provides full featured cloud objects streams.
- Apyfal now accepts path-like objects in functions that accept paths or URLs.
- ``apyfal.storage`` now supports disabling SSL/HTTPS to improve transfer
  performance at the cost of security.

Fixes:

- ``stop`` ``stop_mode`` with OpenStack now pauses instance instead of
  terminates it.

1.1.0 (2018/08)
---------------

New features

- Add support for cloud storage and more using ``apyfal.storage`` URL.
- Apyfal can now be used locally on host (like accelerator executable).

Configuration improvements:

- Add subsection support in configuration file (ex: ``[host.host_type]``)
- Configuration file can be loaded from ``apyfal.storage`` URL.
- Configuration class is now a ``Mapping`` instead of ``ConfigParser`` subclass.
- Configuration file is now open with UTF-8 encoding.
- Add ``instance_name_prefix`` in host section, This allow to add a custom prefix at the start
  of the created instance name.

Fixes:

- Importing Apyfal from an unsupported Python version now raises ``ImportError``.
- Host ``stop_mode`` is now correctly loaded from configuration file.
- Fix available regions list in exception message when trying to use a non existing region.
- Apyfal don't wait until end of timeout if instance is in ``error`` status during instance
  provisioning.
- Instance now terminates correctly if both ``instance_id`` and ``host_ip`` are provided.

Deprecations:

- ``exit_host_on_signal`` host parameter was removed due to side effects.
  Use accelerator with the ``with`` statement to automatically terminate instance after run.

1.0.0 (2018/06)
---------------

Created the new *apyfal* library based on legacy *acceleratorAPI*.

Apyfal keeps all the features from acceleratorAPI but was largely improved. Apyfal is not backward compatible with
acceleratorAPI (Read the documentation to see how update code). Future version of Apyfal will be compatible with
this one.

Features of the 1.0.0 version:

- Accelerator start, process and stop in cloud environment.
- Accelerator configuration with arguments and/or configuration file.
- Support for *generic* OpenStack host.
- Support for AWS and OVH public host.
- Complete unittest for the core or the package.
- Full Sphinx documentation.

Known Issues:
-------------

- All communication between client and host accelerator is in unencrypted plain text.
- Using ``start`` is mandatory when connecting to an already existing instance.

OpenStack only:
~~~~~~~~~~~~~~~

- Configuration file is not properly passed to the instance with ``init_config`` argument.
