package accelize_accelerator {

import io.swagger.common.ApiInvoker;
import io.swagger.exception.ApiErrorCodes;
import io.swagger.exception.ApiError;
import io.swagger.common.ApiUserCredentials;
import io.swagger.event.Response;
import io.swagger.common.SwaggerApi;
import io.swagger.client.model.InlineResponse2003;
import flash.filesystem.File;
import io.swagger.client.model.InlineResponse2002;
import io.swagger.client.model.InlineResponse2004;

import mx.rpc.AsyncToken;
import mx.utils.UIDUtil;
import flash.utils.Dictionary;
import flash.events.EventDispatcher;

public class ProcessApi extends SwaggerApi {
    /**
    * Constructor for the ProcessApi api client
    * @param apiCredentials Wrapper object for tokens and hostName required towards authentication
    * @param eventDispatcher Optional event dispatcher that when provided is used by the SDK to dispatch any Response
    */
    public function ProcessApi(apiCredentials: ApiUserCredentials, eventDispatcher: EventDispatcher = null) {
        super(apiCredentials, eventDispatcher);
    }

        public static const event_process_create: String = "process_create";
        public static const event_process_delete: String = "process_delete";
        public static const event_process_list: String = "process_list";
        public static const event_process_read: String = "process_read";


    /*
     * Returns InlineResponse2003 
     */
    public function process_create (configuration: String, parameters: String, datafile: File): String {
        // create path and map variables
        var path: String = "/v1.0/process/".replace(/{format}/g,"xml");

        // query params
        var queryParams: Dictionary = new Dictionary();
        var headerParams: Dictionary = new Dictionary();

        // verify required params are set
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

        
        
        var token:AsyncToken = getApiInvoker().invokeAPI(path, "POST", queryParams, null, headerParams);

        var requestId: String = getUniqueId();

        token.requestId = requestId;
        token.completionEventType = "process_create";

        token.returnType = InlineResponse2003;
        return requestId;

    }

    /*
     * Returns void 
     */
    public function process_delete (id: Number): String {
        // create path and map variables
        var path: String = "/v1.0/process/{id}/".replace(/{format}/g,"xml").replace("{" + "id" + "}", getApiInvoker().escapeString(id));

        // query params
        var queryParams: Dictionary = new Dictionary();
        var headerParams: Dictionary = new Dictionary();

        // verify required params are set
        if() {
            throw new ApiError(400, "missing required params");
        }

        
        
        var token:AsyncToken = getApiInvoker().invokeAPI(path, "DELETE", queryParams, null, headerParams);

        var requestId: String = getUniqueId();

        token.requestId = requestId;
        token.completionEventType = "process_delete";

        token.returnType = null ;
        return requestId;

    }

    /*
     * Returns InlineResponse2002 
     */
    public function process_list (page: Number): String {
        // create path and map variables
        var path: String = "/v1.0/process/".replace(/{format}/g,"xml");

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
        token.completionEventType = "process_list";

        token.returnType = InlineResponse2002;
        return requestId;

    }

    /*
     * Returns InlineResponse2004 
     */
    public function process_read (id: Number): String {
        // create path and map variables
        var path: String = "/v1.0/process/{id}/".replace(/{format}/g,"xml").replace("{" + "id" + "}", getApiInvoker().escapeString(id));

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
        token.completionEventType = "process_read";

        token.returnType = InlineResponse2004;
        return requestId;

    }
}
}
