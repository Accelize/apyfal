# \ProcessApi

All URIs are relative to *http://52.50.186.13*

Method | HTTP request | Description
------------- | ------------- | -------------
[**ProcessCreate**](ProcessApi.md#ProcessCreate) | **Post** /v1.0/process/ | /v1.0/process/
[**ProcessDelete**](ProcessApi.md#ProcessDelete) | **Delete** /v1.0/process/{id}/ | /v1.0/process/{id}/
[**ProcessList**](ProcessApi.md#ProcessList) | **Get** /v1.0/process/ | /v1.0/process/
[**ProcessRead**](ProcessApi.md#ProcessRead) | **Get** /v1.0/process/{id}/ | /v1.0/process/{id}/


# **ProcessCreate**
> InlineResponse2003 ProcessCreate($configuration, $parameters, $datafile)

/v1.0/process/

Create a new process instance.


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **configuration** | **string**| Id of the configuration to use for this process | 
 **parameters** | **string**| All parameters need for the excution in JSON format : {     \&quot;AcceleratorParam1\&quot;:\&quot;value1\&quot;,    \&quot;AcceleratorParam2\&quot;:\&quot;value2\&quot;,    \&quot;AcceleratorParam3\&quot;:\&quot;value3\&quot;} | [optional] 
 **datafile** | ***os.File**| If needed, file to be processed by the accelerator. | [optional] 

### Return type

[**InlineResponse2003**](inline_response_200_3.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **ProcessDelete**
> ProcessDelete($id)

/v1.0/process/{id}/


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int32**| A unique integer value identifying this process execution. | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **ProcessList**
> InlineResponse2002 ProcessList($page)

/v1.0/process/

Returns a list of all process instance requested in the system.


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32**| A page number within the paginated result set. | [optional] 

### Return type

[**InlineResponse2002**](inline_response_200_2.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **ProcessRead**
> InlineResponse2004 ProcessRead($id)

/v1.0/process/{id}/

Return the given process instance.


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int32**| A unique integer value identifying this process execution. | 

### Return type

[**InlineResponse2004**](inline_response_200_4.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

