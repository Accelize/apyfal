# swagger_client.StopApi

All URIs are relative to *http://52.50.186.13*

Method | HTTP request | Description
------------- | ------------- | -------------
[**stop_list**](StopApi.md#stop_list) | **GET** /v1.0/stop | /v1.0/stop


# **stop_list**
> object stop_list()

/v1.0/stop

### Example 
```python
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.StopApi()

try: 
    # /v1.0/stop
    api_response = api_instance.stop_list()
    pprint(api_response)
except ApiException as e:
    print "Exception when calling StopApi->stop_list: %s\n" % e
```

### Parameters
This endpoint does not need any parameter.

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

