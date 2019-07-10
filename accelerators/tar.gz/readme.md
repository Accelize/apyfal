![AWS](https://img.shields.io/badge/AWS-Supported-orange.svg)

# TAR.GZ Accelerator

![TAR.GZ](.resources/targzip.png)

The TAR.GZ accelerator provides an hardware-acceleration for TAR, GZIP or TAR+GZIP compression.

It is up to 25X faster than CPU compression.

## Features

- TAR operation
- GZIP operation
- TAR + GZIP operation
- Per-use monetization and specific to chosen operation
- Remote or local execution facility
- Easy to use Python API

## Limitations

- The TAR.GZ accelerator does not support password-protected archive generation
- The TAR operation does not support POSIX 1003.1-1990 extra fields
- Inputs and outputs can't be larger than 30GB.
- See also limitations from API

## Parameters

This section describes accelerator inputs and outputs.

### Configuration parameters
**Specific parameters:**
* `mode`: Select the accelerator mode. Possibles values:
    * `1`: GZIP only mode
    * `2`: TAR only mode
    * `3`: TAR + GZIP mode

### Processing parameters
**Generic parameters:**
* `file_in`: Path to input file.
* `file_out`: Path to output file (Required only with `endOfTx=1` if `mode` is `2` or `3`).

**Specific parameters:**
* `endOfTx`: Finalize TAR (Required only if `mode` is `2` or `3`). Must be set to `1` with last input file.
`file_out` must be specified if this argument is `1`. Possibles values:
    * `1`: Finalize
    * `0`: Don't finalize
* `startOfTx`: Initialize TAR (Required only if `mode` is `2` or `3`). Must be set to `1` with first input file. Possibles values:
    * `1`: Initialize
    * `0`: Don't Initialize

### Processing output
Processing output is file defined by `file_out` parameter.

## Getting started

The Apyfal Python library is required.

Apyfal is installed using PIP. 

You can install the full package with all options using:

```bash
pip install apyfal[all]
```

### Using Accelerator with Apyfal

#### Running example

This example show how make a TAR.GZ file containing 3 files.

You can clone a repository to get examples files, then move to the cloned
directory:

```bash
git clone https://github.com/Accelize/tar.gz --depth 1
cd tar.gz
```

You need to create and configure an `accelerator.conf` file to run the example.
See "Configuration" in Apyfal documentation for more information.

You can run the example with Apyfal :
```bash
./run_example.py
```
>The result is the `"results/out.tar.gz"` file.



#### Using Apyfal step by step

This section explains how to run this particular accelerator.
For explanation on Apyfal and host configuration,
See "Getting Started" in Apyfal documentation.

```python
import apyfal

# 1- Create Accelerator
with apyfal.Accelerator(accelerator='aclz_tgz') as myaccel:
    
    # 2- Configure Accelerator and its host
    #    Note: This step can take some minutes depending the configured host
    #    Select the mode TAR + GZIP.
    myaccel.start(mode=3)
    
    # 3- Process file
    #    Initialize TAR and add first file.
    myaccel.process(file_in="samples/sample_1_1MB.txt", startOfTx=1, endOfTx=0)
    #    Add the second file.
    myaccel.process(file_in="samples/sample_1_1MB.txt", startOfTx=0, endOfTx=0)
    #    Add the last file, finalize the TAR and save it.
    myaccel.process(file_in="samples/sample_1_1MB.txt", file_out="results/out.tar.gz", startOfTx=0, endOfTx=1)
```
>The result is the `"results/out.tar.gz"` file.


### Local execution on cloud instance

This section shows how to run the above example directly on host.

This example requires an host running the accelerator.

#### Creating cloud instance host using Apyfal CLI

You can easily generate a cloud instance host with Apyfal CLI

```bash
apyfal create --accelerator aclz_tgz

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

Select the mode TAR + GZIP.
```bash
apyfal start --mode 3
```

#### Process with accelerator

Then, process with accelerator.

Initialize TAR and add first file.
```bash
apyfal process --file_in samples/sample_1_1MB.txt --startOfTx 1 --endOfTx 0
```

Add the second file.
```bash
apyfal process --file_in samples/sample_1_1MB.txt --startOfTx 0 --endOfTx 0
```

Add the last file, finalize the TAR and save it.
```bash
apyfal process --file_in samples/sample_1_1MB.txt --file_out results/out.tar.gz --startOfTx 0 --endOfTx 1
```
>The result is the `"results/out.tar.gz"` file.


#### Terminate cloud instance with Apyfal CLI

From client computer, don't forget to terminate instance you have created with
Apyfal once you have finished with it:

```bash
apyfal stop
```
