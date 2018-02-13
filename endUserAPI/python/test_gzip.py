import acceleratorAPI
import logging
console = logging.StreamHandler()
LOG_FMT = "%(asctime)s - %(levelname)-8s: %(name)-20s, %(funcName)-28s, %(lineno)-4d: %(message)s"
#LOG_FMT = "%(name)-20s, %(funcName)-28s, %(lineno)-4d: %(message)s"

LOG_DATE_FMT = "%d %H:%M:%S"

console.setFormatter(logging.Formatter(LOG_FMT))
logging.getLogger().addHandler(console)
logging.getLogger('acceleratorAPI').setLevel(logging.DEBUG)
#accelize Credential
client_id='F20Umm8AL1d00WrWoEabFR5VTNOdRNWjcaXtWGyZ'
client_secret='B4gxyDkbuFgUWkMudnBHvRRNtayfp6Q1ZcL3fOavPNOR6IT3Hgk5o7nhP8yy7TiHfOyhLObjAlShkHMAGFo0msCLj5VlR1OLVetmzRFznX2tE0iN3dsGavMtuubKzLz9'


#CSP credential if required
#client_id_csp='blabla'
#client_secret_csp='blabla'

myacceleratorinstance = acceleratorAPI.AcceleratorClass(provider='AWS',client_id=client_id,client_secret=client_secret)


#Case without any call to CSP
ip_address='54.154.31.31'
accelerator_parameters=''
datafile=''
accelerator='gzip' #not needed in local mode 
template_instance = {"AGFI":"agfi-056da3074124b7467"} #only needed on local mode 
configdict = myacceleratorinstance.start_accelerator(template_instance=template_instance,ip_address=ip_address,accelerator_parameters=accelerator_parameters,accelerator=accelerator,datafile=datafile)


print "-----Config dict----"
print configdict

#### Configuration Process ####
filein='/home/acampos/acceleratorAPI/userapi/sample_files/gzip/03_hugeBible.txt'
fileout='/home/acampos/acceleratorAPI/userapi/results/03_hugeBible.gz'
processparameter={
			"env":{
					},
			
			"app":{
				"reset": 1,
				"enable-sw-comparison": 0,
				"logging": {
					"format": 1,
					"verbosity": 4 
					}
				}
		}
###################################


####  Process ####

processdict = myacceleratorinstance.process(filein=filein,
								fileout=fileout,
								processparameter=processparameter)

#print processdict

#stopdict = myacceleratorinstance.stop_accelerator()

#print "-----Config stopdict----" 
#print stopdict

