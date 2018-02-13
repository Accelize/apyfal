# swagger_client.SchemaApi

All URIs are relative to *http://52.50.186.13*

Method | HTTP request | Description
------------- | ------------- | -------------
[**schema_list**](SchemaApi.md#schema_list) | **GET** /v1.0/schema/ | /v1.0/schema/


# **schema_list**
> schema_list()

/v1.0/schema/

### Example 
```python
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.SchemaApi()

try: 
    # /v1.0/schema/
    api_instance.schema_list()
except ApiException as e:
    print "Exception when calling SchemaApi->schema_list: %s\n" % e
```

### Parameters
This endpoint does not need any parameter.

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

