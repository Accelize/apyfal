package io.swagger.client.model {

import io.swagger.common.ListWrapper;

    public class InlineResponse2002ResultsList implements ListWrapper {
        // This declaration below of _inline_response_200_2_results_obj_class is to force flash compiler to include this class
        private var _inlineResponse2002Results_obj_class: io.swagger.client.model.InlineResponse2002Results = null;
        [XmlElements(name="inlineResponse2002Results", type="io.swagger.client.model.InlineResponse2002Results")]
        public var inlineResponse2002Results: Array = new Array();

        public function getList(): Array{
            return inlineResponse2002Results;
        }

}

}
