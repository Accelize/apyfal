package accelizea_accelerator {

import io.swagger.common.ApiInvoker;
import io.swagger.exception.ApiErrorCodes;
import io.swagger.exception.ApiError;
import io.swagger.common.ApiUserCredentials;
import io.swagger.event.Response;
import io.swagger.common.SwaggerApi;
import io.swagger.client.model.InlineResponse2001;
import flash.filesystem.File;
import io.swagger.client.model.InlineResponse200;
import io.swagger.client.model.InlineResponse2002;

import mx.rpc.AsyncToken;
import mx.utils.UIDUtil;
import flash.utils.Dictionary;
import flash.events.EventDispatcher;

public class ConfigurationApi extends SwaggerApi {
    /**
    * Constructor for the ConfigurationApi api client
    * @param apiCredentials Wrapper object for tokens and hostName required towards authentication
    * @param eventDispatcher Optional event dispatcher that when provided is used by the SDK to dispatch any Response
    */
    public function ConfigurationApi(apiCredentials: ApiUserCredentials, eventDispatcher: EventDispatcher = null) {
        super(apiCredentials, eventDispatcher);
    }

        public static const event_configuration_create: String = "configuration_create";
        public static const event_configuration_list: String = "configuration_list";
        public static const event_configuration_read: String = "configuration_read";


    /*
     * Returns InlineResponse2001 
     */
    public function configuration_create (owner: String, provider: String, parameters: String, datafile: File): String {
        // create path and map variables
        var path: String = "/v1.0/configuration/".replace(/{format}/g,"xml");

        // query params
        var queryParams: Dictionary = new Dictionary();
        var headerParams: Dictionary = new Dictionary();

        // verify required params are set
        if(        // verify required params are set
        if(        // verify required params are set
        if(        // verify required params are set
        if() {
            throw new ApiError(400, "missing required params");
        }
) {
            throw new ApiError(400, "missing required params");
        }
) {
            throw new ApiError(400, "missing required params");
        }
) {
            throw new ApiError(400, "missing required params");
        }

        
        
        var token:AsyncToken = getApiInvoker().invokeAPI(path, "POST", queryParams, null, headerParams);

        var requestId: String = getUniqueId();

        token.requestId = requestId;
        token.completionEventType = "configuration_create";

        token.returnType = InlineResponse2001;
        return requestId;

    }

    /*
     * Returns InlineResponse200 
     */
    public function configuration_list (page: Number): String {
        // create path and map variables
        var path: String = "/v1.0/configuration/".replace(/{format}/g,"xml");

        // query params
        var queryParams: Dictionary = new Dictionary();
        var headerParams: Dictionary = new Dictionary();

        // verify required params are set
        if() {
            throw new ApiError(400, "missing required params");
        }

        if("null" != String(page))
            queryParams["page"] = toPathValue(page);

        
        var token:AsyncToken = getApiInvoker().invokeAPI(path, "GET", queryParams, null, headerParams);

        var requestId: String = getUniqueId();

        token.requestId = requestId;
        token.completionEventType = "configuration_list";

        token.returnType = InlineResponse200;
        return requestId;

    }

    /*
     * Returns InlineResponse2002 
     */
    public function configuration_read (id: Number): String {
        // create path and map variables
        var path: String = "/v1.0/configuration/{id}/".replace(/{format}/g,"xml").replace("{" + "id" + "}", getApiInvoker().escapeString(id));

        // query params
        var queryParams: Dictionary = new Dictionary();
        var headerParams: Dictionary = new Dictionary();

        // verify required params are set
        if() {
            throw new ApiError(400, "missing required params");
        }

        
        
        var token:AsyncToken = getApiInvoker().invokeAPI(path, "GET", queryParams, null, headerParams);

        var requestId: String = getUniqueId();

        token.requestId = requestId;
        token.completionEventType = "configuration_read";

        token.returnType = InlineResponse2002;
        return requestId;

    }
}
}
