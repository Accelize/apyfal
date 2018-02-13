# Swagger\Client\ConfigurationApi

All URIs are relative to *http://52.50.186.13*

Method | HTTP request | Description
------------- | ------------- | -------------
[**configurationCreate**](ConfigurationApi.md#configurationCreate) | **POST** /v1.0/configuration/ | /v1.0/configuration/
[**configurationList**](ConfigurationApi.md#configurationList) | **GET** /v1.0/configuration/ | /v1.0/configuration/
[**configurationRead**](ConfigurationApi.md#configurationRead) | **GET** /v1.0/configuration/{id}/ | /v1.0/configuration/{id}/


# **configurationCreate**
> \Swagger\Client\Model\InlineResponse2001 configurationCreate($parameters, $datafile)

/v1.0/configuration/

Create a new configuration instance and deploy it.

### Example
```php
<?php
require_once(__DIR__ . '/vendor/autoload.php');

$api_instance = new Swagger\Client\Api\ConfigurationApi();
$parameters = "parameters_example"; // string | All parameters need for the excution in JSON format : {     \"AcceleratorParam1\":\"value1\",    \"AcceleratorParam2\":\"value2\",    \"AcceleratorParam3\":\"value3\"}
$datafile = "/path/to/file.txt"; // \SplFileObject | If needed, file to be processed by the accelerator.

try {
    $result = $api_instance->configurationCreate($parameters, $datafile);
    print_r($result);
} catch (Exception $e) {
    echo 'Exception when calling ConfigurationApi->configurationCreate: ', $e->getMessage(), PHP_EOL;
}
?>
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **parameters** | **string**| All parameters need for the excution in JSON format : {     \&quot;AcceleratorParam1\&quot;:\&quot;value1\&quot;,    \&quot;AcceleratorParam2\&quot;:\&quot;value2\&quot;,    \&quot;AcceleratorParam3\&quot;:\&quot;value3\&quot;} | [optional]
 **datafile** | **\SplFileObject**| If needed, file to be processed by the accelerator. | [optional]

### Return type

[**\Swagger\Client\Model\InlineResponse2001**](../Model/InlineResponse2001.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: multipart/form-data
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../README.md#documentation-for-models) [[Back to README]](../../README.md)

# **configurationList**
> \Swagger\Client\Model\InlineResponse200 configurationList($page)

/v1.0/configuration/

Returns a list of all accelerator configuration instance requested in the system.

### Example
```php
<?php
require_once(__DIR__ . '/vendor/autoload.php');

$api_instance = new Swagger\Client\Api\ConfigurationApi();
$page = 56; // int | A page number within the paginated result set.

try {
    $result = $api_instance->configurationList($page);
    print_r($result);
} catch (Exception $e) {
    echo 'Exception when calling ConfigurationApi->configurationList: ', $e->getMessage(), PHP_EOL;
}
?>
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**| A page number within the paginated result set. | [optional]

### Return type

[**\Swagger\Client\Model\InlineResponse200**](../Model/InlineResponse200.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../README.md#documentation-for-models) [[Back to README]](../../README.md)

# **configurationRead**
> \Swagger\Client\Model\InlineResponse200Results configurationRead($id)

/v1.0/configuration/{id}/

Return the given configuration instance.

### Example
```php
<?php
require_once(__DIR__ . '/vendor/autoload.php');

$api_instance = new Swagger\Client\Api\ConfigurationApi();
$id = 56; // int | A unique integer value identifying this accelerator config.

try {
    $result = $api_instance->configurationRead($id);
    print_r($result);
} catch (Exception $e) {
    echo 'Exception when calling ConfigurationApi->configurationRead: ', $e->getMessage(), PHP_EOL;
}
?>
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this accelerator config. |

### Return type

[**\Swagger\Client\Model\InlineResponse200Results**](../Model/InlineResponse200Results.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../README.md#documentation-for-models) [[Back to README]](../../README.md)

