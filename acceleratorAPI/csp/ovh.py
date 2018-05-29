# coding=utf-8
"""OVH"""

from acceleratorAPI.csp.generic_openstack import OpenStackClass as _OpenStackClass


class OVHClass(_OpenStackClass):
    """OVH CSP Class

    Args:
        provider (str): Cloud service provider name. Default to "OVH".
        config (str or acceleratorAPI.configuration.Configuration): Configuration file path or instance.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        client_id (str): OVH Access Key ID.
        secret_id (str): OVH Secret Access Key.
        region (str): OVH region. Needs a region supporting instances with FPGA devices.
        instance_type (str): OVH Flavor. Default defined by accelerator.
        ssh_key (str): OVH Key pair. Default to 'MySSHKey'.
        security_group: OVH Security group. Default to 'MySecurityGroup'.
        instance_id (str): Instance ID of an already existing OVH nova instance to use.
            If not specified, create a new instance.
        instance_url (str): IP address of an already existing OVH nova instance to use.
            If not specified, create a new instance.
        project_id (str): OVH Project
        interface (str): OVH interface (default to 'public')
        stop_mode (str or int): Define the "stop_instance" method behavior. Default to 'term'.
            See "stop_mode" property for more information and possible values.
        exit_instance_on_signal (bool): If True, exit instance
            on OS exit signals. This may help to not have instance still running
            if Python interpreter is not exited properly. Note: this is provided for
            convenience and does not cover all exit case like process kill and
            may not work on all OS.
    """
    #: Provider name to use
    CSP_NAME = 'OVH'

    #: OVH Website
    CSP_HELP_URL = "https://horizon.cloud.ovh.net"

    #: OVH OpenStack auth-URL
    OPENSTACK_AUTH_URL = 'https://auth.cloud.ovh.net/'
