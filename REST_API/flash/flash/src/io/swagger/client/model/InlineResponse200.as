package io.swagger.client.model {

import io.swagger.client.model.InlineResponse200Results;

    [XmlRootNode(name="InlineResponse200")]
    public class InlineResponse200 {
        /*  */
        [XmlElement(name="count")]
        public var count: Number = NaN;
        /*  */
        [XmlElement(name="previous")]
        public var previous: String = null;
        /*  */
        // This declaration below of _results_obj_class is to force flash compiler to include this class
        private var _results_obj_class: Array = null;
        [XmlElementWrapper(name="results")]
        [XmlElements(name="results", type="Array")]
                public var results: Array = new Array();
        /*  */
        [XmlElement(name="next")]
        public var next: String = null;

    public function toString(): String {
        var str: String = "InlineResponse200: ";
        str += " (count: " + count + ")";
        str += " (previous: " + previous + ")";
        str += " (results: " + results + ")";
        str += " (next: " + next + ")";
        return str;
    }

}

}
