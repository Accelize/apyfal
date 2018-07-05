Storage
=======

Apyfal storage provides ability to use cloud storage services and other storage as source and target for
accelerator.

Using this feature to handle files provides some advantages:

* When using Apyfal to remotely control an accelerator, all file transfer is performed on host directly.
* Apyfal storage use simple URL like ``str`` to define files.
* Apyfal storage can also be used to handle basic copy or open operations on storage services files.

Apyfal storage URL format
-------------------------

Apyfal storage works with extended URL that support extra schemes.

Apyfal use the standard URL format ``scheme://path``.

Basic schemes
~~~~~~~~~~~~~

Apyfal storage support following basic schemes.

* ``file``: Local file on file system (``file`` scheme is assumed if no scheme provided). Example:
  ``file:///home/user/myfile`` or ``/home/user/myfile``
* ``http``/``https``: File available on HTTP/HTTPS. Example:
  ``http://www.accelize.com/file`` or ``https://www.accelize.com/file``

Cloud storage scheme
~~~~~~~~~~~~~~~~~~~~

Apyfal storage support the extra scheme for cloud storage services. In this case, the scheme is the service name or
the provider name.

Cloud storage use buckets (or containers) to hold data.
The bucket name need to be specified just before the file path in URL.

See :doc:`api_storage` for information available storage services and the scheme to use.

Example:

* ``s3://my_bucket/my_file``: File with ``my_file`` key on AWS S3 ``my_bucket`` bucket.
* ``ovh://my_container/my_file``: File with ``my_file`` name on OVH Object Store ``my_container`` container.

Host scheme
~~~~~~~~~~~

``host`` scheme is like ``file`` scheme, but is only available when using Apyfal to remotely control accelerator.

In this case:

* ``file`` represent a client-side file that needs to be transferred on/from host.
* ``host`` represent a host-side file that can be used directly.

Using storage with Accelerator
------------------------------

``apyfal.Accelerator`` have native Apyfal storage URL support for files parameters:

.. code-block:: python

   import apyfal

   with apyfal.Accelerator(accelerator='my_accelerator') as myaccel:

       myaccel.start(datafile='my_storage://datafile')

       myaccel.process(file_in='my_storage://file_in', file_out='my_storage://file_out')

Basic storage operations
------------------------

Apyfal storage provides some basic files operations functions to easily manipulate files on storage:

* ``apyfal.storage.open``: Open a file as file-like object. Like builtin ``open``.
* ``apyfal.storage.copy``: Copy a file between two URL. Like ``shutil.copy``.

This example shows some possible files operations:

.. code-block:: python

    import apyfal.storage

    # Open file as text for reading
    with apyfal.storage.open('my_storage://my_file', 'rt') as file:
        text = file.read()

    # Open file as binary for writing
    with apyfal.storage.open('my_storage://my_file', 'wb') as file:
        file.write(b'binary_data')

    # Copy file from storage to local file system
    copy('my_storage://my_file', 'my_file')

    # Copy file from local file system to storage
    copy('my_file', 'my_storage://my_file')

    # Copy file between storage
    copy('my_storage://my_file', 'my_other_storage://my_file')

    # Download a file from internet to storage
    copy('http://www.accelize.com/file', 'my_storage://my_file')

Register extra storage services
-------------------------------

Cloud storage services use credentials to secure access and can't be accessed without them.

By default, storage services that are already configured as host will be automatically registered with same parameters.

But, if parameters are different or if the storage service don't have CSP host equivalent,
the service needs to be registered before use.

Each storage needs an unique ``storage_type`` that will be used to register it and as *scheme* to access to it with URL.

This can be done using the ``apyfal.storage.register`` function or with configuration file.

See :doc:`api_storage` for information on possibles parameters of the targeted storage.

Following examples shows the registration of ``my_storage`` storage type.
This storage needs following parameters to be registered: ``client_id``, ``secret_id``.

With register function
~~~~~~~~~~~~~~~~~~~~~~

The registration of ``my_storage`` storage is done like following.

.. code-block:: python

    import apyfal.storage

    # Register "my_provider.my_bucket" storage
    apyfal.storage.register(storage_type='my_storage',
                            client_id='my_client_id', secret_id='my_secret_id')

With configuration file
~~~~~~~~~~~~~~~~~~~~~~~

The registration of ``my_storage`` storage is done by adding a ``storage`` subsection to
the configuration file containing storage parameters.

.. code-block:: ini

    [storage.my_storage]
    client_id  = my_client_id
    secret_id  = my_secret_id

See :doc:`configuration` for more information on configuration file.
