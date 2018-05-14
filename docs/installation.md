# Installation

## Requirements

Supported Python versions: 2.7, 3.4, 3.5, 3.6

Required Python Packages:

+ `Request`, `urllib3`, `six`, `certifi`, `python-dateutil`
+ `pip` and `setuptools`: For package installation
+ `boto3` (Optional): Required for AWS.
+ `openstack` (Optional): Required for OVH.
+ `pycurl` (Optional): Improve upload performance and file size limit.

Credentials:

+ Accelize Access Key (create it within your [AccelStore account](https://accelstore.accelize.com/user/application))
+ Cloud Service Provider Access Key (See your CSP documentation for more information).

```eval_rst
See :doc:`configuration` for more information.
```

### Linux
On Linux, some extra packages are required:

+ `python-pip` package is required.

+ Depending on the Python version, CSP targeted and wheel format availability, a C/C++ compiler may also be required 
for install dependencies. In this case, `gcc` & `python-devel` are required.

+ `pycurl` need the `curl` package.

Install is done with the package manager of your Linux distribution, example:

+ On Redhat: 
```
sudo yum install gcc python-pip python-devel curl
```
+ On Debian or Ubuntu:
```
sudo apt-get install gcc python-pip python-dev curl
```

### Windows

Depending on the Python version, CSP targeted and wheel format availability, a C/C++ compiler may also be required for 
install dependencies.

+ see [Windows Compilers on Python documentation](https://wiki.python.org/moin/WindowsCompilers)

## Setup

Installation is done using PIP:
```
pip install acceleratorAPI
```

All mandatory dependencies are automatically installed. It is possible to install also optional dependencies passing 
following setuptools extras:

* `all`: Install all extras.
* `AWS`: Requirements for AWS.
* `OVH`: Requirements for OVH.
* `optional`: other optional requirements (ex `pycurl`).

Example for installing the `all` extra:
```
pip install acceleratorAPI[all]
```
