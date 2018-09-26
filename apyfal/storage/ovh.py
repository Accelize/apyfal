# coding=utf-8
"""OVH Object Store"""

from apyfal.storage.openstack import SwiftStorage as _SwiftStorage


class OVHStorage(_SwiftStorage):
    """OVH Object Store

    Storage URL:
        - "https://storage.Region.cloud.ovh.net/v1/AUTH_ProjectID/Container/Object"
        - "ovh://Container/Object"

    Args:
        storage_type (str): Cloud service provider name. Default to "OVH".
        config (apyfal.configuration.Configuration, path-like object or file-like object):
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration
            values.
            Path-like object can be path, URL or cloud object URL.
        ssl (bool): If True (default) allow SSL for transfer,
            else tries to disable it. Disabling SSL can improve performance,
            but makes connection insecure.
        client_id (str): OVH Access Key ID.
        secret_id (str): OVH Secret Access Key.
        region (str): OVH region.
        project_id (str): OVH Project
        storage_parameters (dict): Extra "storage_parameters".
            See "pycosio.mount".
    """
    #: Provider name
    NAME = 'OVH'

    #: Storage name
    STORAGE_NAME = 'swift'

    #: OVH Website
    DOC_URL = "https://horizon.cloud.ovh.net"

    #: OVH OpenStack auth-URL
    OPENSTACK_AUTH_URL = 'https://auth.cloud.ovh.net/'

    #: Extra root (For shorter URL)
    EXTRA_ROOT = 'ovh://'
