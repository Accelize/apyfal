
# Overview
Accelize AcceleratorAPI is a powerful and flexible toolkit for testing and operate FPGA accelerated function .

Some reasons you might want to use AcceleratorAPI :
+ The Accelize AcceleratorAPI provides an abstraction layer to use the power of FPGA devices in a cloud environment. 
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



# Configuration

Edit the accelerator.conf to provide the Accelize ID and the CSP credential in case you want the script manage the configuration and Instance start/stop.

    [general]
    
    [csp]
    #Name of your provider AWS, OVH ...
    provider = 
    #Set your CSP information
    client_id =
    secret_id =
    region = 
    project_id = 
    #Defaut CSP environement value
    instance_type =
    ssh_key = MySSHKEY
    security_group = MySecurityGROUP
    role = MyRole 
    instance_id =
    instance_ip =
    # Instance stop mode: 0=TERMINATE, 1=STOP, 2=KEEP
    stop_mode = 0
    
    [accelize]
    #Set Accelerator Access Key from your Accelize account on https://accelstore.accelize.com/user/applications
    client_id = 
    secret_id = 
    

    
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

## Simple example with  accelerator configuration

    python
    from acceleratorAPI.acceleratorAPI import *
    myaccel = AcceleratorClass(accelerator='axonerve_hyperfire')
    myaccel.start(datafile='/path/configuration/file.csv')
    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    ...
    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    myaccel.stop()

## Simple keeping CSP instance running for later use

    python
    from acceleratorAPI.acceleratorAPI import *
    myaccel = AcceleratorClass(accelerator='axonerve_hyperfire')
    myaccel.start(datafile='/path/configuration/file.csv',stop_mode=KEEP)
    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    ...
    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    myaccel.stop()

## Simple reusing a running instance

    python
    from acceleratorAPI.acceleratorAPI import *
    myaccel = AcceleratorClass(accelerator='axonerve_hyperfire',instance_ip='<Address IP>')
    myaccel.start(datafile='/path/configuration/file.csv',stop_mode=KEEP)
    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    ...
    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    myaccel.stop()

## Simple reusing a running instance already configured ( previous run didn't call the myaccel.stop())

    python
    from acceleratorAPI.acceleratorAPI import *
    myaccel = AcceleratorClass(accelerator='axonerve_hyperfire',instance_ip='<Address IP>')
    myaccel.start(stop_mode=KEEP)
    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    ...
    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    myaccel.stop()



# All the accelerated functions

Browse our web site https://accelstore.accelize.com



# Metering
Check the accelerator metering information on your [AccelStore account](https://accelstore.accelize.com/user/metering). 



# Feature Support
+ Configuration of CSP envrionement for AWS ( OVH is coming soon)
+ Remote or local execution facility
+ Simplified API



# Class AcceleratorClass

## \_\_init\_\_(_**kwargs_)

initialisation of the Class AcceleratorClass allow to define and/or overwrite the accelerator configuration.
**Syntax**

    myaccel = AcceleratorClass(accelerator='string', config_file='string', provider='string',
	region='string', xlz_client_id='string', xlz_secret_id='string', csp_client_id='string',
	csp_secret_id='string', ssh_key='string', instance_id='string', instance_ip='string'
    )

**Parameters**

 - **accelerator**(string) -- **\[REQUIRED\]**
Name of the accelerator you want to initialized, to know the autorised list please visit https://accelstore.accelize.com
 - **config_file**(string) -- 
Path to a custom configuration file based on the accelerator.conf example.
If not set will use the file name accelerator.conf in the current folder

 - **provider**(string) -- 
If set will overwrite the value content in the configuration file
Provider value : OVH | AWS

 - **region**(string) -- 
If set will overwrite the value content in the configuration file
Check with your provide witch region all using instance with FPGA.


 - **xlz_client_id**(string) -- 
If set will overwrite the value content in the configuration file
Client Id is part of the access key your can generate on https:/accelstore.accelire.com/user/applications


 - **xlz_secret_id**(string) -- 
If set will overwrite the value content in the configuration file
Secret Id is part of the access key your can generate on https:/accelstore.accelire.com/user/applications

 - **csp_client_id**(string) -- 
If set will overwrite the value content in the configuration file
Client Id is part of the access key your can generate on your CSP

 - **csp_secret_id**(string) -- 
If set will overwrite the value content in the configuration file
Secret Id is part of the access key your can generate on your CSP

 - **ssh_key**(string) -- 
If set will overwrite the value content in the configuration file
Name of the SSH key to create or reuse.

 - **instance_id**(string) -- 
If set will overwrite the value content in the configuration file
ID of the instance you want to reuse for the acceleratorClass

 - **instance_ip**(string) -- 
If set will overwrite the value content in the configuration file
IP address of the instance you want to reuse for the acceleratorClass


**Return type**

AcceleratorClass object

## start(_**kwargs_)

Starts and configure an accelerator instance

**Syntax**

    myaccel.start(self, stop_mode='int', datafile='string', accelerator_parameters='string' )
   

**Parameters**

 - **stop_mode**(string) -- 
If set will overwrite the value content in the configuration file
Define the way the instance will be defined at the object closure or script end.
TERM = 0 => Instance will be deleted 
STOP = 1 => Instance will be stopped, and can be restarted at CSP level
KEEP = 2 => Instance will stay in running mode
 - **datafile**(string) -- 
Depending of the accelerator ( like for HyperFiRe) , a configuration need to be loaded before a process can be run.
In such case please define the path of the configuration file (for HyperFiRe the corpus file path).

 - **accelerator_parameters**(string) -- 
If set will overwrite the value content in the configuration file
Parameters can be forwarded to the accelerator for the configuration step using this parameters.
Take a look accelerator documentation for more information.

**Return type**

boolean, dict


**Response example**

    (
	    True,# boolean for Succes or Failed
	    {  
	    "app":{  
		    "msg":"WARN: FPGA has been reset.\\nWARN: FPGA reset\\nRESULT: ==> SUCCESS <==\\n",  
		    "specific":{  
			    "Metering":"SUCCESSFULLY ACTIVATED",  
			    "details":{  
			    "elapsedTime":14.572049654  
			    }  
		    },  
	    "status":0  
	    },  
	    "url_instance":"http://54.38.71.77",  
	    "url_config":"http://54.38.71.77/v1.0/configuration/1/"  
	    }
    )

## process(_**kwargs_)

Process a file

**Syntax**

    myaccel.process(file_in='string',  file_out='string', accelerator_parameters='string')

   
**Parameters**

 - **file_in**(string) --  **\[REQUIRED\]**
Path to the file you want to process
 - **file_out**(string) --  **\[REQUIRED\]**
Path where you want the processed file will be stored
 - **accelerator_parameters**(string) -- 
If set will overwrite the value content in the configuration file
Parameters can be forwarded to the accelerator for the process step using this parameters.
Take a look accelerator documentation for more information.

**Return type**

boolean, dict

**Response example**

    (
	    True, # boolean for Succes or Failed
	    {  
		    "app":{  
			    "msg":"WARN: FPGA has been reset.\\nRESULT: ==> SUCCESS <==\\n",  
			    "specific":{  
				    "Metering":"SUCCESSFULLY ACTIVATED"  
			    },  
		    "status":0,  
		    "result-profiling":{  
				    "FPGA R+W bandwidth (in MB/s)":164.92035418317957,  
				    "FPGA execution time":0.030145971,  
				    "FPGA image bandwidth (in frames/s)":44.90909984466436,  
				    "Total bytes transferred":"6.6 MB",  
				    "hw_statistics":""  
				    }  
		    }  
	    }
    )
    
## stop(_**kwargs_)

Stop your accelerator session and accelerator csp instance depending of the parameters

**Syntax**

    myaccel.stop(self, stop_mode=int)

   
**Parameters**

 - **stop_mode**(string) -- 
If set will overwrite the value content in the configuration file and the one define at start time.
TERM = 0 => Instance will be deleted 
STOP = 1 => Instance will be stopped, and can be restarted at CSP level
KEEP = 2 => Instance will stay in running mode


**Return type**

boolean, dict

**Response example**

    (
	    True, # boolean for Succes or Failed
	    {  
		    "app":{  
			    "msg":"==\> SUCCESS <==\\n",  
			    "specific":{  
				    "my_message":"nothing done"  
			    },  
		    "status":0  
		    }  
	    }
    )



# Limitations

+ Max data file is limited to 30 G ( in case of usage of pycurl) or 2G using urllib 
+ Timeout will appear if request take more than 900s


## Support and enhancement requests
[Contact us](https://accelstore.accelize.com/contact-us/) if you have any support or enhancement request.
