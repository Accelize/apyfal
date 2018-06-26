# coding=utf-8
"""OVH Object Store"""

from apyfal.storage.openstack import OpenStackStorage as _OpenStackStorage


class OVHStorage(_OpenStackStorage):
    """OVH Object Store

    apyfal.storage URL: "OVH.ContainerName://ObjectName"

    Args:
        storage_type (str): Cloud service provider name. Default to "OVH".
        config (str or apyfal.configuration.Configuration): Configuration file path or instance.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration values.
        client_id (str): OVH Access Key ID.
        secret_id (str): OVH Secret Access Key.
        region (str): OVH region.
        bucket_name (str): Name on the container on OVH.
        project_id (str): OVH Project
    """
    #: Provider name to use
    NAME = 'OVH'

    #: OVH Website
    DOC_URL = "https://horizon.cloud.ovh.net"

    #: OVH OpenStack auth-URL
    OPENSTACK_AUTH_URL = 'https://auth.cloud.ovh.net/'

    #: OVH OpenStack interface
    OPENSTACK_INTERFACE = 'public'
