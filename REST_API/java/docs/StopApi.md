# StopApi

All URIs are relative to *http://52.50.186.13*

Method | HTTP request | Description
------------- | ------------- | -------------
[**stopList**](StopApi.md#stopList) | **GET** /v1.0/stop | /v1.0/stop


<a name="stopList"></a>
# **stopList**
> Object stopList()

/v1.0/stop

### Example
```java
// Import classes:
//import invalidPackageName.ApiException;
//import accelize_accelerator.StopApi;


StopApi apiInstance = new StopApi();
try {
    Object result = apiInstance.stopList();
    System.out.println(result);
} catch (ApiException e) {
    System.err.println("Exception when calling StopApi#stopList");
    e.printStackTrace();
}
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

