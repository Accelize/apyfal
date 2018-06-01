# Getting Started

This section explains how to use AcceleratorAPI with Python to run accelerators.

All of theses examples requires that you first install the AcceleratorAPI
and get configuration requirements like at least your Accelize credentials (`accelize_client_id` and `accelize_secret_id`
parameters in following examples).

```eval_rst
See :doc:`installation` and :doc:`configuration` for more information.
```

You also needs the name (`accelerator` parameter in following example) of the accelerator you want to use.

See [AccelStore](https://accelstore.accelize.com) for more information.

>Examples below uses configuration as arguments to be more explicit, but you can also set them with configuration file.

>For testing and examples, it is possible to enable acceleratorAPI logger to see more details on running steps:
>
>```python
>import acceleratorAPI
>acceleratorAPI.get_logger(True)
>```

## Running an accelerator on a cloud instance

This tutorial will cover creating a simple accelerator instance and process a file using a Cloud Service 
Provider (*CSP*). 

Parameters required in this case may depends on the CSP used, but it need always at least:

* `provider`: CSP name
* `region`: CSP region name, need a region that support FPGA instance.
* `client_id` and `secret_id`: CSP credentials

See your CSP documentation to know how obtains theses values.

```python
# Import the accelerator module.
import acceleratorAPI

# Choose an accelerator to use and configure it.
with acceleratorAPI.AcceleratorClass(
        # Accelerator parameters
        accelerator='my_accelerator',
        # CSP parameters
        provider='my_provider', region='my_region', 
        client_id='my_client_id', secret_id='my_secret_id',
        # Accelize parameters
        accelize_client_id='my_accelize_client_id',
        accelize_secret_id='my_accelize_secret_id') as myaccel:

    # Start the accelerator:
    # In this case a new CSP instance will be provisioned credential passed to 
    # AcceleratorClass
    # Note: This step can take some minutes depending your CSP
    myaccel.start()

    # Process data:
    # Define witch file you want to process and where they should be stored.
    myaccel.process(file_in='/path/myfile1.dat', file_out='/path/result1.dat')
    myaccel.process(file_in='/path/myfile2.dat', file_out='/path/result2.dat')
    # ... It is possible to process any number of file

# The accelerator is automatically closed  on "with" exit.
# In this case, the default stop_mode ('term') is used:
# the previously created instance will be deleted and all its content lost.
```

### Keeping instance running

Starting instance take long time, so it may be a good idea to keeping it running for reusing it later.

This is done with the `stop_mode` parameter.

Depending your CSP, note that you will pay until your instance is alive.

```python
import acceleratorAPI

with acceleratorAPI.AcceleratorClass(
        accelerator='my_accelerator',
        provider='my_provider', region='my_region', 
        client_id='my_client_id', secret_id='my_secret_id',
        accelize_client_id='my_accelize_client_id',
        accelize_secret_id='my_accelize_secret_id') as myaccel:

    # We can start accelerator with "keep" stop mode to keep instance running
    myaccel.start(stop_mode='keep')

    myaccel.process(file_in='/path/myfile.dat', file_out='/path/result.dat')
    
    # We can get and store instance IP and ID for later use
    my_instance_id = myaccel.csp.instance_id
    my_instance_ip = myaccel.csp.public_ip

# This time instance is not deleted and will stay running when accelerator is close.
```

### Reusing existing instance

#### With instance ID and full instance access

With `instance_id`, depending your CSP, your can reuse an already existing instance without providing
`client_id` and `secret_id`.

An accelerator started with `instance_id` keep control on this instance an can stop it.

```python
import acceleratorAPI

# We select the instance to use on AcceleratorClass instantiation
# with its ID stored previously
with acceleratorAPI.AcceleratorClass(
        accelerator='my_accelerator',
        provider='my_provider', region='my_region',
        # Use 'instance_id' and removed 'client_id' and 'secret_id'
        instance_id='my_instance_id',
        accelize_client_id='my_accelize_client_id',
        accelize_secret_id='my_accelize_secret_id') as myaccel:

    myaccel.start()

    myaccel.process(file_in='/path/myfile.dat', file_out='/path/result.dat')
```

#### With instance IP with accelerator only access

With `instance_ip`, your can reuse an already existing instance ID without providing any CSP information.

An accelerator started with `instance_ip` have no control over this instance and can't stop it.

```python
import acceleratorAPI

# We also can select the instance to use on AcceleratorClass instantiation
# with its IP address stored previously
with acceleratorAPI.AcceleratorClass(
        accelerator='my_accelerator', 
        # Use 'instance_ip' and removed 'client_id' and 'secret_id'
        instance_ip='my_instance_ip',
        accelize_client_id='my_accelize_client_id',
        accelize_secret_id='my_accelize_secret_id') as myaccel:

    myaccel.start()

    myaccel.process(file_in='/path/myfile.dat', file_out='/path/result.dat')
```

## Configuring accelerators

Some accelerators requires to be configured to run. Accelerator configuration is done with `start` and `process`
methods.

### Start configuration

Configuration passed to `start` applies to every `process` calls that follows.

It is possible to call `start` a new time to change configuration.

The `start` configuration is divided in two parts:

* The `datafile` argument: Some accelerator may require a data file to run, this argument is simply the path to 
this file. Read the accelerator documentation to see the file format to use.
* The `**parameters` argument(s): Parameters are *specific configuration parameters*, they are passed as keyword 
arguments. Read the accelerator documentation to see possible *specific configuration parameters*.
Any value passed to this argument overrides default configuration values.

```python
import acceleratorAPI

with acceleratorAPI.AcceleratorClass(accelerator='my_accelerator') as myaccel:

    # The parameters are passed to "start" to configure accelerator, parameters are:
    # - datafile: The path to "datafile1.dat" file.
    # - parameter1, parameter2: Keywords parameters passed to "**parameters" arguments.
    myaccel.start(datafile='/path/datafile1.dat', parameter1='my_parameter_1', parameter2='my_parameter_2')
    
    # Every "process" call after start use the previously specified configuration to perform processing 
    myaccel.process(file_in='/path/myfile1.dat', file_out='/path/result1.dat')
    myaccel.process(file_in='/path/myfile2.dat', file_out='/path/result2.dat') 
    # ...

    # It is possible to re-call "start" method with other parameters to change configuration
    myaccel.start(datafile='/path/datafile2.dat')
    
    # Following "process" will use the new configuration.
    myaccel.process(file_in='/path/myfile3.dat', file_out='/path/result3.dat')
    # ...
```

### Process configuration

Configuration passed to `process` applies only to this `process` call.

The `process` method accept the following arguments:

* `file_in`: Path to the input file. Read the accelerator documentation to see if input file is needed.
* `file_out`: Path to the output file. Read the accelerator documentation to see if an output file is needed.
* The `**parameters` argument(s): Parameters are *specific process parameters*, they are passed as keyword 
arguments. Read the accelerator documentation to see possible *specific process parameters*. Any value passed to this
argument overrides default configuration values.

```python
import acceleratorAPI

with acceleratorAPI.AcceleratorClass(accelerator='my_accelerator') as myaccel:

    myaccel.start()
    
    # The parameters are passed to "process" to configure it, parameters are:
    # - parameter1, parameter2: Keywords parameters passed to "**parameters" arguments. 
    myaccel.process(file_in='/path/myfile1.dat', file_out='/path/result1.dat',
                    parameter1='my_parameter_1', parameter2='my_parameter_2')
```

### Configuration and Process parameters dict/JSON

TODO:

#### Using "**parameters" argument with dict or JSON

The `**parameters` argument passed to `start` and `process` methods can also be used to pass
*parameters dict/JSON* like defined previously. In this case, `**parameters` is used as `parameters=`

Assuming `parameter_dict` is the parameters `dict`:

* To pass the `parameter_dict` directly as `dict`: `parameters=parameter_dict`.
* To pass the `parameter_dict` as JSON `str` literal: `parameters=parameter_dict_json_dump`.
* To pass the `parameter_dict` as JSON file, in this case simply pass its path:
`parameters='/path/parameter_dict.json'`.

`parameters=` can be used with classical `**parameters` keywords arguments, in this case keywords arguments overrides
values already existing in in dict passed to `parameters=`.

```python
import acceleratorAPI

with acceleratorAPI.AcceleratorClass(accelerator='my_accelerator') as myaccel:

    myaccel.start()
    
    # Example passing the JSON file of "parameter_dict" + keywords arguments
    myaccel.process(file_in='/path/myfile1.dat', file_out='/path/result1.dat',
                    # Passing Path to JSON file of "parameter_dict" to "parameters="
                    parameters='/path/parameter_dict.json',
                    # Passing keywords arguments like previously
                    parameter1='my_parameter_1', parameter2='my_parameter_2')
```
