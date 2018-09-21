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

A custom security group can be used using the ``security_group`` argument.

Before host instantiation, the range of ports can be modified in the
``ALLOW_PORTS`` host class attribute.

Security groups rules can also be modified using the CSP console.

Host local storage
~~~~~~~~~~~~~~~~~~

Apyfal allows to process file that are stored locally on host instance.
By default, this is limited to an unique directory for security reason.

This behavior can be change with the ``authorized_host_dirs`` parameter of
the ``security`` section in the host side configuration file.

See :doc:`advanced_storage` for more information.

SSL certificate
~~~~~~~~~~~~~~~

The SSL/TLS certificate allows to access host over HTTPS instead of HTTP.

Certificate selection and generation
____________________________________

Apyfal allows to define a certificate to use, or to generates automatically a
certificate.

Using an user defined certificate:
    A certificate can to be passed to the host creation using
    ``ssl_cert_crt`` and ``ssl_cert_key`` parameters.

Generating a self signed wildcard certificate:
    ``ssl_cert_generate`` parameter can be used to generate a self signed
    certificate.

    If ``ssl_cert_generate`` is used without ``ssl_cert_crt`` and
    ``ssl_cert_key``, a generic certificate is generated in the ``.ssh``
    directory of the user home. If the generic certificate exists, it is reused
    and not regenerated.

Certificate verification
________________________

The certificate needs to be verified to provides security.

Classical DNS host name based certificate
    This kind of certificate is verified as usual using a Certificate Authority.

Self signed wildcard certificate
    Certificate Authority cannot verify this kind of certificate., but Apyfal
    can verify the connexion against a specified certificate.

    Once a client have the ``ssl_cert_crt`` specified or a generic certificate
    is found in the ``.ssh`` directory, connections are verified using this
    certificate.

    Host name is not verified when using a wildcard certificate.

Disabling HTTPS and using HTTP
______________________________

If ``ssl_cert_crt`` is specified or if a generic certificate is found in the
``.ssh`` directory, HTTPS is enabled.

``ssl_cert_crt`` can be set to ``False`` to disable HTTPS.

Usage scenarios
_______________

Host has a DNS host name:
    Use a Certificate Authority to generate a certificate for this DNS host name
    and define ``ssl_cert_crt`` and ``ssl_cert_key`` to this certificate files.

    This is the most secure and recommended way, but it require to bind hosts IP
    address to an host name.

Host has no DNS host name and is shared between its creator and other users:
    Creator generate a self signed certificate by defining ``ssl_cert_crt``,
    ``ssl_cert_key`` and ``ssl_cert_generate`` and share the public certificate
    file with other users. Others user set ``ssl_cert_crt`` to this certificate
    file to enable connection verification with it.

Host has no DNS host name and is used only by its creator for a single session:
    Creator generate a generic self signed certificate by defining only
    ``ssl_cert_generate``.

Using HTTP to improve data transfer speed between client and host.
    Set ``ssl_cert_generate`` to ``False`` to be sure using HTTP instead of
    HTTPS.

    Note that with this option, transferred data and Accelize access keys
    are publicly visible to anyone on the network.

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
