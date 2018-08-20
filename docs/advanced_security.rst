Security
========

This chapter detail security configuration in Apyfal.

Apyfal configuration file
-------------------------

The Apyfal configuration file may contain some access keys. This file needs
to be stored and exchanged with care to not compromises theses access keys.

Cloud hosts security configuration
----------------------------------

By default, Apyfal configures some cloud instances settings to improves
security.

SSH key pair
~~~~~~~~~~~~

By default, Apyfal generates an SSH key pair to give user access to the instance
using SSH. The private key file is automatically added in PEM format to the
``.ssh`` directory of your user home.

A custom key pair can be used using the ``key_pair`` argument.

An example of SSH connexion is given in :doc:`getting_started`

Security groups
~~~~~~~~~~~~~~~

Security groups are like firewalls for cloud instance and are used to allow only
a limited range of IP address to connect to the host using a limited range of
ports.

By default, Apyfal creates a security group that allows only the machine used
to generate the host instance to access it using SSH and HTTP/HTTPS
(ports ``22``, ``80`` and ``443``).

Before host instantiation, the range of ports can be modified in the
``ALLOW_PORTS`` host class attribute.

Security groups rules can also be modified using the CSP console.

Host local storage
~~~~~~~~~~~~~~~~~~

Apyfal allows to process file that are stored locally on host instance.
By default, this is limited to an unique directory for security reason.

This behavior can be change with the ``authorized_host_dirs`` parameter of
the ``security`` section in the configuration file.

See :doc:`advanced_storage` for more information.

SSL certificate
~~~~~~~~~~~~~~~

The SSL/TLS certificate allows to access host over HTTPS instead of HTTP.

A certificate needs to be passed to the instance using ``ssl_cert_crt`` and
``ssl_cert_key`` parameters.

Host side configuration file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``init_config`` parameter allows to pass Apyfal configuration file to host
instance, this can be used to configure some parameters on host.

On this parameter use, always transfer a cleaned up configuration
file to your instance to avoid the risk of compromises your access keys.

CSP specific parameters
~~~~~~~~~~~~~~~~~~~~~~~

Some CSP provides more security options, refer to each host class for more
information.

Cloud storage security configuration
------------------------------------

Some CSP that provides both computes and storage services allows to
configure host instance to access storage.
By default, Apyfal allows access to all storage to accelerator cloud instance.

But, this can be modified, refers to each host class for more information.
