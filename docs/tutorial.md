# Tutorial

This section show some examples of AcceleratorAPI use.

Along the way it will introduce the various components that make up AcceleratorAPI,
and give you a comprehensive understanding of how everything fits together.

All of theses examples requires that you first install the API
and create a configuration file in your current working directory or home folder:

* [Installation](installation.md)
* [Configuration File](configuration.md)

## Simple example

This tutorial will cover creating a simple accelerator instance and process a file. 

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
    myaccel.process(file_in='/path/myfile1.dat', file_out='/path/result1.dat')
    myaccel.process(file_in='/path/myfile2.dat', file_out='/path/result2.dat')
    # ... We can run any file as we need.

# The accelerator is automatically closed  on "with" exit.
# In this case, assuming the stop_mode is 1 (TERM) in configuration file,
# the previously created instance will be deleted and all the content lost.
```

## Keeping instance running

Tis tutorial will cover creating a simple accelerator instance and process a
file without stopping this CSP instance in order to be reused later.

```python
import acceleratorAPI

with acceleratorAPI.AcceleratorClass(accelerator='cast_gzip') as myaccel:

    # We can start accelerator with "KEEP" stop mode to keep instance running
    myaccel.start(stop_mode=acceleratorAPI.KEEP)

    myaccel.process(file_in='/path/myfile.dat', file_out='/path/result.dat')
    
    # We can get and store instance IP and ID for later use
    myaccel_instance_id = myaccel.instance_id
    myaccel_instance_ip = myaccel.instance_ip

# This time instance is not deleted and will stay running when accelerator is close.
```

## Reusing Accelerator instance

### With instance ID

This tutorial will cover how to reuse an instance and process a file.

```python
import acceleratorAPI

# We select the instance to use on AcceleratorCLass instantiation
# with its ID stored previously
with acceleratorAPI.AcceleratorClass(accelerator='cast_gzip',
                                     instance_id=myaccel_instance_id) as myaccel:

    myaccel.start(stop_mode=acceleratorAPI.KEEP)

    myaccel.process(file_in='/path/myfile.dat', file_out='/path/result.dat')
```

### With instance IP

This tutorial will cover how to reuse an instance and process a file using a instance IP
address and without a CSP credential.

```python
import acceleratorAPI

# We also can select the instance to use on AcceleratorCLass instantiation
# with its IP address stored previously
with acceleratorAPI.AcceleratorClass(accelerator='cast_gzip', 
                                     instance_ip=myaccel_instance_ip) as myaccel:

    myaccel.start(stop_mode=acceleratorAPI.KEEP)

    myaccel.process(file_in='/path/myfile.dat', file_out='/path/result.dat')
```

## Reusing already configured instance

This tutorial will cover reusing an instance already configured by an other client and process a file.

```python
import acceleratorAPI

with acceleratorAPI.AcceleratorClass(accelerator='cast_gzip', instance_ip='<Address IP>') as myaccel:

    myaccel.start(stop_mode=acceleratorAPI.KEEP)

    myaccel.process(file_in='/path/myfile.dat',  file_out='/path/result.dat')
```
<!-- TODO: I don't see difference from previous case ? -->