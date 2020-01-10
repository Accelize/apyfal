:warning: **This project is cancelled and unmaintened**

### Repository content

This repository is available as archive and contain:

* The Apyfal client side utility.
* Accelerators that where powered by Apyfal in the `accelerators` directory.


### Overview

Apyfal is a powerful and flexible toolkit to operate FPGA fpga accelerated
function .

Some reasons to use Apyfal :

+ Apyfal provides an abstraction layer to use the power of FPGA accelerated
  function in a hybrid multi-cloud environment.
+ The configuration and the provisioning is generated for the FPGA cloud
  context.
+ Apyfal can perform acceleration directly on cloud storage files.
+ Don't like Python ? Use the REST API and generate a client in any language.


#### Basic Python code example

Apyfal is easy to use and only need few lines of codes for instantiate
accelerator and its host and then process files:

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
