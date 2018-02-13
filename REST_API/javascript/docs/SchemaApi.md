# AccelizeAcceleratorWs.SchemaApi

All URIs are relative to *http://52.50.186.13*

Method | HTTP request | Description
------------- | ------------- | -------------
[**schemaList**](SchemaApi.md#schemaList) | **GET** /v1.0/schema/ | /v1.0/schema/


<a name="schemaList"></a>
# **schemaList**
> schemaList()

/v1.0/schema/

### Example
```javascript
var AccelizeAcceleratorWs = require('accelize_accelerator_ws');

var apiInstance = new AccelizeAcceleratorWs.SchemaApi();

var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
};
apiInstance.schemaList(callback);
```

### Parameters
This endpoint does not need any parameter.

### Return type

null (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

