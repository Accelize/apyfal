# Configuration

## What is needed for configuring an accelerator ?

Two main configuration needs to be done before running an accelerator:

### CSP access key

The CSP configuration in order to configure the CSP environment without pain,
and when needed start a preconfigured instance with FPGA:

* [CSP guide](csp.md)

### Accelize account

The second part is the Accelize credential, in order to unlock the accelerator:

* [Accelize credential](https://accelstore.accelize.com/user/applications)

## Configuring an accelerator

This can be done with the configuration file, or can also be performed by passing directly
information to API as parameters.

### Configuration File 

You can use the `accelerator.conf` file to provides parameters to run your accelerator.

<!-- NOTE: configuration_file.md is dynamically generated from "accelerator.conf".
     Update directly documentation in "accelerator.conf" if needed. -->

* [Configuration file details](configuration_file.md)

This file is automatically loaded by the API if found in the current working directory or current user home
directory. A custom path can also be passed as argument to the API.

### Passing as parameters to acceleratorAPI

The used on configuration file is not mandatory, all parameters can be passed directly to
the API as arguments. Please read API documentation for more information.

* [API documentation](api.md)

If both configuration file and arguments are used, arguments overrides configuration file values.
