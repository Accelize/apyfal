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
    public interface IConfigurationApi
    {
        /// <summary>
        /// /v1.0/configuration/ Create a new configuration instance and deploy it.
        /// </summary>
        /// <param name="owner">user id : username</param>
        /// <param name="provider">cloud provider example : AWS</param>
        /// <param name="parameters">All parameters need for the excution in JSON format : {     \&quot;AcceleratorParam1\&quot;:\&quot;value1\&quot;,    \&quot;AcceleratorParam2\&quot;:\&quot;value2\&quot;,    \&quot;AcceleratorParam3\&quot;:\&quot;value3\&quot;}</param>
        /// <param name="datafile">If needed, file to be processed by the accelerator.</param>
        /// <returns>InlineResponse2001</returns>
        InlineResponse2001 ConfigurationCreate (string owner, string provider, string parameters, System.IO.Stream datafile);
        /// <summary>
        /// /v1.0/configuration/ Returns a list of all accelerator configuration instance requested in the system.
        /// </summary>
        /// <param name="page">A page number within the paginated result set.</param>
        /// <returns>InlineResponse200</returns>
        InlineResponse200 ConfigurationList (int? page);
        /// <summary>
        /// /v1.0/configuration/{id}/ Return the given configuration instance.
        /// </summary>
        /// <param name="id">A unique integer value identifying this accelerator config.</param>
        /// <returns>InlineResponse2002</returns>
        InlineResponse2002 ConfigurationRead (int? id);
    }
  
    /// <summary>
    /// Represents a collection of functions to interact with the API endpoints
    /// </summary>
    public class ConfigurationApi : IConfigurationApi
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="ConfigurationApi"/> class.
        /// </summary>
        /// <param name="apiClient"> an instance of ApiClient (optional)</param>
        /// <returns></returns>
        public ConfigurationApi(ApiClient apiClient = null)
        {
            if (apiClient == null) // use the default one in Configuration
                this.ApiClient = Configuration.DefaultApiClient; 
            else
                this.ApiClient = apiClient;
        }
    
        /// <summary>
        /// Initializes a new instance of the <see cref="ConfigurationApi"/> class.
        /// </summary>
        /// <returns></returns>
        public ConfigurationApi(String basePath)
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
        /// /v1.0/configuration/ Create a new configuration instance and deploy it.
        /// </summary>
        /// <param name="owner">user id : username</param> 
        /// <param name="provider">cloud provider example : AWS</param> 
        /// <param name="parameters">All parameters need for the excution in JSON format : {     \&quot;AcceleratorParam1\&quot;:\&quot;value1\&quot;,    \&quot;AcceleratorParam2\&quot;:\&quot;value2\&quot;,    \&quot;AcceleratorParam3\&quot;:\&quot;value3\&quot;}</param> 
        /// <param name="datafile">If needed, file to be processed by the accelerator.</param> 
        /// <returns>InlineResponse2001</returns>            
        public InlineResponse2001 ConfigurationCreate (string owner, string provider, string parameters, System.IO.Stream datafile)
        {
            
            // verify the required parameter 'owner' is set
            if (owner == null) throw new ApiException(400, "Missing required parameter 'owner' when calling ConfigurationCreate");
            
            // verify the required parameter 'provider' is set
            if (provider == null) throw new ApiException(400, "Missing required parameter 'provider' when calling ConfigurationCreate");
            
    
            var path = "/v1.0/configuration/";
            path = path.Replace("{format}", "json");
                
            var queryParams = new Dictionary<String, String>();
            var headerParams = new Dictionary<String, String>();
            var formParams = new Dictionary<String, String>();
            var fileParams = new Dictionary<String, FileParameter>();
            String postBody = null;
    
                                    if (parameters != null) formParams.Add("parameters", ApiClient.ParameterToString(parameters)); // form parameter
if (owner != null) formParams.Add("owner", ApiClient.ParameterToString(owner)); // form parameter
if (provider != null) formParams.Add("provider", ApiClient.ParameterToString(provider)); // form parameter
if (datafile != null) fileParams.Add("datafile", ApiClient.ParameterToFile("datafile", datafile));
                
            // authentication setting, if any
            String[] authSettings = new String[] {  };
    
            // make the HTTP request
            IRestResponse response = (IRestResponse) ApiClient.CallApi(path, Method.POST, queryParams, postBody, headerParams, formParams, fileParams, authSettings);
    
            if (((int)response.StatusCode) >= 400)
                throw new ApiException ((int)response.StatusCode, "Error calling ConfigurationCreate: " + response.Content, response.Content);
            else if (((int)response.StatusCode) == 0)
                throw new ApiException ((int)response.StatusCode, "Error calling ConfigurationCreate: " + response.ErrorMessage, response.ErrorMessage);
    
            return (InlineResponse2001) ApiClient.Deserialize(response.Content, typeof(InlineResponse2001), response.Headers);
        }
    
        /// <summary>
        /// /v1.0/configuration/ Returns a list of all accelerator configuration instance requested in the system.
        /// </summary>
        /// <param name="page">A page number within the paginated result set.</param> 
        /// <returns>InlineResponse200</returns>            
        public InlineResponse200 ConfigurationList (int? page)
        {
            
    
            var path = "/v1.0/configuration/";
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
                throw new ApiException ((int)response.StatusCode, "Error calling ConfigurationList: " + response.Content, response.Content);
            else if (((int)response.StatusCode) == 0)
                throw new ApiException ((int)response.StatusCode, "Error calling ConfigurationList: " + response.ErrorMessage, response.ErrorMessage);
    
            return (InlineResponse200) ApiClient.Deserialize(response.Content, typeof(InlineResponse200), response.Headers);
        }
    
        /// <summary>
        /// /v1.0/configuration/{id}/ Return the given configuration instance.
        /// </summary>
        /// <param name="id">A unique integer value identifying this accelerator config.</param> 
        /// <returns>InlineResponse2002</returns>            
        public InlineResponse2002 ConfigurationRead (int? id)
        {
            
            // verify the required parameter 'id' is set
            if (id == null) throw new ApiException(400, "Missing required parameter 'id' when calling ConfigurationRead");
            
    
            var path = "/v1.0/configuration/{id}/";
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
                throw new ApiException ((int)response.StatusCode, "Error calling ConfigurationRead: " + response.Content, response.Content);
            else if (((int)response.StatusCode) == 0)
                throw new ApiException ((int)response.StatusCode, "Error calling ConfigurationRead: " + response.ErrorMessage, response.ErrorMessage);
    
            return (InlineResponse2002) ApiClient.Deserialize(response.Content, typeof(InlineResponse2002), response.Headers);
        }
    
    }
}
