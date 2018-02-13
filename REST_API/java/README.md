# swagger-java-client

## Requirements

Building the API client library requires [Maven](https://maven.apache.org/) to be installed.

## Installation

To install the API client library to your local Maven repository, simply execute:

```shell
mvn install
```

To deploy it to a remote Maven repository instead, configure the settings of the repository and execute:

```shell
mvn deploy
```

Refer to the [official documentation](https://maven.apache.org/plugins/maven-deploy-plugin/usage.html) for more information.

### Maven users

Add this dependency to your project's POM:

```xml
<dependency>
    <groupId>io.swagger</groupId>
    <artifactId>swagger-java-client</artifactId>
    <version>1.0.0</version>
    <scope>compile</scope>
</dependency>
```

### Gradle users

Add this dependency to your project's build file:

```groovy
compile "io.swagger:swagger-java-client:1.0.0"
```

### Others

At first generate the JAR by executing:

    mvn package

Then manually install the following JARs:

* target/swagger-java-client-1.0.0.jar
* target/lib/*.jar

## Getting Started

Please follow the [installation](#installation) instruction and execute the following Java code:

```java

import invalidPackageName.*;
import invalidPackageName.auth.*;
import invalidPackageName.model.*;
import accelizea_accelerator.ConfigurationApi;

import java.io.File;
import java.util.*;

public class ConfigurationApiExample {

    public static void main(String[] args) {
        
        ConfigurationApi apiInstance = new ConfigurationApi();
        String owner = "owner_example"; // String | user id : username
        String provider = "provider_example"; // String | cloud provider example : AWS
        String parameters = "parameters_example"; // String | All parameters need for the excution in JSON format : {     \"AcceleratorParam1\":\"value1\",    \"AcceleratorParam2\":\"value2\",    \"AcceleratorParam3\":\"value3\"}
        File datafile = new File("/path/to/file.txt"); // File | If needed, file to be processed by the accelerator.
        try {
            InlineResponse2001 result = apiInstance.configurationCreate(owner, provider, parameters, datafile);
            System.out.println(result);
        } catch (ApiException e) {
            System.err.println("Exception when calling ConfigurationApi#configurationCreate");
            e.printStackTrace();
        }
    }
}

```

## Documentation for API Endpoints

All URIs are relative to *http://34.226.159.218*

Class | Method | HTTP request | Description
------------ | ------------- | ------------- | -------------
*ConfigurationApi* | [**configurationCreate**](docs/ConfigurationApi.md#configurationCreate) | **POST** /v1.0/configuration/ | /v1.0/configuration/
*ConfigurationApi* | [**configurationList**](docs/ConfigurationApi.md#configurationList) | **GET** /v1.0/configuration/ | /v1.0/configuration/
*ConfigurationApi* | [**configurationRead**](docs/ConfigurationApi.md#configurationRead) | **GET** /v1.0/configuration/{id}/ | /v1.0/configuration/{id}/
*ProcessApi* | [**processCreate**](docs/ProcessApi.md#processCreate) | **POST** /v1.0/process/ | /v1.0/process/
*ProcessApi* | [**processList**](docs/ProcessApi.md#processList) | **GET** /v1.0/process/ | /v1.0/process/
*ProcessApi* | [**processRead**](docs/ProcessApi.md#processRead) | **GET** /v1.0/process/{id}/ | /v1.0/process/{id}/
*SchemaApi* | [**schemaList**](docs/SchemaApi.md#schemaList) | **GET** /v1.0/schema/ | /v1.0/schema/


## Documentation for Models

 - [InlineResponse200](docs/InlineResponse200.md)
 - [InlineResponse2001](docs/InlineResponse2001.md)
 - [InlineResponse2002](docs/InlineResponse2002.md)
 - [InlineResponse2003](docs/InlineResponse2003.md)
 - [InlineResponse2003Results](docs/InlineResponse2003Results.md)
 - [InlineResponse2004](docs/InlineResponse2004.md)
 - [InlineResponse200Results](docs/InlineResponse200Results.md)


## Documentation for Authorization

Authentication schemes defined for the API:
### basic

- **Type**: HTTP basic authentication


## Recommendation

It's recommended to create an instance of `ApiClient` per thread in a multithreaded environment to avoid any potential issue.

## Author



