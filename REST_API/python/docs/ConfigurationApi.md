# swagger_client.ConfigurationApi

All URIs are relative to *http://52.50.186.13*

Method | HTTP request | Description
------------- | ------------- | -------------
[**configuration_create**](ConfigurationApi.md#configuration_create) | **POST** /v1.0/configuration/ | /v1.0/configuration/
[**configuration_list**](ConfigurationApi.md#configuration_list) | **GET** /v1.0/configuration/ | /v1.0/configuration/
[**configuration_read**](ConfigurationApi.md#configuration_read) | **GET** /v1.0/configuration/{id}/ | /v1.0/configuration/{id}/


# **configuration_create**
> InlineResponse2001 configuration_create(parameters=parameters, datafile=datafile)

/v1.0/configuration/

Create a new configuration instance and deploy it.

### Example 
```python
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.ConfigurationApi()
parameters = 'parameters_example' # str | All parameters need for the excution in JSON format : {     \"AcceleratorParam1\":\"value1\",    \"AcceleratorParam2\":\"value2\",    \"AcceleratorParam3\":\"value3\"} (optional)
datafile = '/path/to/file.txt' # file | If needed, file to be processed by the accelerator. (optional)

try: 
    # /v1.0/configuration/
    api_response = api_instance.configuration_create(parameters=parameters, datafile=datafile)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling ConfigurationApi->configuration_create: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parameters** | **str**| All parameters need for the excution in JSON format : {     \&quot;AcceleratorParam1\&quot;:\&quot;value1\&quot;,    \&quot;AcceleratorParam2\&quot;:\&quot;value2\&quot;,    \&quot;AcceleratorParam3\&quot;:\&quot;value3\&quot;} | [optional] 
 **datafile** | **file**| If needed, file to be processed by the accelerator. | [optional] 

### Return type

[**InlineResponse2001**](InlineResponse2001.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **configuration_list**
> InlineResponse200 configuration_list(page=page)

/v1.0/configuration/

Returns a list of all accelerator configuration instance requested in the system.

### Example 
```python
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.ConfigurationApi()
page = 56 # int | A page number within the paginated result set. (optional)

try: 
    # /v1.0/configuration/
    api_response = api_instance.configuration_list(page=page)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling ConfigurationApi->configuration_list: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**| A page number within the paginated result set. | [optional] 

### Return type

[**InlineResponse200**](InlineResponse200.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **configuration_read**
> InlineResponse200Results configuration_read(id)

/v1.0/configuration/{id}/

Return the given configuration instance.

### Example 
```python
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.ConfigurationApi()
id = 56 # int | A unique integer value identifying this accelerator config.

try: 
    # /v1.0/configuration/{id}/
    api_response = api_instance.configuration_read(id)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling ConfigurationApi->configuration_read: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this accelerator config. | 

### Return type

[**InlineResponse200Results**](InlineResponse200Results.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

