# \ConfigurationApi

All URIs are relative to *http://52.50.186.13*

Method | HTTP request | Description
------------- | ------------- | -------------
[**ConfigurationCreate**](ConfigurationApi.md#ConfigurationCreate) | **Post** /v1.0/configuration/ | /v1.0/configuration/
[**ConfigurationList**](ConfigurationApi.md#ConfigurationList) | **Get** /v1.0/configuration/ | /v1.0/configuration/
[**ConfigurationRead**](ConfigurationApi.md#ConfigurationRead) | **Get** /v1.0/configuration/{id}/ | /v1.0/configuration/{id}/


# **ConfigurationCreate**
> InlineResponse2001 ConfigurationCreate($parameters, $datafile)

/v1.0/configuration/

Create a new configuration instance and deploy it.


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parameters** | **string**| All parameters need for the excution in JSON format : {     \&quot;AcceleratorParam1\&quot;:\&quot;value1\&quot;,    \&quot;AcceleratorParam2\&quot;:\&quot;value2\&quot;,    \&quot;AcceleratorParam3\&quot;:\&quot;value3\&quot;} | [optional] 
 **datafile** | ***os.File**| If needed, file to be processed by the accelerator. | [optional] 

### Return type

[**InlineResponse2001**](inline_response_200_1.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **ConfigurationList**
> InlineResponse200 ConfigurationList($page)

/v1.0/configuration/

Returns a list of all accelerator configuration instance requested in the system.


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int32**| A page number within the paginated result set. | [optional] 

### Return type

[**InlineResponse200**](inline_response_200.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **ConfigurationRead**
> InlineResponse200Results ConfigurationRead($id)

/v1.0/configuration/{id}/

Return the given configuration instance.


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int32**| A unique integer value identifying this accelerator config. | 

### Return type

[**InlineResponse200Results**](inline_response_200_results.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

