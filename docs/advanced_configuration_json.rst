JSON configuration files
========================

This section provides more information about parameter use than that described
in the :doc:`getting_started`.

JSON is not the recommanded way to send parameters to Apyfal

Apyfal provides JSON support to allow compatibility with JSON used with
Accelerator CLI.

The low-level accelerator API that runs on the FPGA host works with parameters
files.

These files are JSON files that have the following format:

.. code-block:: python

   {
       "app": {
           "specific":{
           # Specific parameters as key value pairs.
           }
       }
   }

See the accelerator documentation for specific parameters values.

Using ``**parameters`` argument with JSON parameters files
----------------------------------------------------------

The ``**parameters`` argument passed to the ``start`` and ``process``
methods, as described previously, can also be used to pass *JSON parameters
files*.
In this case, ``**parameters`` is used as ``parameters=``

Assuming ``parameters.json`` is the JSON parameters files:

-  To pass the ``parameters.json`` file, simply pass its path:
   ``parameters='/path/parameters.json'``.
-  To pass the ``parameters.json`` content as JSON ``str`` literal:
   ``parameters=parameters_json_content``.
-  To pass the ``dict`` equivalent of ``parameters.json``:
   ``parameters=parameters_json_content_as_dict``.

``parameters=`` can be used with classical ``**parameters`` keywords
arguments. In this case, the keywords arguments override values already
existing in the dict passed to ``parameters=``.

.. code-block:: python

   import apyfal

   with apyfal.Accelerator(accelerator='my_accelerator') as myaccel:
       myaccel.start()

       # Example of passing the parameter JSON file and keyword arguments
       myaccel.process(src='/path/myfile1.dat', dst='/path/result1.dat',
                       # Passing Path to JSON file to "parameters="
                       parameters='/path/parameters.json',
                       # Passing keywords arguments
                       parameter1='my_parameter_1', parameter2='my_parameter_2')

Using JSON parameters files with the configuration file
-------------------------------------------------------

JSON parameters files can also be defined directly in ``accelerator.conf``.
Parameters in configuration files will act as default values and will be
overridden by any parameter passed directly to the ``start`` and ``process``
methods.

See :doc:`configuration` for more information.
