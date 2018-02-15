# Overview
Accelize AcceleratorAPI is a powerful and flexible toolkit for testing and operate FPGA accelerated function .

Some reasons you might want to use AcceleratorAPI :
+ The Accelize AcceleratorAPI provides an abstraction layer to use the power of FPGA devices in a cloud environment. 
+ The configuration and the provisioning is generated for you in your CSP context ( Keep your data on your Private Cloud)
+ Don't like python use one of the REST_API provided in most of the language to interact with the REST instance


## Requirements
+ Python 2.7
+ Access Key (create it within your [AccelStore account](https://accelstore.accelize.com/user/application))
+ Optional pycurl python module to reach good upload performance


## Installation
Download the acceleratorAPI 

    git clone https://github.com/Accelize/acceleratorAPI.git 

Install using pip...

    sudo pip install -r acceleratorAPI/endUserAPI/python/requirements.txt


## All the accelerated functions

Browse our web site https://accelstore.accelize.com

## Configuration
Edit the accelerator.conf to provide the Accelize ID and the CSP credential in case you want the script manage the Configuration and Instance start/stop.

    [accelize]
    #Create your free account and access keys  on https://accelstore.accelize.com/user/applications
    client_id =
    secret_id =
    
    [csp]
    #Create AccessKey from your CSP Provider
    client_id =
    secret_id =

## Simple Demo

    myacceleratorinstance = acceleratorAPI.AcceleratorClass(provider='AWS', stop_instance=True)
    myacceleratorinstance.start_accelerator(start_instance=True,  accelerator='accelize_gzip')
    myacceleratorinstance.process(file_in='myfile',  file_out='result')
    myacceleratorinstance.stop_accelerator()
    
## Metering
Check the accelerator metering information on your [AccelStore account](https://accelstore.accelize.com/user/metering). 

## Feature Support
+ Configuration of CSP envrionement for AWS ( OVH is coming soon)
+ Remote or local execution facility
+ Simplified API

## Limitations
+ Max data file is limited to 30 G ( in case of usage of pycurl) or 2G using urllib 
+ Timeout will appear if request take more than 900s


## Expert mode: local execution on the server
TODO
/!\ Use AMI private IP, not public IP

## Support and enhancement requests
[Contact us](https://accelstore.accelize.com/contact-us/) if you have any support or enhancement request.
