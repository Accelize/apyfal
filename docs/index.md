# Welcome to Accelize AcceleratorAPI's documentation!

## Overview

Accelize AcceleratorAPI is a powerful and flexible toolkit for testing and operate FPGA accelerated function .

Some reasons you might want to use AcceleratorAPI :
+ Accelize AcceleratorAPI provides an abstraction layer to use the power of FPGA devices in a cloud environment. 
+ The configuration and the provisioning is generated for you in your CSP context ( Keep your data on your Private Cloud)
+ Don't like python use one of the REST_API provided in most of the language to interact with the REST instance

### All the accelerated functions

Browse our web site [AccelStore](https://accelstore.accelize.com)

### Metering

Check the accelerator metering information on your [AccelStore account](https://accelstore.accelize.com/user/metering). 

### Feature Support

+ Configuration of CSP environment for AWS, OVH 
+ Remote or local execution facility
+ Simplified API

### Limitations

+ Max data file is limited to 30 G ( in case of usage of pycurl) or 2G using urllib 
+ Timeout will appear if request take more than 900s

### User Documentation

* [Installation](installation.md)
* [Configuration file](configuration_file.md)
* [Tutorial](tutorial.md)

### API documentation:

* [acceleratorAPI](api.rst)
* [acceleratorAPI.accelerator](api_accelerator.rst)
* [acceleratorAPI.csp](api_csp.rst)
* [acceleratorAPI.configuration](api_configuration.rst)
* [acceleratorAPI.exceptions](api_exceptions.rst)
<!-- TODO: add swagger low-level api-->

## Indices and tables

```eval_rst
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
```
