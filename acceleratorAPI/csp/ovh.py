# coding=utf-8
"""OVH"""

from acceleratorAPI.csp.openstack_generic import OpenStackClass as _OpenStackClass


class OVHClass(_OpenStackClass):
    """OVH CSP Class"""
    CSP_HELP_URL = "https://horizon.cloud.ovh.net"
