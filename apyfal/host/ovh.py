# coding=utf-8
"""OVH"""

from apyfal.host.openstack import OpenStackHost as _OpenStackHost


class OVHHost(_OpenStackHost):
    """OVH CSP

    Args:
        host_type (str): Cloud service provider name. Default to "OVH".
        config (apyfal.configuration.Configuration, path-like object or file-like object):
            If not set, will search it in current working directory,
            in current user "home" folder. If none found, will use default
            configuration values.
            Path-like object can be path, URL or cloud object URL.
        client_id (str): OVH Access Key ID.
        secret_id (str): OVH Secret Access Key.
        region (str): OVH region. Needs a region supporting instances with FPGA
            devices.
        instance_type (str): OVH Flavor. Default defined by accelerator.
        key_pair (str): OVH Key pair. Default to 'AccelizeOVHKeyPair'.
        security_group: OVH Security group. Default to 'AccelizeSecurityGroup'.
        instance_id (str): Instance ID of an already existing OVH nova instance
            to use. If not specified, create a new instance.
        host_name_prefix (str): Prefix to add to instance name.
            Also used as value of the "Apyfal" metadata.
        host_ip (str): IP or URL address of an already existing AWS EC2 instance
            to use. If not specified, create a new instance.
        use_private_ip (bool): If True, on new instances,
            uses private IP instead of public IP as default host IP.
        project_id (str): OVH Project
        stop_mode (str or int): Define the "stop" method behavior.
            Default to 'term' if new instance, or 'keep' if already existing
            instance. See "stop_mode" property for more information and possible
            values.
        init_config (bool or apyfal.configuration.Configuration, path-like object or file-like object):
            Configuration file to pass to instance on
            initialization. This configuration file will be used as default for
            host side accelerator.
            If value is True, use 'config' configuration.
            If value is a configuration use this configuration.
            If value is None or False, don't passe any configuration file
            (This is default behavior).
        init_script (path-like object or file-like object): A bash script
            to execute on instance startup.
        ssl_cert_crt (path-like object or file-like object or bool):
            Public ".crt" key file of the SSL ssl_cert_key used to provides
            HTTPS.
            If not specified, uses already generated certificate if found.
            If False, disable HTTPS.
        ssl_cert_key (path-like object or file-like object):
            Private ".key" key file of the SSL ssl_cert_key used to provides
            HTTPS.
            If not specified, uses already generated key if found.
        ssl_cert_generate (bool): Generate a self signed ssl_cert_key.
            The ssl_cert_key and private key will be stored in files specified
            by "ssl_cert_crt" and "ssl_cert_key" (Or temporary certificates if
            not specified). Note that this ssl_cert_key is only safe if other
            client verify it by providing "ssl_cert_crt". No Certificate
            Authority are available to trust this ssl_cert_key.
        nova_client_kwargs (dict): Extra keyword arguments for
            novaclient.client.Client.
        nova_client_create_server_kwargs (dict): Extra Keyword arguments for
            novaclient.servers.ServerManager.create.
        neutron_client_kwargs (dict): Extra keyword arguments for
            neutronclient.client.Client. By default, neutron client
            inherits from nova client session.
    """
    #: Provider name to use
    NAME = 'OVH'

    #: OVH Website
    DOC_URL = "https://horizon.cloud.ovh.net"

    #: OVH OpenStack auth-URL
    OPENSTACK_AUTH_URL = 'https://auth.cloud.ovh.net/'
