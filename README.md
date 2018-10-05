[![Linux Build Status](https://travis-ci.org/Accelize/apyfal.svg?branch=master)](https://travis-ci.org/Accelize/apyfal)
[![Windows Build status](https://ci.appveyor.com/api/projects/status/87jgroaoo2iddlco/branch/master?svg=true)](https://ci.appveyor.com/project/accelize-application/apyfal/branch/master)
[![codecov](https://codecov.io/gh/Accelize/apyfal/branch/master/graph/badge.svg)](https://codecov.io/gh/Accelize/apyfal)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/b67c9a1cf17e443290b0191a7970c3d1)](https://www.codacy.com/app/Accelize/apyfal?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Accelize/apyfal&amp;utm_campaign=Badge_Grade)
[![Documentation Status](https://readthedocs.org/projects/apyfal/badge/?version=latest)](https://apyfal.readthedocs.io/en/latest/?badge=latest)

# Overview

Apyfal is a powerful and flexible toolkit to operate FPGA <sup>[1](#fpga)</sup> accelerated function .

Some reasons to use Apyfal :

+ Apyfal provides an abstraction layer to use the power of FPGA accelerated function in a hybrid
  multi-cloud environment.
+ The configuration and the provisioning is generated for the FPGA cloud context.
+ Apyfal can perform acceleration directly on cloud storage files.
+ Don't like Python ? Use the REST API and generate a client in any language.

## All the accelerated functions

Apyfal provides a variety of accelerated functions.

Browse our web site [AccelStore](https://accelstore.accelize.com), to discover them.

## Basic Python code example

Accelerator API is easy to use and only need few lines of codes for instantiate accelerator and its host and then
 process files:

```python
import apyfal

# Choose and initialize an accelerator
with apyfal.Accelerator(accelerator='my_accelerator') as myaccel:

    # Start and configure accelerator
    myaccel.start()

    # Process data using FPGA accelerated function
    myaccel.process(src='/path/myfile1.dat',  dst='/path/result1.dat')
    myaccel.process(src='/path/myfile2.dat',  dst='/path/result2.dat')
```

# Documentation

For more information on Apyfal, please read the [documentation](https://apyfal.readthedocs.io).

# Installation

Installation is made with PIP. Some installation options are available depending the host to use (See 
documentation for more information).

The full package can be installed using:
```bash
pip install apyfal[all]
```

# Support and enhancement requests
[Contact us](https://www.accelize.com/contact) for any support or enhancement request.


# Footnotes

<a name="fpga">1</a>: FPGA is a programmable chip that can be used as function specialized high performance accelerator.
