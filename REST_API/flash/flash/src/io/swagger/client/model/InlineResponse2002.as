package io.swagger.client.model {

import io.swagger.client.model.InlineResponse2002Results;

    [XmlRootNode(name="InlineResponse2002")]
    public class InlineResponse2002 {
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
        var str: String = "InlineResponse2002: ";
        str += " (count: " + count + ")";
        str += " (previous: " + previous + ")";
        str += " (results: " + results + ")";
        str += " (next: " + next + ")";
        return str;
    }

}

}
