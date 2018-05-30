# Configuration

*Warning: do not use your credentials on untrusted environments. You are responsible to 
secure your credentials and accelerator access.*

## What is needed to configure an accelerator ?

Two main configuration needs to be done before running an accelerator:

### Accelize account

The second part is the Accelize credential, in order to unlock the accelerator:

* [Accelize credential](https://accelstore.accelize.com/user/applications)

Your user account provides also to you metering information on your accelerator use
[AccelStore account](https://accelstore.accelize.com/user/metering). 

### CSP configuration

Accelerator needs an CSP with FPGA device that needs to be configured to run.

```eval_rst
See :doc:`getting_started` to see examples of possible cases.
```

## Accelerator configuration

This can be done with the configuration file, or can also be performed by passing directly
information to API as parameters.

### Using the configuration File 

You can use the `accelerator.conf` file to provides parameters to run your accelerator.

<!-- NOTE: configuration_file.md is dynamically generated from "accelerator.conf".
     Update directly documentation in "accelerator.conf" if needed. -->

* [Configuration file details](configuration_file.md)

This file is automatically loaded by the API if found in the current working directory or current user home
directory. A custom path can also be passed as argument to the API.

```eval_rst
:download:`accelerator.conf example file <../acceleratorAPI/accelerator.conf>`.
```

### Passing as parameters to acceleratorAPI

The use of the configuration file is not mandatory, all parameters can be passed directly to
the API as arguments. Please read API documentation for more information.

```eval_rst
See :doc:`api` for more information.
```

If both configuration file and arguments are used, arguments overrides configuration file values.
