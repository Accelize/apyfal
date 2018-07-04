JSON configuration files
========================

This section extend parameter use documentation from :doc:`getting_started`.

The low level accelerator API that run on FPGA host works with parameters files.

Theses files are JSON that have the following format:

.. code-block:: python

   {
       "app": {
           "specific":{
           # Specific parameters as key, values pairs.
           }
       }
   }

Read the accelerator documentation to see possibles specific parameters
values.

Using ``**parameters`` argument with JSON parameters files
----------------------------------------------------------

The ``**parameters`` argument passed to ``start`` and ``process``
methods can also be used to pass *JSON parameters files* like defined
previously. In this case, ``**parameters`` is used as ``parameters=``

Assuming ``parameters.json`` is the JSON parameters files:

-  To pass the ``parameters.json`` file, simply pass its path:
   ``parameters='/path/parameters.json'``.
-  To pass the ``parameters.json`` content as JSON ``str`` literal:
   ``parameters=parameters_json_content``.
-  To pass the ``dict`` equivalent of ``parameters.json``:
   ``parameters=parameters_json_content_as_dict``.

``parameters=`` can be used with classical ``**parameters`` keywords
arguments, in this case keywords arguments overrides values already
existing in in dict passed to ``parameters=``.

.. code-block:: python

   import apyfal

   with apyfal.Accelerator(accelerator='my_accelerator') as myaccel:
       myaccel.start()

       # Example passing the parameter JSON file and keywords arguments at same time
       myaccel.process(file_in='/path/myfile1.dat', file_out='/path/result1.dat',
                       # Passing Path to JSON file to "parameters="
                       parameters='/path/parameters.json',
                       # Passing keywords arguments
                       parameter1='my_parameter_1', parameter2='my_parameter_2')

Using JSON parameters files with the configuration file
-------------------------------------------------------

JSON parameters files can also be defined directly in
``accelerator.conf``. Parameters in configuration files will act as
default values and will be overridden by any parameter passed directly
to ``start`` and ``process`` methods.

See :doc:`configuration` for more information.
