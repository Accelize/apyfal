# swagger_client.ProcessApi

All URIs are relative to *http://52.50.186.13*

Method | HTTP request | Description
------------- | ------------- | -------------
[**process_create**](ProcessApi.md#process_create) | **POST** /v1.0/process/ | /v1.0/process/
[**process_delete**](ProcessApi.md#process_delete) | **DELETE** /v1.0/process/{id}/ | /v1.0/process/{id}/
[**process_list**](ProcessApi.md#process_list) | **GET** /v1.0/process/ | /v1.0/process/
[**process_read**](ProcessApi.md#process_read) | **GET** /v1.0/process/{id}/ | /v1.0/process/{id}/


# **process_create**
> InlineResponse2003 process_create(configuration, parameters=parameters, datafile=datafile)

/v1.0/process/

Create a new process instance.

### Example 
```python
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.ProcessApi()
configuration = 'configuration_example' # str | Id of the configuration to use for this process
parameters = 'parameters_example' # str | All parameters need for the excution in JSON format : {     \"AcceleratorParam1\":\"value1\",    \"AcceleratorParam2\":\"value2\",    \"AcceleratorParam3\":\"value3\"} (optional)
datafile = '/path/to/file.txt' # file | If needed, file to be processed by the accelerator. (optional)

try: 
    # /v1.0/process/
    api_response = api_instance.process_create(configuration, parameters=parameters, datafile=datafile)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling ProcessApi->process_create: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **configuration** | **str**| Id of the configuration to use for this process | 
 **parameters** | **str**| All parameters need for the excution in JSON format : {     \&quot;AcceleratorParam1\&quot;:\&quot;value1\&quot;,    \&quot;AcceleratorParam2\&quot;:\&quot;value2\&quot;,    \&quot;AcceleratorParam3\&quot;:\&quot;value3\&quot;} | [optional] 
 **datafile** | **file**| If needed, file to be processed by the accelerator. | [optional] 

### Return type

[**InlineResponse2003**](InlineResponse2003.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **process_delete**
> process_delete(id)

/v1.0/process/{id}/

### Example 
```python
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.ProcessApi()
id = 56 # int | A unique integer value identifying this process execution.

try: 
    # /v1.0/process/{id}/
    api_instance.process_delete(id)
except ApiException as e:
    print "Exception when calling ProcessApi->process_delete: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this process execution. | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **process_list**
> InlineResponse2002 process_list(page=page)

/v1.0/process/

Returns a list of all process instance requested in the system.

### Example 
```python
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.ProcessApi()
page = 56 # int | A page number within the paginated result set. (optional)

try: 
    # /v1.0/process/
    api_response = api_instance.process_list(page=page)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling ProcessApi->process_list: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**| A page number within the paginated result set. | [optional] 

### Return type

[**InlineResponse2002**](InlineResponse2002.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **process_read**
> InlineResponse2004 process_read(id)

/v1.0/process/{id}/

Return the given process instance.

### Example 
```python
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.ProcessApi()
id = 56 # int | A unique integer value identifying this process execution.

try: 
    # /v1.0/process/{id}/
    api_response = api_instance.process_read(id)
    pprint(api_response)
except ApiException as e:
    print "Exception when calling ProcessApi->process_read: %s\n" % e
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this process execution. | 

### Return type

[**InlineResponse2004**](InlineResponse2004.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

