# coding=utf-8
"""OVH"""

from acceleratorAPI.csp.openstack_generic import OpenStackClass as _OpenStackClass


class OVHClass(_OpenStackClass):
    """OVH CSP Class"""
    # TODO: Help in exception but generic
    #def start_instance(self):
    #    if not super(OVHClass, self).start_instance():
    #        raise Exception("Failed to create OVH instance, please refer to: https://horizon.cloud.ovh.net")
    #    return True
