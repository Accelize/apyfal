# AccelizeAcceleratorWs.StopApi

All URIs are relative to *http://52.50.186.13*

Method | HTTP request | Description
------------- | ------------- | -------------
[**stopList**](StopApi.md#stopList) | **GET** /v1.0/stop | /v1.0/stop


<a name="stopList"></a>
# **stopList**
> Object stopList()

/v1.0/stop

### Example
```javascript
var AccelizeAcceleratorWs = require('accelize_accelerator_ws');

var apiInstance = new AccelizeAcceleratorWs.StopApi();

var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.stopList(callback);
```

### Parameters
This endpoint does not need any parameter.

### Return type

**Object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

