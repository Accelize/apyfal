package io.swagger.client.model {

import io.swagger.common.ListWrapper;

    public class InlineResponse200ResultsList implements ListWrapper {
        // This declaration below of _inline_response_200_results_obj_class is to force flash compiler to include this class
        private var _inlineResponse200Results_obj_class: io.swagger.client.model.InlineResponse200Results = null;
        [XmlElements(name="inlineResponse200Results", type="io.swagger.client.model.InlineResponse200Results")]
        public var inlineResponse200Results: Array = new Array();

        public function getList(): Array{
            return inlineResponse200Results;
        }

}

}
