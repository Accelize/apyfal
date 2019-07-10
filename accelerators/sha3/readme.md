![AWS](https://img.shields.io/badge/AWS-Supported-orange.svg)

# SHA3 and SHAKE Application

This application is capable of hashing any file.

## Features

- Support: SHA3-224, SHA3-256, SHA3-384, SHA3-512, SHAKE-128, SHAKE-256
- Remote or local execution facility
- Easy to use Python API

## Limitations

- Performance of this accelerator is between 1x and 6x faster than CPU depending on the SHA3 algorithm and the size of the file to hash. Larger is the file, better is the acceleration factor.
- Inputs and outputs can't be larger than 30GB.
- See also limitations from API

## Parameters

This section describes accelerator inputs and outputs.

### Configuration parameters
No parameters required.

### Processing parameters
**Generic parameters:**
* `file_in`: Path to file to hash.

**Specific parameters:**
* `type`: Hashing algorithm. Possibles values:
    * `sha3-224`: SHA3-224 algorithm
    * `sha3-256`: SHA3-256 algorithm
    * `sha3-384`: SHA3-384 algorithm
    * `sha3-512`: SHA3-512 algorithm
    * `shake-128`: SHAKE-128 algorithm
    * `shake-256`: SHAKE-256 algorithm
* `length`: Length of the expected digest in SHAKE algorithm.

### Processing output
Result is the hashing result.

**Specific outputs:**
* `digest`: SHA3/SHAKE digest.

## Getting started

The Apyfal Python library is required.

Apyfal is installed using PIP. 

You can install the full package with all options using:

```bash
pip install apyfal[all]
```

### Using Accelerator with Apyfal

#### Running example

This example computes the sha3-224 for the run_example.py file.
Make sure the accelerator.conf file has been completed before running the script.

You can clone a repository to get examples files, then move to the cloned
directory:

```bash
git clone https://github.com/Accelize/sha3 --depth 1
cd sha3
```

You need to create and configure an `accelerator.conf` file to run the example.
See "Configuration" in Apyfal documentation for more information.

You can run the example with Apyfal :
```bash
./run_example.py
```

- To benchmark this solution with the standard openssl C++ library, use this command: python run_benchmark.py
  This script is hashing differente sizes of message from 1KB to 1GB for all the sha3 algorithms. Both It will produce a results.csv file that can be imported in a spreadsheet application.
- To run this solution with the NIST test vectors, use this command: python run_nist_test.py

#### Using Apyfal step by step

This section explains how to run this particular accelerator.
For explanation on Apyfal and host configuration,
See "Getting Started" in Apyfal documentation.

```python
import apyfal

# 1- Create Accelerator
with apyfal.Accelerator(accelerator='silex_sha3') as myaccel:
    
    # 2- Configure Accelerator and its host
    #    Note: This step can take some minutes depending the configured host
    myaccel.start()
    
    # 3- Process file
    myaccel.process()
```


### Local execution on cloud instance

This section shows how to run the above example directly on host.

This example requires an host running the accelerator.

#### Creating cloud instance host using Apyfal CLI

You can easily generate a cloud instance host with Apyfal CLI

```bash
apyfal create --accelerator silex_sha3

apyfal start
```

And then connect to it with SSH (``key_pair`` and ``ip_address`` values are
printed by Apyfal CLI on start):

```bash
ssh -Yt -i ~/.ssh/${key_pair}.pem centos@${ip_address}
```

It is now possible to continue using Apyfal as Python library or as CLI, 
The example next steps will use the CLI.

#### Accelerator configuration

First, initialize the Apyfal CLI.
```bash
apyfal create
```

Like previously, start the accelerator:

```bash
apyfal start
```

#### Process with accelerator

Then, process with accelerator.

```bash
apyfal process
```


#### Terminate cloud instance with Apyfal CLI

From client computer, don't forget to terminate instance you have created with
Apyfal once you have finished with it:

```bash
apyfal stop
```
