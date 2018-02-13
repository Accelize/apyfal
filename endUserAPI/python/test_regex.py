import acceleratorAPI

#accelize Credential
client_id='F20Umm8AL1d00WrWoEabFR5VTNOdRNWjcaXtWGyZ'
client_secret='B4gxyDkbuFgUWkMudnBHvRRNtayfp6Q1ZcL3fOavPNOR6IT3Hgk5o7nhP8yy7TiHfOyhLObjAlShkHMAGFo0msCLj5VlR1OLVetmzRFznX2tE0iN3dsGavMtuubKzLz9'


#CSP credential if required
#client_id_csp='blabla'
#client_secret_csp='blabla'

myacceleratorinstance = acceleratorAPI.AcceleratorClass(provider='AWS',client_id=client_id,client_secret=client_secret)


#Case without any call to CSP
ip_address='34.240.95.151'
acceleratorparameters=''
accelerator='regex' #not needed in local mode 
template_instance = {"AGFI":"agfi-016408de8fd3e6505"} #only needed on local mode 
configdict = myacceleratorinstance.start_accelerator(template_instance=template_instance,ip_address=ip_address,acceleratorparameters=acceleratorparameters,accelerator=accelerator,datafile='/home/acampos/acceleratorAPI/userapi//sample_files/regex/regex_2500w.csv')


print "-----Config dict----"
print configdict

#### Configuration Process ####
filein='/home/acampos/acceleratorAPI/userapi/sample_files/gzip/03_hugeBible.txt'
fileout='/home/acampos/acceleratorAPI/userapi/results/bible_csv.txt'
processparameter={
			"env":{
					},
			
			"app":{
				"reset": 1,
				"enable-sw-comparison": 0,
				"logging": {
					"format": 1,
					"verbosity": 1
					}
				}
		}
###################################


####  Process ####
import time
print "sleep"
#time.sleep(10)

processdict = myacceleratorinstance.process(filein=filein,
								fileout=fileout,
								processparameter=processparameter)
'''
fileout='/home/acampos/acceleratorAPI/userapi/results/bible_csv2.txt'
processdict = myacceleratorinstance.process(filein=filein,
								fileout=fileout,
								processparameter=processparameter)
fileout='/home/acampos/acceleratorAPI/userapi/results/bible_csv3.txt'								
processdict = myacceleratorinstance.process(filein=filein,
								fileout=fileout,
								processparameter=processparameter)				
'''								
#print "-----Config process----"
#print processdict

stopdict = myacceleratorinstance.stop_accelerator()

print "-----Config stopdict----" 
print stopdict