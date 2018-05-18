# Accelerator REST API

It is possible to use accelerators using the REST API instead of Python acceleratorAPI. But, note that in this case, 
CSP instance configuration is not supported.

## Generating REST API client in any language using Swagger-Codegen

Swagger-Codegen can be used to generate client for almost any language (Java, Javascript, ...)

- Download and install [Swagger-Codegen](https://github.com/swagger-api/swagger-codegen).
- Download the AcceleratorAPI repository:

```bash
git clone https://github.com/Accelize/acceleratorAPI.git 
```
- From the repository directory, run Swagger-Codegen with the following command after replacing `$SWAGGER_CODEGEN_CLI` 
with the path to the Swagger-Codegen Jar (`swagger-codegen-cli-X.X.X.jar`), and replacing `$LANGUAGE` by the 
language to generate (Please refer to Swagger-Codegen documentation for the list of possible languages)

```bash
java -jar $SWAGGER_CODEGEN_CLI generate -i rest_api/input_spec.json -o rest_api/output -l $LANGUAGE
```

- The generated API in the target language can be found in `rest_api/output` sub-directory inside the repository folder.
