# coding=utf-8
"""OVH Object Store"""

from apyfal.storage.openstack import SwiftStorage as _SwiftStorage


class OVHStorage(_SwiftStorage):
    """OVH Object Store

    Storage URL:
        - "https://Region.cloud.ovh.net/v1/ProjectID/Container/Object"
        - "ovh://Container/Object"

    Args:
        storage_type (str): Cloud service provider name. Default to "OVH".
        config (str or apyfal.configuration.Configuration or file-like object):
            Can be Configuration instance, apyfal.storage URL, paths, file-like
            object.
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration
            values.
        client_id (str): OVH Access Key ID.
        secret_id (str): OVH Secret Access Key.
        region (str): OVH region.
        project_id (str): OVH Project
    """
    #: Provider name
    NAME = 'OVH'

    #: Storage name
    STORAGE_NAME = 'swift'

    #: OVH Website
    DOC_URL = "https://horizon.cloud.ovh.net"

    #: OVH OpenStack auth-URL
    OPENSTACK_AUTH_URL = 'https://auth.cloud.ovh.net/'

    #: Extra URL prefix (For shorter URL)
    EXTRA_URL_PREFIX = 'ovh://'
