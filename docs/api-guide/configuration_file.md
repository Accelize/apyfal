# Configuration File 

Edit the accelerator.conf to provide the default information to run your accelerator.

Four sections are availabled.


## CSP section
The CSP sections contain all the information related to the CSP you want to use to deploy your accelerator ( example :AWS,OVH, ..)

The value set in these sections can be overridden be the AcceleratorClass function in case it needs for your usage/


    # Name of your provider AWS, OVH ...
	provider = AWS
	# Set your CSP information
	client_id = 
	secret_id = 
	region = eu-west-1
	project_id = 
	auth_url = 
	interface = 
	# Default CSP environment value
	instance_type =
	ssh_key = MySSHKEY
	security_group = MySecurityGROUP
	role = MyRole
	instance_id =
	instance_ip =
	# Instance stop mode: 0=TERMINATE, 1=STOP, 2=KEEP
	stop_mode = 0
	    

**Parameters**

 - **provider**(string) -- 
Name of the CSP you want to target.
Value : OVH | AWS
 - **client_id**(string) -- 
The client_id you need to generate on your CSP [generate yours][dependencies/]
 - **secret_id**(string) -- 
The secret_id you need to generate on your CSP [generate yours][dependencies/]
 - **region**(string) -- 
The CSP region you need to target, check with your provider which region are using instances with FPGA.
Value : eu-west-1|us-east-1|us-west-2|GRA3
 - **project_id**(string) -- 
Value required for openstack compatible CSP ( example OVH), ignore by other CSP.
The project ID you want to use.
 - **auth_url**(string) -- 
Value required for openstack compatible CSP ( example OVH), ignore by other CSP.
The auth_url provided by the openstack configuration.
OVH value : 
 - **interface**(string) -- 
Value required for openstack compatible CSP( example OVH), ignore by other CSP.
The interface provided by the openstack configuration.
Value : public
 - **instance_type**(string) -- 
[Attention] : This value should never be used please let the API handle the right instance type.
 - **ssh_key**(string) -- 
The name of the ssh key, stored in the CSP environment, you want to create or reuse.
 - **security_group**(string) -- 
The name of the security group, visible in the CSP environment, you want to create or reuse.
 - **role**(string) -- 
Value required for AWS CSP, ignore by others CSP.
The name of the role, visible in the CSP environment, you want to create or reuse.
This role is generated to allow the instance to load the right AGFI ( FPGA bitstream)
 - **instance_id**(string) -- 
Parameter to define if you want to reuse an existing instance. In case, you have multiple client and one Accelerator instance.
 - **instance_ip**(string) -- 
Parameter to define if you want to reuse an existing instance without CSP Access Keys. In case, you have multiple client and one Accelerator instance, but client doesn't know the CSP ID. To work the instance must be up and running.
 - **stop_mode**(int) -- 
Define the way for the CSP instance to be stopped in case of the object closure, script end or function stop call.
Value : 
TERM = 0 => Instance will be deleted 
STOP = 1 => Instance will be stopped, and can be restarted at CSP level
KEEP = 2 => Instance will stay in running mode


## Accelize section

    [accelize]
    #Set Accelerator Access Keys from your Accelize account on https://accelstore.accelize.com/user/applications
    client_id = 
    secret_id = 

 **Parameters**   
 - **client_id**(string) -- 
The client_id you need to generate on [Accelize website][https://accelsotre.accelize.com/user/applications]
 - **secret_id**(string) -- 
The secret_id you need to generate on [Accelize website][https://accelsotre.accelize.com/user/applications]




## configuration section

	[configuration]
	# Default parameters for the configuration step
	parameters = {
	            "app": {
	                "reset": 0,
	                "enable-sw-comparison": 0,
	                "logging": {
	                    "format": 1,
	                    "verbosity": 2
	                }
	            }
	        }
	        
 - **parameters**(string) -- 
Parameters can be forwarded to the accelerator for the configuration step using this parameter.
Take a look accelerator documentation for more information.

## process section

	[process]
	# Default parameters for the process step
	parameters = {
	            "app": {
	                "reset": 0,
	                "enable-sw-comparison": 0,
	                "logging": {
	                    "format": 1,
	                    "verbosity": 2
	                }
	            }
	        }
 - **parameters**(string) -- 
Parameters can be forwarded to the accelerator for the process step using this parameter.
Take a look accelerator documentation for more information.
