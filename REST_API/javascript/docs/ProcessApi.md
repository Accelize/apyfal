# AccelizeAcceleratorWs.ProcessApi

All URIs are relative to *http://52.50.186.13*

Method | HTTP request | Description
------------- | ------------- | -------------
[**processCreate**](ProcessApi.md#processCreate) | **POST** /v1.0/process/ | /v1.0/process/
[**processDelete**](ProcessApi.md#processDelete) | **DELETE** /v1.0/process/{id}/ | /v1.0/process/{id}/
[**processList**](ProcessApi.md#processList) | **GET** /v1.0/process/ | /v1.0/process/
[**processRead**](ProcessApi.md#processRead) | **GET** /v1.0/process/{id}/ | /v1.0/process/{id}/


<a name="processCreate"></a>
# **processCreate**
> InlineResponse2003 processCreate(configuration, opts)

/v1.0/process/

Create a new process instance.

### Example
```javascript
var AccelizeAcceleratorWs = require('accelize_accelerator_ws');

var apiInstance = new AccelizeAcceleratorWs.ProcessApi();

var configuration = "configuration_example"; // String | Id of the configuration to use for this process

var opts = { 
  'parameters': "parameters_example", // String | All parameters need for the excution in JSON format : {     \"AcceleratorParam1\":\"value1\",    \"AcceleratorParam2\":\"value2\",    \"AcceleratorParam3\":\"value3\"}
  'datafile': "/path/to/file.txt" // File | If needed, file to be processed by the accelerator.
};

var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.processCreate(configuration, opts, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **configuration** | **String**| Id of the configuration to use for this process | 
 **parameters** | **String**| All parameters need for the excution in JSON format : {     \&quot;AcceleratorParam1\&quot;:\&quot;value1\&quot;,    \&quot;AcceleratorParam2\&quot;:\&quot;value2\&quot;,    \&quot;AcceleratorParam3\&quot;:\&quot;value3\&quot;} | [optional] 
 **datafile** | **File**| If needed, file to be processed by the accelerator. | [optional] 

### Return type

[**InlineResponse2003**](InlineResponse2003.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: Not defined

<a name="processDelete"></a>
# **processDelete**
> processDelete(id)

/v1.0/process/{id}/

### Example
```javascript
var AccelizeAcceleratorWs = require('accelize_accelerator_ws');

var apiInstance = new AccelizeAcceleratorWs.ProcessApi();

var id = 56; // Integer | A unique integer value identifying this process execution.


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully.');
  }
};
apiInstance.processDelete(id, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **Integer**| A unique integer value identifying this process execution. | 

### Return type

null (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

<a name="processList"></a>
# **processList**
> InlineResponse2002 processList(opts)

/v1.0/process/

Returns a list of all process instance requested in the system.

### Example
```javascript
var AccelizeAcceleratorWs = require('accelize_accelerator_ws');

var apiInstance = new AccelizeAcceleratorWs.ProcessApi();

var opts = { 
  'page': 56 // Integer | A page number within the paginated result set.
};

var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.processList(opts, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **Integer**| A page number within the paginated result set. | [optional] 

### Return type

[**InlineResponse2002**](InlineResponse2002.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

<a name="processRead"></a>
# **processRead**
> InlineResponse2004 processRead(id)

/v1.0/process/{id}/

Return the given process instance.

### Example
```javascript
var AccelizeAcceleratorWs = require('accelize_accelerator_ws');

var apiInstance = new AccelizeAcceleratorWs.ProcessApi();

var id = 56; // Integer | A unique integer value identifying this process execution.


var callback = function(error, data, response) {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
};
apiInstance.processRead(id, callback);
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **Integer**| A unique integer value identifying this process execution. | 

### Return type

[**InlineResponse2004**](InlineResponse2004.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

