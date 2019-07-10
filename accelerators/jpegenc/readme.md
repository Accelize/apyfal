![AWS](https://img.shields.io/badge/AWS-Supported-orange.svg)

# JPEG Encoder Accelerator

![JPEGENC](.resources/jpegenc.png)

This accelerator is capable of encoding in real-time video on-the-fly Bitmap images while producing standard JPEG
compressed format. It does not require any processor nor any external memory but run on FPGA instances.
The application can run at more than 40 BMP (1920x1080) processed per second.

## Features

- FPGA-accelerated JPEG encoding
- Remote or local execution facility
- Easy to use Python API

## Limitations

- Supported input format is Bitmap with 24 bits per pixels (RGB)
- Size of input bitmap:
    - Minimum size is 4 pixels
    - Maximum size is 3840 pixels x 2160 pixels
    - size must be a multiple of 4 pixels
- Inputs and outputs can't be larger than 30GB.
- See also limitations from API

## Parameters

This section describes accelerator inputs and outputs.

### Configuration parameters
No parameters required.

### Processing parameters
**Generic parameters:**
* `file_in`: Path to input BMP file.
* `file_out`: Path to output JPEG file.

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

Convert an sample BMP image to JPEG
(*[Image source](https://pixabay.com/en/switzerland-zermatt-mountains-snow-862870)*).

You can clone a repository to get examples files, then move to the cloned
directory:

```bash
git clone https://github.com/Accelize/jpegenc --depth 1
cd jpegenc
```

You need to create and configure an `accelerator.conf` file to run the example.
See "Configuration" in Apyfal documentation for more information.

You can run the example with Apyfal :
```bash
./run_example.py
```
>The result is the `"result/image.jpg"` file.



#### Using Apyfal step by step

This section explains how to run this particular accelerator.
For explanation on Apyfal and host configuration,
See "Getting Started" in Apyfal documentation.

```python
import apyfal

# 1- Create Accelerator
with apyfal.Accelerator(accelerator='alse_jpegenc') as myaccel:
    
    # 2- Configure Accelerator and its host
    #    Note: This step can take some minutes depending the configured host
    myaccel.start()
    
    # 3- Process file
    myaccel.process(file_in="samples/image.bmp", file_out="result/image.jpg")
```
>The result is the `"result/image.jpg"` file.


### Local execution on cloud instance

This section shows how to run the above example directly on host.

This example requires an host running the accelerator.

#### Creating cloud instance host using Apyfal CLI

You can easily generate a cloud instance host with Apyfal CLI

```bash
apyfal create --accelerator alse_jpegenc

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
apyfal process --file_in samples/image.bmp --file_out result/image.jpg
```
>The result is the `"result/image.jpg"` file.


#### Terminate cloud instance with Apyfal CLI

From client computer, don't forget to terminate instance you have created with
Apyfal once you have finished with it:

```bash
apyfal stop
```
