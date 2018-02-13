# SchemaApi

All URIs are relative to *http://52.50.186.13*

Method | HTTP request | Description
------------- | ------------- | -------------
[**schemaList**](SchemaApi.md#schemaList) | **GET** /v1.0/schema/ | /v1.0/schema/


<a name="schemaList"></a>
# **schemaList**
> schemaList()

/v1.0/schema/

### Example
```java
// Import classes:
//import invalidPackageName.ApiException;
//import accelize_accelerator.SchemaApi;


SchemaApi apiInstance = new SchemaApi();
try {
    apiInstance.schemaList();
} catch (ApiException e) {
    System.err.println("Exception when calling SchemaApi#schemaList");
    e.printStackTrace();
}
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

