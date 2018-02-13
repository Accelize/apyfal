package io.swagger.client.model {


    [XmlRootNode(name="InlineResponse2001")]
    public class InlineResponse2001 {
        /*  */
        [XmlElement(name="id")]
        public var id: String = null;
        /*  */
        [XmlElement(name="url")]
        public var url: String = null;
        /*  */
        [XmlElement(name="inerror")]
        public var inerror: Boolean = false;
        /*  */
        [XmlElement(name="processed_date")]
        public var processedDate: String = null;
        /*  */
        [XmlElement(name="parametersresult")]
        public var parametersresult: String = null;
        /*  */
        [XmlElement(name="errorcode")]
        public var errorcode: String = null;
        /*  */
        [XmlElement(name="processed")]
        public var processed: Boolean = false;

    public function toString(): String {
        var str: String = "InlineResponse2001: ";
        str += " (id: " + id + ")";
        str += " (url: " + url + ")";
        str += " (inerror: " + inerror + ")";
        str += " (processedDate: " + processedDate + ")";
        str += " (parametersresult: " + parametersresult + ")";
        str += " (errorcode: " + errorcode + ")";
        str += " (processed: " + processed + ")";
        return str;
    }

}

}
