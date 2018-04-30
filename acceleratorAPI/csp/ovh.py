from acceleratorAPI.csp.openstack import OpenStackClass as _OpenStackClass


class OVHClass(_OpenStackClass):

    def start_instance_csp(self):
        if not super(OVHClass, self).start_instance_csp():
            raise Exception("Failed to create OVH instance, please refer to: https://horizon.cloud.ovh.net")
        return True
