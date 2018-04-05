# Overview
Accelize AcceleratorAPI is a powerful and flexible toolkit for testing and operate FPGA accelerated function .

Some reasons you might want to use AcceleratorAPI :
+ Accelize AcceleratorAPI provides an abstraction layer to use the power of FPGA devices in a cloud environment. 
+ The configuration and the provisioning is generated for you in your CSP context ( Keep your data on your Private Cloud)
+ Don't like python use one of the REST_API provided in most of the language to interact with the REST instance



# Requirements

+ Python 2.7
+ System packages gcc , python-pip,  python-devel, git  :
	+ On Redhat : sudo yum install gcc python-pip python-devel curl git
	+ On Ubuntu :  sudo apt-get install gcc python-pip python-dev curl git
+ Access Key (create it within your [AccelStore account](https://accelstore.accelize.com/user/application))
+ Optional pycurl python module to reach good upload performance



# Installation

Download the acceleratorAPI 

    git clone https://github.com/Accelize/acceleratorAPI.git 

Install using pip...

    sudo pip install -r acceleratorAPI/requirements.txt



# Examples

## Simple example 

    python
    from acceleratorAPI.acceleratorAPI import *
    myaccel = AcceleratorClass(accelerator='cast_gzip')
    myaccel.start()
    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    ...
    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    myaccel.stop()

## Details examples 

[1 - Standard usage](tutorial/1-simple-exemple.md)

[2 - Example keeping CSP instance running for later use](tutorial/2-keeping_instance_running.md)

[3 - Example reusing a running instance with instance_id](tutorial/3-reusing_instance_with_instance_id.md)

[4 - Example reusing a running instance with instance_ip](tutorial/4-reusing_instance_with_instance_ip.md)

[5 - Example reusing a running instance already configured](tutorial/5-reusing_instance_already_configured.md)

## Documentation

[Configuration file](api-guide/configuraton_file.md)

[AcceleratorClass details](api-guide/acceleratorclass.md)

# All the accelerated functions

Browse our web site [AccelStore](https://accelstore.accelize.com)



# Metering
Check the accelerator metering information on your [AccelStore account](https://accelstore.accelize.com/user/metering). 


# Feature Support
+ Configuration of CSP environment for AWS, OVH 
+ Remote or local execution facility
+ Simplified API


# Limitations

+ Max data file is limited to 30 G ( in case of usage of pycurl) or 2G using urllib 
+ Timeout will appear if request take more than 900s

## Troubleshooting

- [Create an AWS account](https://portal.aws.amazon.com/billing/signup?nc2=h_ct&redirect_url=https%3A%2F%2Faws.amazon.com%2Fregistration-confirmation#/start)
- [Guide to Create an AWS Access Keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)
- [Create an OVH account](https://www.ovh.com/fr/support/new_nic.xml?redirectTo=https%3A%2F%2Fwww.ovh.com%2Fmanager%2Fcloud%2F%23%2F)
- [Guide to Create an OVH Access Keys](https://docs.ovh.com/ie/en/public-cloud/configure_user_access_to_horizon/)
- [Request an adjustment to the limit of AWS EC2 F1 instances](http://aws.amazon.com/contact-us/ec2-request) you can launch (0 by default)
- [Documentation on configuration file](https://github.com/Accelize/AcceleratorAPI/docs/api-guide/configuration_file.md)
- [Documentation on python API ](https://github.com/Accelize/AcceleratorAPI/docs/api-guide/acceleratorclass.md)

## Support and enhancement requests
[Contact us](https://www.accelize.com/contact-us/) if you have any support or enhancement request.
