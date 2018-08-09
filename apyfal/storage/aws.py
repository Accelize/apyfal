# coding=utf-8
"""Amazon Web Services S3"""

from apyfal.storage import _Storage


class S3Storage(_Storage):
    """AWS S3 Bucket

    Storage URL: s3://BucketName/ObjectKey

    Args:
        storage_type (str): Cloud service provider name. Default to "AWS".
        config (apyfal.configuration.Configuration, path-like object or
            file-like object):
            If not set, will search it in current working directory, in current
            user "home" folder. If none found, will use default configuration
            values.
            Path-like object can be path, URL or cloud object URL.
        unsecure (bool): if True (default) disables TLS/SSL/HTTPS for transfer.
            This can improve performance, but makes connection insecure.
        client_id (str): AWS Access Key ID.
        secret_id (str): AWS Secret Access Key.
    """
    #: Provider name
    NAME = 'AWS'

    #: Storage name
    STORAGE_NAME = 's3'

    #: AWS Website
    DOC_URL = "https://aws.amazon.com"

    #: Storage parameters template
    STORAGE_PARAMETERS = {'client': {
        'aws_access_key_id': 'self._client_id',
        'aws_secret_access_key': 'self._secret_id'}}
