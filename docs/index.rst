Welcome to Accelize AcceleratorAPI's documentation!
===================================================

Overview
--------

Accelize AcceleratorAPI is a powerful and flexible toolkit to operate FPGA [#fpga]_ accelerated function .

Some reasons you might want to use AcceleratorAPI :

+ Accelize AcceleratorAPI provides an abstraction layer to use the power of FPGA accelerated function in a hybrid
  multi-cloud environment.
+ The configuration and the provisioning is generated for you in your FPGA cloud context.
+ Don't like Python ? Use the REST API and generate a client in the language of your choice.

**All the accelerated functions**

AcceleratorAPI provides a variety of accelerated functions.

Browse our web site `AccelStore <https://accelstore.accelize.com>`_, to discover them.

**Basic Python code example**

Accelerator API is easy to use and only need few lines of codes for instantiate accelerator and CSP instance and then
process files:

.. code-block:: python

   import acceleratorAPI

   # Choose an accelerator
   with acceleratorAPI.AcceleratorClass(accelerator='cast_gzip') as myaccel:

       # Start and configure accelerator CSP instance
       myaccel.start()

       # Process files using FPGA
       myaccel.process(file_in='/path/myfile1.dat',  file_out='/path/result1.dat')
       myaccel.process(file_in='/path/myfile2.dat',  file_out='/path/result2.dat')
       # ... Process any number of file as needed

   # By default, CSP instance is automatically close on "with" exit.


Feature
-------

+ Configuration of CSP environment for AWS, OVH 
+ Remote or local execution facility
+ Simplified API

**Limitations**

+ Max data file is limited to 30GB (in case of usage of pycurl) or 2GB else
+ Timeout will appear if request takes more than 900s


.. toctree::
   :maxdepth: 2
   :caption: User Documentation
   
   installation.md
   configuration.md
   getting_started.md

.. toctree::
   :maxdepth: 2
   :caption: API Documentation
   
   api.md
   rest.md

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide
   
   build.md
   changes.md
   
.. toctree::
   :maxdepth: 2
   :caption: Accelize links 

   Website <https://www.accelize.com>
   AccelStore <https://accelstore.accelize.com>
   GitHub <https://github.com/Accelize>
   Contact us <https://www.accelize.com/contact>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. rubric:: Footnotes

.. [#fpga] FPGA is a programmable chip that can be used as function specialized high performance accelerator.
