Storage
=======

Apyfal storage provides the ability to use cloud storage services and other
storage as a source and target for an accelerator.

Using this feature to handle files provides some advantages:

* When using Apyfal to remotely control an accelerator, all file transfers are
  performed on the host directly.
* Apyfal storage uses simple URLs like ``str`` to define files.
* Apyfal storage can also be used to handle basic copy or open operations on
  storage services files.

Apyfal storage URL format
-------------------------

Apyfal storage works with extended URLs that support extra schemes.

Apyfal use the standard URL format ``scheme://path``.

Basic schemes
~~~~~~~~~~~~~

Apyfal storage supports the following basic schemes.

* ``file``: Local file on file system (``file`` scheme is assumed if no scheme
  provided). Example:
  ``file:///home/user/myfile`` or ``/home/user/myfile``
* ``http``/``https``: File available on HTTP/HTTPS. Example:
  ``http://www.accelize.com/file`` or ``https://www.accelize.com/file``

Cloud storage schemes
~~~~~~~~~~~~~~~~~~~~~

Apyfal storage supports extra schemes for cloud storage services. In this case,
the scheme is the service name or the provider name.

Cloud storage use buckets (or containers) to hold data.
The bucket name needs to be specified just before the file path in URL.

See :doc:`api_storage` for information available storage services and the scheme
to use.

Example:

* ``s3://my_bucket/my_file``: File with ``my_file`` key on AWS S3 ``my_bucket``
  bucket.
* ``ovh://my_container/my_file``: File with ``my_file`` name on OVH Object Store
  ``my_container`` container.

The ``host`` scheme
~~~~~~~~~~~~~~~~~~~

The ``host`` scheme is similar to the ``file`` scheme, but is only available
when using Apyfal to control the accelerator remotely.

In this case:

* ``file`` represents a client-side file that needs to be transferred to/from
  host.
* ``host`` represents a host-side file that can be used directly.

For security reason, ``host`` scheme is restricted to a whitelisted list of
directories on host.
This list can be modified, host side, using the ``authorized_host_dirs``
of the ``security`` section in the configuration file.
The only default authorized directory is ``~/shared``.

Using storage with Accelerator
------------------------------

``apyfal.Accelerator`` has native Apyfal storage URL support for file
parameters:

.. code-block:: python

   import apyfal

   with apyfal.Accelerator(accelerator='my_accelerator') as myaccel:

       myaccel.start(datafile='my_storage://datafile')

       myaccel.process(file_in='my_storage://file_in',
                       file_out='my_storage://file_out')

Basic storage operations
------------------------

Apyfal storage provides some basic file operation functions to easily manipulate
storage files:

* ``apyfal.storage.open``: Open a file as file-like object. Like builtin
  ``open``.
* ``apyfal.storage.copy``: Copy a file between two URL. Like ``shutil.copy``.

The following example shows some possible file operations:

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

Mount extra storage services
----------------------------

Cloud storage services use a login and password to secure access and can’t be
accessed without them.

By default, storage services that are already configured as host are
automatically mounted with same parameters.

But, in other cases, these services need to be mounted before use.
Each storage needs a unique ``storage_type`` that will be used to mount it
and to access it with a URL.

This can be done using the ``apyfal.storage.mount`` function or with the
configuration file.

See :doc:`api_storage` for information on possible parameters for the targeted
storage.

The following examples show the registration of the ``my_storage`` storage type.
This storage needs the following parameters to be mounted:
``client_id`` and ``secret_id``.

With mount function
~~~~~~~~~~~~~~~~~~~

The registration of ``my_storage`` storage is performed as follows.

.. code-block:: python

    import apyfal.storage

    # Mount "my_provider.my_bucket" storage
    apyfal.storage.mount(storage_type='my_storage',
                         client_id='my_client_id', secret_id='my_secret_id')

With configuration file
~~~~~~~~~~~~~~~~~~~~~~~

The registration of ``my_storage`` storage is performed by adding a ``storage``
subsection to the configuration file containing storage parameters.

.. code-block:: ini

    [storage.my_storage]
    client_id  = my_client_id
    secret_id  = my_secret_id

See :doc:`configuration` for more information on the configuration file.
