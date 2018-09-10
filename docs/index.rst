Welcome to Apyfal’s Documentation!
==================================

Overview
--------

Apyfal is a powerful and flexible toolkit that enables you to use FPGA [#fpga]_
accelerated functions.”

Some reasons to use Apyfal :

+ Apyfal provides an abstraction layer to use the power of FPGA accelerated
  function in a hybrid multi-cloud environment.
+ The configuration and the provisioning is generated for the FPGA cloud
  context.
+ Apyfal can perform acceleration directly on cloud storage files.
+ Don't like Python ? Use the REST API and generate a client in any language.

**All the accelerated functions**

Apyfal provides a variety of accelerated functions.

Browse our web site `AccelStore <https://accelstore.accelize.com>`_, to
discover them.

**Basic Python code example**

Accelerator API is easy to use and only needs a few lines of codes to
instantiate an accelerator and its host and process files:

.. code-block:: python

   import apyfal

   # Choose and initialize an accelerator
   with apyfal.Accelerator(accelerator='my_accelerator') as myaccel:

       # Start and configure accelerator
       myaccel.start()

       # Process files using FPGA accelerated function
       myaccel.process(
           file_in='/path/myfile1.dat',  file_out='/path/result1.dat')
       myaccel.process(
           file_in='/path/myfile2.dat',  file_out='/path/result2.dat')

Features
--------

+ Configuration of cloud host environment
+ Remote or local execution
+ Cloud storage direct access from accelerator

**Limitations in remote mode**

+ Max input file size is limited to 30GB when using client local file.
+ Timeout will occur if a request takes more than 900s.


.. toctree::
   :maxdepth: 2
   :caption: User Documentation
   
   installation
   configuration
   getting_started
   advanced

.. toctree::
   :maxdepth: 2
   :caption: API Documentation
   
   api
   cli
   rest
   accelerator_executable

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide
   
   build
   changes
   
.. toctree::
   :maxdepth: 2
   :caption: Accelize links

   AccelStore <https://accelstore.accelize.com>
   Apyfal on GitHub <https://github.com/Accelize/apyfal>
   Apyfal on PyPI <https://pypi.org/project/apyfal>
   Accelize Website <https://www.accelize.com>
   Contact us <https://www.accelize.com/contact>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. rubric:: Footnotes

.. [#fpga] FPGA is a programmable chip that can be used as a
           function-specialized, high-performance accelerator.
