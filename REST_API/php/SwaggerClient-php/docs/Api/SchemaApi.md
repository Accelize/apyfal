# Swagger\Client\SchemaApi

All URIs are relative to *http://52.50.186.13*

Method | HTTP request | Description
------------- | ------------- | -------------
[**schemaList**](SchemaApi.md#schemaList) | **GET** /v1.0/schema/ | /v1.0/schema/


# **schemaList**
> schemaList()

/v1.0/schema/

### Example
```php
<?php
require_once(__DIR__ . '/vendor/autoload.php');

$api_instance = new Swagger\Client\Api\SchemaApi();

try {
    $api_instance->schemaList();
} catch (Exception $e) {
    echo 'Exception when calling SchemaApi->schemaList: ', $e->getMessage(), PHP_EOL;
}
?>
```

### Parameters
This endpoint does not need any parameter.

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../../README.md#documentation-for-api-endpoints) [[Back to Model list]](../../README.md#documentation-for-models) [[Back to README]](../../README.md)

