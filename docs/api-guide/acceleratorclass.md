# Class AcceleratorClass

## \_\_init\_\_(_**kwargs_)

Initialization of the Class AcceleratorClass allow to define and/or overwrite the accelerator configuration.
**Syntax**

    myaccel = AcceleratorClass(accelerator='string', config_file='string', provider='string',
	region='string', xlz_client_id='string', xlz_secret_id='string', csp_client_id='string',
	csp_secret_id='string', ssh_key='string', instance_id='string', instance_ip='string'
    )

**Parameters**

 - **accelerator**(string) -- **\[REQUIRED\]**
Name of the accelerator you want to initialize, to know the authorized list please visit https://accelstore.accelize.com
 - **config_file**(string) -- 
Path to a custom configuration file based on the accelerator.conf example.
If not set will use the file name accelerator.conf in the current folder

 - **provider**(string) -- 
If set will overwrite the value content in the configuration file
Provider value : OVH | AWS

 - **region**(string) -- 
If set will overwrite the value content in the configuration file
Check with your provider which region are using instances with FPGA.


 - **xlz_client_id**(string) -- 
If set will overwrite the value content in the configuration file
Client Id is part of the access key you can generate on https:/accelstore.accelire.com/user/applications


 - **xlz_secret_id**(string) -- 
If set will overwrite the value content in the configuration file
Secret Id is part of the access key you can generate on https:/accelstore.accelire.com/user/applications

 - **csp_client_id**(string) -- 
If set will overwrite the value content in the configuration file
Client Id is part of the access key you can generate on your CSP

 - **csp_secret_id**(string) -- 
If set will overwrite the value content in the configuration file
Secret Id is part of the access key, you can generate on your CSP

 - **ssh_key**(string) -- 
If set will overwrite the value content in the configuration file
Name of the SSH key to create or reuse.

 - **instance_id**(string) -- 
If set will overwrite the value content in the configuration file
ID of the instance, you want to reuse for the acceleratorClass

 - **instance_ip**(string) -- 
If set will overwrite the value content in the configuration file
IP address of the instance, you want to reuse for the acceleratorClass


**Return type**

AcceleratorClass object

## start(_**kwargs_)

Starts and configure an accelerator instance

**Syntax**

    myaccel.start(self, stop_mode='int', datafile='string', accelerator_parameters='string' )
   

**Parameters**

 - **stop_mode**(string) -- 
If set will overwrite the value content in the configuration file
Define the way for the CSP instance to be stopped in case of the object closure, script end or function stop call.
TERM = 0 => Instance will be deleted 
STOP = 1 => Instance will be stopped, and can be restarted at CSP level
KEEP = 2 => Instance will stay in running mode
 - **datafile**(string) -- 
Depending on the accelerator ( like for HyperFiRe) , a configuration need to be loaded before a process can be run.
In such case please define the path of the configuration file (for HyperFiRe the corpus file path).

 - **accelerator_parameters**(string) -- 
If set will overwrite the value content in the configuration file
Parameters can be forwarded to the accelerator for the configuration step using these parameters.
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
Parameters can be forwarded to the accelerator for the process step using these parameters.
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


