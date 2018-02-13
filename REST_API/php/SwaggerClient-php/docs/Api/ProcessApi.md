# Swagger\Client\ProcessApi

All URIs are relative to *http://52.50.186.13*

Method | HTTP request | Description
------------- | ------------- | -------------
[**processCreate**](ProcessApi.md#processCreate) | **POST** /v1.0/process/ | /v1.0/process/
[**processDelete**](ProcessApi.md#processDelete) | **DELETE** /v1.0/process/{id}/ | /v1.0/process/{id}/
[**processList**](ProcessApi.md#processList) | **GET** /v1.0/process/ | /v1.0/process/
[**processRead**](ProcessApi.md#processRead) | **GET** /v1.0/process/{id}/ | /v1.0/process/{id}/


# **processCreate**
> \Swagger\Client\Model\InlineResponse2003 processCreate($configuration, $parameters, $datafile)

/v1.0/process/

Create a new process instance.

### Example
```php
<?php
require_once(__DIR__ . '/vendor/autoload.php');

$api_instance = new Swagger\Client\Api\ProcessApi();
$configuration = "configuration_example"; // string | Id of the configuration to use for this process
$parameters = "parameters_example"; // string | All parameters need for the excution in JSON format : {     \"AcceleratorParam1\":\"value1\",    \"AcceleratorParam2\":\"value2\",    \"AcceleratorParam3\":\"value3\"}
$datafile = "/path/to/file.txt"; // \SplFileObject | If needed, file to be processed by the accelerator.

try {
    $result = $api_instance->processCreate($configuration, $parameters, $datafile);
    print_r($result);
} catch (Exception $e) {
    echo 'Exception when calling ProcessApi->processCreate: ', $e->getMessage(), PHP_EOL;
}
?>
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **configuration** | **string**| Id of the configuration to use for this process |
 **parameters** | **string**| All parameters need for the excution in JSON format : {     \&quot;AcceleratorParam1\&quot;:\&quot;value1\&quot;,    \&quot;AcceleratorParam2\&quot;:\&quot;value2\&quot;,    \&quot;AcceleratorParam3\&quot;:\&quot;value3\&quot;} | [optional]
 **datafile** | **\SplFileObject**| If needed, file to be processed by the accelerator. | [optional]

### Return type

[**\Swagger\Client\Model\InlineResponse2003**](../Model/InlineResponse2003.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../README.md#documentation-for-models) [[Back to README]](../../README.md)

# **processDelete**
> processDelete($id)

/v1.0/process/{id}/

### Example
```php
<?php
require_once(__DIR__ . '/vendor/autoload.php');

$api_instance = new Swagger\Client\Api\ProcessApi();
$id = 56; // int | A unique integer value identifying this process execution.

try {
    $api_instance->processDelete($id);
} catch (Exception $e) {
    echo 'Exception when calling ProcessApi->processDelete: ', $e->getMessage(), PHP_EOL;
}
?>
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this process execution. |

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../README.md#documentation-for-models) [[Back to README]](../../README.md)

# **processList**
> \Swagger\Client\Model\InlineResponse2002 processList($page)

/v1.0/process/

Returns a list of all process instance requested in the system.

### Example
```php
<?php
require_once(__DIR__ . '/vendor/autoload.php');

$api_instance = new Swagger\Client\Api\ProcessApi();
$page = 56; // int | A page number within the paginated result set.

try {
    $result = $api_instance->processList($page);
    print_r($result);
} catch (Exception $e) {
    echo 'Exception when calling ProcessApi->processList: ', $e->getMessage(), PHP_EOL;
}
?>
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**| A page number within the paginated result set. | [optional]

### Return type

[**\Swagger\Client\Model\InlineResponse2002**](../Model/InlineResponse2002.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../README.md#documentation-for-models) [[Back to README]](../../README.md)

# **processRead**
> \Swagger\Client\Model\InlineResponse2004 processRead($id)

/v1.0/process/{id}/

Return the given process instance.

### Example
```php
<?php
require_once(__DIR__ . '/vendor/autoload.php');

$api_instance = new Swagger\Client\Api\ProcessApi();
$id = 56; // int | A unique integer value identifying this process execution.

try {
    $result = $api_instance->processRead($id);
    print_r($result);
} catch (Exception $e) {
    echo 'Exception when calling ProcessApi->processRead: ', $e->getMessage(), PHP_EOL;
}
?>
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this process execution. |

### Return type

[**\Swagger\Client\Model\InlineResponse2004**](../Model/InlineResponse2004.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../README.md#documentation-for-models) [[Back to README]](../../README.md)

