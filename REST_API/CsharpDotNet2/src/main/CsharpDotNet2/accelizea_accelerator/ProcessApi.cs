using System;
using System.Collections.Generic;
using RestSharp;
using IO.Swagger.Client;
using IO.Swagger.Model;

namespace IO.Swagger.Api
{
    /// <summary>
    /// Represents a collection of functions to interact with the API endpoints
    /// </summary>
    public interface IProcessApi
    {
        /// <summary>
        /// /v1.0/process/ Create a new process instance.
        /// </summary>
        /// <param name="configuration">Id of the configuration to use for this process</param>
        /// <param name="parameters">All parameters need for the excution in JSON format : {     \&quot;AcceleratorParam1\&quot;:\&quot;value1\&quot;,    \&quot;AcceleratorParam2\&quot;:\&quot;value2\&quot;,    \&quot;AcceleratorParam3\&quot;:\&quot;value3\&quot;}</param>
        /// <param name="datafile">If needed, file to be processed by the accelerator.</param>
        /// <returns>InlineResponse2004</returns>
        InlineResponse2004 ProcessCreate (string configuration, string parameters, System.IO.Stream datafile);
        /// <summary>
        /// /v1.0/process/ Returns a list of all process instance requested in the system.
        /// </summary>
        /// <param name="page">A page number within the paginated result set.</param>
        /// <returns>InlineResponse2003</returns>
        InlineResponse2003 ProcessList (int? page);
        /// <summary>
        /// /v1.0/process/{id}/ Return the given process instance.
        /// </summary>
        /// <param name="id">A unique integer value identifying this process execution.</param>
        /// <returns>InlineResponse2004</returns>
        InlineResponse2004 ProcessRead (int? id);
    }
  
    /// <summary>
    /// Represents a collection of functions to interact with the API endpoints
    /// </summary>
    public class ProcessApi : IProcessApi
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="ProcessApi"/> class.
        /// </summary>
        /// <param name="apiClient"> an instance of ApiClient (optional)</param>
        /// <returns></returns>
        public ProcessApi(ApiClient apiClient = null)
        {
            if (apiClient == null) // use the default one in Configuration
                this.ApiClient = Configuration.DefaultApiClient; 
            else
                this.ApiClient = apiClient;
        }
    
        /// <summary>
        /// Initializes a new instance of the <see cref="ProcessApi"/> class.
        /// </summary>
        /// <returns></returns>
        public ProcessApi(String basePath)
        {
            this.ApiClient = new ApiClient(basePath);
        }
    
        /// <summary>
        /// Sets the base path of the API client.
        /// </summary>
        /// <param name="basePath">The base path</param>
        /// <value>The base path</value>
        public void SetBasePath(String basePath)
        {
            this.ApiClient.BasePath = basePath;
        }
    
        /// <summary>
        /// Gets the base path of the API client.
        /// </summary>
        /// <param name="basePath">The base path</param>
        /// <value>The base path</value>
        public String GetBasePath(String basePath)
        {
            return this.ApiClient.BasePath;
        }
    
        /// <summary>
        /// Gets or sets the API client.
        /// </summary>
        /// <value>An instance of the ApiClient</value>
        public ApiClient ApiClient {get; set;}
    
        /// <summary>
        /// /v1.0/process/ Create a new process instance.
        /// </summary>
        /// <param name="configuration">Id of the configuration to use for this process</param> 
        /// <param name="parameters">All parameters need for the excution in JSON format : {     \&quot;AcceleratorParam1\&quot;:\&quot;value1\&quot;,    \&quot;AcceleratorParam2\&quot;:\&quot;value2\&quot;,    \&quot;AcceleratorParam3\&quot;:\&quot;value3\&quot;}</param> 
        /// <param name="datafile">If needed, file to be processed by the accelerator.</param> 
        /// <returns>InlineResponse2004</returns>            
        public InlineResponse2004 ProcessCreate (string configuration, string parameters, System.IO.Stream datafile)
        {
            
            // verify the required parameter 'configuration' is set
            if (configuration == null) throw new ApiException(400, "Missing required parameter 'configuration' when calling ProcessCreate");
            
    
            var path = "/v1.0/process/";
            path = path.Replace("{format}", "json");
                
            var queryParams = new Dictionary<String, String>();
            var headerParams = new Dictionary<String, String>();
            var formParams = new Dictionary<String, String>();
            var fileParams = new Dictionary<String, FileParameter>();
            String postBody = null;
    
                                    if (parameters != null) formParams.Add("parameters", ApiClient.ParameterToString(parameters)); // form parameter
if (configuration != null) formParams.Add("configuration", ApiClient.ParameterToString(configuration)); // form parameter
if (datafile != null) fileParams.Add("datafile", ApiClient.ParameterToFile("datafile", datafile));
                
            // authentication setting, if any
            String[] authSettings = new String[] {  };
    
            // make the HTTP request
            IRestResponse response = (IRestResponse) ApiClient.CallApi(path, Method.POST, queryParams, postBody, headerParams, formParams, fileParams, authSettings);
    
            if (((int)response.StatusCode) >= 400)
                throw new ApiException ((int)response.StatusCode, "Error calling ProcessCreate: " + response.Content, response.Content);
            else if (((int)response.StatusCode) == 0)
                throw new ApiException ((int)response.StatusCode, "Error calling ProcessCreate: " + response.ErrorMessage, response.ErrorMessage);
    
            return (InlineResponse2004) ApiClient.Deserialize(response.Content, typeof(InlineResponse2004), response.Headers);
        }
    
        /// <summary>
        /// /v1.0/process/ Returns a list of all process instance requested in the system.
        /// </summary>
        /// <param name="page">A page number within the paginated result set.</param> 
        /// <returns>InlineResponse2003</returns>            
        public InlineResponse2003 ProcessList (int? page)
        {
            
    
            var path = "/v1.0/process/";
            path = path.Replace("{format}", "json");
                
            var queryParams = new Dictionary<String, String>();
            var headerParams = new Dictionary<String, String>();
            var formParams = new Dictionary<String, String>();
            var fileParams = new Dictionary<String, FileParameter>();
            String postBody = null;
    
             if (page != null) queryParams.Add("page", ApiClient.ParameterToString(page)); // query parameter
                                        
            // authentication setting, if any
            String[] authSettings = new String[] {  };
    
            // make the HTTP request
            IRestResponse response = (IRestResponse) ApiClient.CallApi(path, Method.GET, queryParams, postBody, headerParams, formParams, fileParams, authSettings);
    
            if (((int)response.StatusCode) >= 400)
                throw new ApiException ((int)response.StatusCode, "Error calling ProcessList: " + response.Content, response.Content);
            else if (((int)response.StatusCode) == 0)
                throw new ApiException ((int)response.StatusCode, "Error calling ProcessList: " + response.ErrorMessage, response.ErrorMessage);
    
            return (InlineResponse2003) ApiClient.Deserialize(response.Content, typeof(InlineResponse2003), response.Headers);
        }
    
        /// <summary>
        /// /v1.0/process/{id}/ Return the given process instance.
        /// </summary>
        /// <param name="id">A unique integer value identifying this process execution.</param> 
        /// <returns>InlineResponse2004</returns>            
        public InlineResponse2004 ProcessRead (int? id)
        {
            
            // verify the required parameter 'id' is set
            if (id == null) throw new ApiException(400, "Missing required parameter 'id' when calling ProcessRead");
            
    
            var path = "/v1.0/process/{id}/";
            path = path.Replace("{format}", "json");
            path = path.Replace("{" + "id" + "}", ApiClient.ParameterToString(id));
    
            var queryParams = new Dictionary<String, String>();
            var headerParams = new Dictionary<String, String>();
            var formParams = new Dictionary<String, String>();
            var fileParams = new Dictionary<String, FileParameter>();
            String postBody = null;
    
                                                    
            // authentication setting, if any
            String[] authSettings = new String[] {  };
    
            // make the HTTP request
            IRestResponse response = (IRestResponse) ApiClient.CallApi(path, Method.GET, queryParams, postBody, headerParams, formParams, fileParams, authSettings);
    
            if (((int)response.StatusCode) >= 400)
                throw new ApiException ((int)response.StatusCode, "Error calling ProcessRead: " + response.Content, response.Content);
            else if (((int)response.StatusCode) == 0)
                throw new ApiException ((int)response.StatusCode, "Error calling ProcessRead: " + response.ErrorMessage, response.ErrorMessage);
    
            return (InlineResponse2004) ApiClient.Deserialize(response.Content, typeof(InlineResponse2004), response.Headers);
        }
    
    }
}
