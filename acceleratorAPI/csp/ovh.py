# coding=utf-8
"""OVH"""

from acceleratorAPI.csp.generic_openstack import OpenStackClass as _OpenStackClass


class OVHClass(_OpenStackClass):
    """OVH CSP Class

    Args:
        provider (str): Cloud service provider name. Default to "OVH".
            If set will override value from configuration file.
        config (str or acceleratorAPI.configuration.Configuration): Configuration file path or instance.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        client_id (str):CSP Client ID. See with your provider to generate this value.
            If set will override value from configuration file.
        secret_id (str):CSP secret ID. See with your provider to generate this value.
            If set will override value from configuration file.
        region (str): CSP region. Check with your provider which region are using instances with FPGA.
             If set will override value from configuration file.
        instance_type:
        ssh_key (str): SSH key to use with your CSP. If set will override value from configuration file.
        security_group:
        instance_id (str): CSP Instance ID to reuse. If set will override value from configuration file.
        instance_url (str): CSP Instance URL or IP address to reuse. If set will override value from configuration file.
        project_id:
        auth_url:
        interface:
        stop_mode (int): Define the "stop_instance" method behavior. See "stop_mode"
            property for more information and possible values.
        exit_instance_on_signal (bool): If True, exit CSP instances
            on OS exit signals. This may help to not have instance still running
            if Python interpreter is not exited properly. Note: this is provided for
            convenience and does not cover all exit case like process kill and
            may not work on all OS."""

    CSP_NAME = 'OVH'
    CSP_HELP_URL = "https://horizon.cloud.ovh.net"
