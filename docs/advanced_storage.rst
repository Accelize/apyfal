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

Apyfal storage support the following extra scheme for cloud storage services: ``provider.bucket``

* ``provider`` is the provider name of the cloud storage service.
* ``bucket`` is the basic container that hold data on cloud storage.

Example:

* ``aws.my_bucket://my_file``: File with ``my_file`` key on AWS S3 ``my_bucket`` bucket.
* ``ovh.my_container://my_file``: File with ``my_file`` name on OVH Object Store ``my_container`` container.

Host scheme
~~~~~~~~~~~

``host`` scheme is like ``file`` scheme, but is only available when using Apyfal to remotely control accelerator.

In this case:

* ``file`` represent a client-side file that needs to be transferred on/from host.
* ``host`` represent a host-side file that can be used directly.

Register storage services
-------------------------

Cloud storage services use credentials to secure access and can't be accessed without them.

In Apyfal storage, theses service needs to be registered before use.
Each storage needs an unique ``storage_type`` that will be used to register it and as *scheme* to access to it with URL.

This can be done using the ``apyfal.storage.register`` function or with configuration file.

See :doc:`api_storage` for information on possibles parameters of the targeted storage.

Following examples shows the registration of ``my_provider.my_bucket`` storage type.
This storage needs following parameters to be registered: ``client_id``, ``secret_id`` & ``region``.

With register function
~~~~~~~~~~~~~~~~~~~~~~

The registration of ``my_provider.my_bucket`` storage is done like following.

.. code-block:: python

    import apyfal.storage

    # Register "my_provider.my_bucket" storage
    apyfal.storage.register(storage_type='my_provider.my_bucket',
                            client_id='my_client_id', secret_id='my_secret_id',
                            region='my_bucket_region',)

With configuration file
~~~~~~~~~~~~~~~~~~~~~~~

The registration of ``my_provider.my_bucket`` storage is done by adding a ``storage`` subsection to
the configuration file containing storage parameters.

.. code-block:: ini

    [storage.my_provider.my_bucket]
    client_id  = my_client_id
    secret_id  = my_secret_id
    region     = my_bucket_region

See :doc:`configuration` for more information on configuration file.

Basic storage operations
------------------------

Apyfal storage provides some basic files operations functions to easily manipulate storage files:

* ``apyfal.storage.open``: Open a file as file-like object. Like builtin ``open``.
* ``apyfal.storage.copy``: Copy a file between two URL. Like ``shutil.copy``.

This example shows some possible files operations:

.. code-block:: python

    import apyfal.storage

    # Open file as text for reading
    with apyfal.storage.open('my_provider.my_bucket://my_file', 'rt') as file:
        text = file.read()

    # Open file as binary for writing
    with apyfal.storage.open('my_provider.my_bucket://my_file', 'wb') as file:
        file.write(b'binary_data')

    # Copy file from storage to local file system
    copy('my_provider.my_bucket://my_file', 'my_file')

    # Copy file from local file system to storage
    copy('my_file', 'my_provider.my_bucket://my_file')

    # Copy file between storage
    copy('my_provider.my_bucket://my_file', 'my_provider.my_other_bucket://my_file')

    # Download a file from internet to storage
    copy('http://www.accelize.com/file', 'my_provider.my_bucket://my_file')

Using storage with Accelerator
------------------------------

``apyfal.Accelerator`` have native Apyfal storage URL support for files parameters:

.. code-block:: python

   import apyfal

   with apyfal.Accelerator(accelerator='my_accelerator') as myaccel:

       myaccel.start(datafile='my_provider.my_bucket://datafile')

       myaccel.process(file_in='my_provider.my_bucket://file_in',
                       file_out='my_provider.my_bucket://file_out')
