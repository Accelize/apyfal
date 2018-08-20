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
        host_ip (str): IP or URL address of an already existing AWS EC2 instance
            to use. If not specified, create a new instance.
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
        ssl_cert_crt (path-like object or file-like object):
            Public ".crt" key file of the SSL certificate used to provides
            HTTPS.
        ssl_cert_key (path-like object or file-like object):
            Private ".key" key file of the SSL certificate used to provides
            HTTPS.
    """
    #: Provider name to use
    NAME = 'OVH'

    #: OVH Website
    DOC_URL = "https://horizon.cloud.ovh.net"

    #: OVH OpenStack auth-URL
    OPENSTACK_AUTH_URL = 'https://auth.cloud.ovh.net/'
