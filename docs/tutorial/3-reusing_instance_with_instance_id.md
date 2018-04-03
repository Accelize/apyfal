# Tutorial 3 : ReUsing Accelerator instance

## Introduction

This tutorial will cover creating a simple accelerator instance and process a file.  Along the way it will introduce the various components that make up AcceleratorAPI, and give you a comprehensive understanding of how everything fits together.

## Setting up a new environment


System packages are needed to compile some openstack packages  gcc , python-pip,  python-devel, git  :
	+ On Redhat : 
	
    sudo yum install gcc python-pip python-devel curl git
    
   + On Ubuntu : 
    
    sudo apt-get install gcc python-pip python-dev curl git

Before we do anything else we'll create a new virtual environment, using [virtualenv].  This will make sure our package configuration is kept nicely isolated from any other projects we're working on.

    virtualenv env
    source env/bin/activate


Now that we're inside a virtualenv environment, we can install our package requirements.

    git clone https://github.com/Accelize/acceleratorAPI.git 
    sudo pip install -r acceleratorAPI/requirements.txt

**Note:** To exit the virtualenv environment at any time, just type `deactivate`.  For more information see the [virtualenv documentation][virtualenv].


## Configuration of the accelerator file
2 main configuration needs to be done before running an accelerator.

The CSP configuration in order to configure the CSP envrionnement without pain , and when needed start a preconfigured instance with FPGA.

The second part is the Accelize credential, in order to unlock the accelerator.

To help you in these actions, you can check the meaning of each [configuration paramters](repo/api-guide/configuration_file.md)

Or use one of the preconfigured csp , where you only need to add the [CSP credential](repo/depdendencies/) and [Accelize credential](https://accelstore.accelize.com/user/applications)



[Accelize/acceleratorAPI](repo) 



## Getting started

Okay, we're ready to get coding.
To get started, let's open a python shell to work with.

    python
    
Once that's done we can import our module.
    
    from acceleratorAPI.acceleratorAPI import *
    
Choose an accelerator to use.
    
    myaccel = AcceleratorClass(accelerator='cast_gzip',instance_i='<Instance ID>')
        
Start the accelerator. In this case will reuse a CSP instance. 

    myaccel.start(datafile='/path/configuration/file.csv',stop_mode=KEEP)
    
Okay, we're ready to roll. Define witch file you want to process and where they should be stored.

    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    ...
    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    
Stop the accelerator. In this case , the previously created instance will stay running.

    myaccel.stop()
        
---

**Note**: The code for this tutorial is available in the [Accelize/acceleratorAPI](repo) repository on GitHub.  .

---