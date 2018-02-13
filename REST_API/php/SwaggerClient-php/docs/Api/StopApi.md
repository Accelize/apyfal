# Swagger\Client\StopApi

All URIs are relative to *http://52.50.186.13*

Method | HTTP request | Description
------------- | ------------- | -------------
[**stopList**](StopApi.md#stopList) | **GET** /v1.0/stop | /v1.0/stop


# **stopList**
> object stopList()

/v1.0/stop

### Example
```php
<?php
require_once(__DIR__ . '/vendor/autoload.php');

$api_instance = new Swagger\Client\Api\StopApi();

try {
    $result = $api_instance->stopList();
    print_r($result);
} catch (Exception $e) {
    echo 'Exception when calling StopApi->stopList: ', $e->getMessage(), PHP_EOL;
}
?>
```

### Parameters
This endpoint does not need any parameter.

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../README.md#documentation-for-models) [[Back to README]](../../README.md)

