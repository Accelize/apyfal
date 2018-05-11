# Tutorial

All of theses examples requires that you first install the API
and create a configuration file in your current working directory or home folder.

* [Installation](installation.md)
* [Configuration File](configuration_file.md)

## Simple example

This tutorial will cover creating a simple accelerator instance and process a file. 
Along the way it will introduce the various components that make up AcceleratorAPI,
and give you a comprehensive understanding of how everything fits together.

Okay, we're ready to get coding, let's scripting accelerator with Python:

```python
# Import the accelerator module.
import acceleratorAPI

# Choose an accelerator to use.
with acceleratorAPI.AcceleratorClass(accelerator='cast_gzip') as myaccel:
    # Start the accelerator.
    # In this case a new CSP instance will be provisioned using the CSP
    # credential provided in the configuration file. 
    myaccel.start()

    # Okay, we're ready to roll.
    # Define witch file you want to process and where they should be stored.
    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    # ...
    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')

# The accelerator automatically stop on "with" exit.
# In this case, assuming the stop_mode is 1,
# the previously created instance will be deleted and all the content lost.
```

## Keeping instance running

Tis tutorial will cover creating a simple accelerator instance and process a
file without stopping this CSP instance in order to be reused later.
Along the way it will introduce the various components that make up AcceleratorAPI,
and give you a comprehensive understanding of how everything fits together.

Okay, we're ready to get coding.
To get started, let's open a python shell to work with.

    python
    
Once that's done we can import our module.
    
    from acceleratorAPI.acceleratorAPI import *
    
Choose an accelerator to use.
    
    myaccel = AcceleratorClass(accelerator='cast_gzip')
    
Start the accelerator. In this case a new CSP instance will be provisioned using
the CSP credential provided in the configuration file and the module will let him up and running. 

    myaccel.start(datafile='/path/configuration/file.csv',stop_mode=KEEP)
    
Okay, we're ready to roll. Define witch file you want to process and where they should be stored.

    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    ...
    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    
Stop the accelerator. In this case , the previously created instance will stay running.

    myaccel.stop()

## Reusing Accelerator instance

### With instance ID

This tutorial will cover how to reuse an instance and process a file.
Along the way it will introduce the various components that make up AcceleratorAPI,
and give you a comprehensive understanding of how everything fits together.

Okay, we're ready to get coding.
To get started, let's open a python shell to work with.

    python
    
Once that's done we can import our module.
    
    from acceleratorAPI.acceleratorAPI import *
    
Choose an accelerator to use.
    
    myaccel = AcceleratorClass(accelerator='cast_gzip',instance_id='<Instance ID>')
        
Start the accelerator. In this case will reuse a CSP instance. 

    myaccel.start(datafile='/path/configuration/file.csv',stop_mode=KEEP)
    
Okay, we're ready to roll. Define witch file you want to process and where they should be stored.

    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    ...
    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    
Stop the accelerator. In this case , the previously created instance will stay running.

    myaccel.stop()

### With instance IP

This tutorial will cover how to reuse an instance and process a file using a instance IP
address and without a CSP credential.  Along the way it will introduce the various components
that make up AcceleratorAPI, and give you a comprehensive understanding of how everything fits together.

Okay, we're ready to get coding.
To get started, let's open a python shell to work with.

    python
    
Once that's done we can import our module.
    
    from acceleratorAPI.acceleratorAPI import *
    
Choose an accelerator to use.
    
    myaccel = AcceleratorClass(accelerator='cast_gzip',instance_ip='<Address IP>')
    
    
Start the accelerator. In this case will reuse a CSP instance. 

    myaccel.start(datafile='/path/configuration/file.csv',stop_mode=KEEP)
    
Okay, we're ready to roll. Define witch file you want to process and where they should be stored.

    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    ...
    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    
Stop the accelerator. In this case , the previously created instance will stay running.

    myaccel.stop()

## Reusing already configured instance

This tutorial will cover reusing an instance already configured by an other client and process a file.
Along the way it will introduce the various components that make up AcceleratorAPI,
and give you a comprehensive understanding of how everything fits together.

Okay, we're ready to get coding.
To get started, let's open a python shell to work with.

    python
    
Once that's done we can import our module.
    
    from acceleratorAPI.acceleratorAPI import *
    
Choose an accelerator to use.
    
    myaccel = AcceleratorClass(accelerator='cast_gzip',instance_ip='<Address IP>')
    
    
Start the accelerator. In this case will reuse a CSP instance. 

    myaccel.start(stop_mode=KEEP)
    
Okay, we're ready to roll. Define witch file you want to process and where they should be stored.

    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    ...
    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
    
Stop the accelerator. In this case , the previously created instance will stay running.

    myaccel.stop()
