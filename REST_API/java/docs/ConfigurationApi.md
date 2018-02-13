# ConfigurationApi

All URIs are relative to *http://52.50.186.13*

Method | HTTP request | Description
------------- | ------------- | -------------
[**configurationCreate**](ConfigurationApi.md#configurationCreate) | **POST** /v1.0/configuration/ | /v1.0/configuration/
[**configurationList**](ConfigurationApi.md#configurationList) | **GET** /v1.0/configuration/ | /v1.0/configuration/
[**configurationRead**](ConfigurationApi.md#configurationRead) | **GET** /v1.0/configuration/{id}/ | /v1.0/configuration/{id}/


<a name="configurationCreate"></a>
# **configurationCreate**
> InlineResponse2001 configurationCreate(parameters, datafile)

/v1.0/configuration/

Create a new configuration instance and deploy it.

### Example
```java
// Import classes:
//import invalidPackageName.ApiException;
//import accelize_accelerator.ConfigurationApi;


ConfigurationApi apiInstance = new ConfigurationApi();
String parameters = "parameters_example"; // String | All parameters need for the excution in JSON format : {     \"AcceleratorParam1\":\"value1\",    \"AcceleratorParam2\":\"value2\",    \"AcceleratorParam3\":\"value3\"}
File datafile = new File("/path/to/file.txt"); // File | If needed, file to be processed by the accelerator.
try {
    InlineResponse2001 result = apiInstance.configurationCreate(parameters, datafile);
    System.out.println(result);
} catch (ApiException e) {
    System.err.println("Exception when calling ConfigurationApi#configurationCreate");
    e.printStackTrace();
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parameters** | **String**| All parameters need for the excution in JSON format : {     \&quot;AcceleratorParam1\&quot;:\&quot;value1\&quot;,    \&quot;AcceleratorParam2\&quot;:\&quot;value2\&quot;,    \&quot;AcceleratorParam3\&quot;:\&quot;value3\&quot;} | [optional]
 **datafile** | **File**| If needed, file to be processed by the accelerator. | [optional]

### Return type

[**InlineResponse2001**](InlineResponse2001.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: Not defined

<a name="configurationList"></a>
# **configurationList**
> InlineResponse200 configurationList(page)

/v1.0/configuration/

Returns a list of all accelerator configuration instance requested in the system.

### Example
```java
// Import classes:
//import invalidPackageName.ApiException;
//import accelize_accelerator.ConfigurationApi;


ConfigurationApi apiInstance = new ConfigurationApi();
Integer page = 56; // Integer | A page number within the paginated result set.
try {
    InlineResponse200 result = apiInstance.configurationList(page);
    System.out.println(result);
} catch (ApiException e) {
    System.err.println("Exception when calling ConfigurationApi#configurationList");
    e.printStackTrace();
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **Integer**| A page number within the paginated result set. | [optional]

### Return type

[**InlineResponse200**](InlineResponse200.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

<a name="configurationRead"></a>
# **configurationRead**
> InlineResponse200Results configurationRead(id)

/v1.0/configuration/{id}/

Return the given configuration instance.

### Example
```java
// Import classes:
//import invalidPackageName.ApiException;
//import accelize_accelerator.ConfigurationApi;


ConfigurationApi apiInstance = new ConfigurationApi();
Integer id = 56; // Integer | A unique integer value identifying this accelerator config.
try {
    InlineResponse200Results result = apiInstance.configurationRead(id);
    System.out.println(result);
} catch (ApiException e) {
    System.err.println("Exception when calling ConfigurationApi#configurationRead");
    e.printStackTrace();
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **Integer**| A unique integer value identifying this accelerator config. |

### Return type

[**InlineResponse200Results**](InlineResponse200Results.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

