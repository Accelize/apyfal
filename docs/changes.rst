Changelog
=========

1.1.0 (In development)
----------------------

General improvements:

- Importing Apyfal from an unsupported Python version now raise ImportError.

Configuration improvements:

- Add subsection support in configuration file (ex: *[host.host_type]*)
- Configuration class is now a Mapping instead of ConfigParser subclass.

Fixes:

- Fix exception message when trying to use a non existing region.

1.0.0 (2018/06)
---------------

Created the new *apyfal* library based on legacy *acceleratorAPI*.

Apyfal keeps all the features from acceleratorAPI but was largely improved. Apyfal is not backward compatible with
acceleratorAPI (Read the documentation to see how update your code). Future version of Apyfal will be compatible with
this one.

Features of the 1.0.0 version:

- Accelerator start, process and stop in cloud environment.
- Accelerator configuration with arguments and/or configuration file.
- Support for *generic* OpenStack host.
- Support for AWS and OVH public host.
- Complete unittest for the core or the package.
- Full Sphinx documentation.
