[![Linux Build Status](https://travis-ci.org/Accelize/acceleratorAPI.svg?branch=master)](https://travis-ci.org/Accelize/acceleratorAPI)
[![Windows Build status](https://ci.appveyor.com/api/projects/status/qo4tfua8spb2jt42/branch/master?svg=true)](https://ci.appveyor.com/project/xlz-jgoutin/acceleratorapi/branch/master)
[![Coverage Status](https://coveralls.io/repos/github/Accelize/acceleratorAPI/badge.svg?branch=master)](https://coveralls.io/github/Accelize/acceleratorAPI?branch=master)
[![Documentation Status](https://readthedocs.org/projects/acceleratorapi/badge/?version=latest)](https://acceleratorapi.readthedocs.io/en/latest/?badge=latest)

# Overview

Accelize AcceleratorAPI is a powerful and flexible toolkit to operate FPGA <sup>[1](#fpga)</sup> accelerated function .

Some reasons you might want to use AcceleratorAPI :

+ Accelize AcceleratorAPI provides an abstraction layer to use the power of FPGA accelerated function in a hybrid
  multi-cloud environment.
+ The configuration and the provisioning is generated for you in your FPGA cloud context.
+ Don't like Python ? Use the REST API and generate a client in the language of your choice.

## All the accelerated functions

AcceleratorAPI provides a variety of accelerated functions.

Browse our web site [AccelStore](https://accelstore.accelize.com), to discover them.

## Basic Python code example

Accelerator API is easy to use and only need few lines of codes for instantiate accelerator and CSP instance and then
 process files:

```python
import acceleratorAPI

# Choose and initialize an accelerator
with acceleratorAPI.AcceleratorClass(accelerator='my_accelerator') as myaccel:

   # Start and configure accelerator
   myaccel.start()

   # Process files using FPGA accelerated function
   myaccel.process(file_in='/path/myfile1.dat',  file_out='/path/result1.dat')
   myaccel.process(file_in='/path/myfile2.dat',  file_out='/path/result2.dat')
```

# Documentation

For more information acceleratorAPI, please read the [documentation](https://acceleratorapi.readthedocs.io).

# Installation

Installation is made with PIP. Some installation options are available depending the CSP you want to use (See 
documentation for more information).

You can install the full package with all options using:
```bash
pip install acceleratorAPI[all]
```

# Support and enhancement requests
[Contact us](https://www.accelize.com/contact) if you have any support or enhancement request.


# Footnotes

<a name="fpga">1</a>: FPGA is a programmable chip that can be used as function specialized high performance accelerator.
