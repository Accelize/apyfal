# coding=utf-8
"""Alibaba Cloud OSS"""

from apyfal.storage import _Storage


class OSSStorage(_Storage):
    """Alibaba Cloud OSS Bucket

    Storage URL: "oss://BucketName/ObjectKey"

    Args:
        storage_type (str): Cloud service provider name. Default to "Alibaba".
        config (apyfal.configuration.Configuration, path-like object or file-like object):
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration
            values.
            Path-like object can be path, URL or cloud object URL.
        unsecure (bool): if True (default) disables TLS/SSL/HTTPS for transfer.
            This can improve performance, but makes connection insecure.
        client_id (str): Alibaba Access Key ID.
        secret_id (str): Alibaba Secret Access Key.
        region (str): Alibaba region.
        storage_parameters (dict): Extra "storage_parameters".
            See "pycosio.mount".
    """
    #: Provider name
    NAME = 'Alibaba'

    #: Storage name
    STORAGE_NAME = 'oss'

    #: AWS Website
    DOC_URL = "https://www.alibabacloud.com"

    #: Storage parameters template
    STORAGE_PARAMETERS = {
        'access_key_id': 'self._client_id',
        'access_key_secret': 'self._secret_id',
        'endpoint': 'self._endpoint'}

    def __init__(self, region=None, unsecure=None, **kwargs):
        _Storage.__init__(self, unsecure=unsecure, **kwargs)

        # TODO: Get STS role credentials
        # https://www.alibabacloud.com/help/doc-detail/49122.htm?spm=a2c63.p38356.a3.12.4152453c6RckQP#concept_j5w_pj4_xdb

        # Read configuration
        self._endpoint = 'http%s://oss-%s.aliyuncs.com' % (
            '' if unsecure else 's', self._from_config('region', region))
