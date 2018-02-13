package io.swagger.client.model {

import io.swagger.common.ListWrapper;

    public class InlineResponse2003ResultsList implements ListWrapper {
        // This declaration below of _inline_response_200_3_results_obj_class is to force flash compiler to include this class
        private var _inlineResponse2003Results_obj_class: io.swagger.client.model.InlineResponse2003Results = null;
        [XmlElements(name="inlineResponse2003Results", type="io.swagger.client.model.InlineResponse2003Results")]
        public var inlineResponse2003Results: Array = new Array();

        public function getList(): Array{
            return inlineResponse2003Results;
        }

}

}
