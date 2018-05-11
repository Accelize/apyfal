# Welcome to Accelize AcceleratorAPI's documentation!

## Overview

Accelize AcceleratorAPI is a powerful and flexible toolkit for testing and operate FPGA accelerated function .

Some reasons you might want to use AcceleratorAPI :
+ Accelize AcceleratorAPI provides an abstraction layer to use the power of FPGA devices in a cloud environment. 
+ The configuration and the provisioning is generated for you in your CSP context (Keep your data on your Private Cloud)
+ Don't like python use one of the REST_API provided in most of the language to interact with the REST instance

### All the accelerated functions

AcceleratorAPI provides a variety of accelerated functions.

Browse our web site [AccelStore](https://accelstore.accelize.com), to discover them.

### Basic Python code example

Accelerator API is easy to use and only need few lines of codes for instantiate accelerator and CSP instance and then
 process files:

```python
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
```

### Metering

Check the accelerator metering information on your [AccelStore account](https://accelstore.accelize.com/user/metering). 

## Feature

+ Configuration of CSP environment for AWS, OVH 
+ Remote or local execution facility
+ Simplified API

### Limitations

+ Max data file is limited to 30GB (in case of usage of pycurl) or 2GB else
+ Timeout will appear if request takes more than 900s

## User Documentation

* [Installation](installation.md)
* [Configuration](configuration.md)
* [Tutorial](tutorial.md)
* [CSP guide](csp.md)

## AcceleratorAPI documentation:

* [AcceleratorAPI GitHub page](https://github.com/Accelize/acceleratorAPI)
* [acceleratorAPI](api.rst)
* [acceleratorAPI.accelerator](api_accelerator.rst)
* [acceleratorAPI.csp](api_csp.rst)
* [acceleratorAPI.configuration](api_configuration.rst)
* [acceleratorAPI.exceptions](api_exceptions.rst)
<!-- TODO: add swagger low-level api-->

## Accelize links

* [Accelize website](https://www.accelize.com)
* [AccelStore](https://accelstore.accelize.com)
* [Accelize on GitHub](https://github.com/Accelize)
* [Contact us](https://www.accelize.com/contact)

## Indices and tables

```eval_rst
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
```
