Apyfal REST API
===============

It is possible to use accelerators using the REST API instead of Python
But, note that in this case, host configuration is not supported.

The Apyfal REST API follow rhe OpenApi specification.

- `Apyfal REST API Documentation <./_static/rest_api.html>`_
- :download:`Apyfal OpenAPI specification <../rest_api/input_spec.json>`

Generating REST API client in any language using OpenApi
--------------------------------------------------------

With OpenApi, a client can be generated for almost any language
(Java, Javascript, ...)

-  Download and install an OpenAPI client generator (like
   `OpenAPI Generator`_ or `Swagger-Codegen`_).
-  Download the Apyfal repository:

.. code-block:: bash

    git clone https://github.com/Accelize/apyfal.git

-  From the repository directory, run the client generator with the following
   command after replacing ``$GENERATOR_CLI`` with the path to the
   client generator ``.jar`` executable, and
   replacing ``$LANGUAGE`` by the language to generate (Please refer to
   client generator documentation for the list of possible languages)

.. code-block:: bash

    java -jar $GENERATOR_CLI generate -i rest_api/input_spec.json -o rest_api/output -l $LANGUAGE

-  The generated API in the target language can be found in
   ``rest_api/output`` sub-directory inside the repository folder.

.. _OpenAPI Generator: https://github.com/OpenAPITools/openapi-generator
.. _Swagger-Codegen: https://github.com/swagger-api/swagger-codegen
