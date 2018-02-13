package io.swagger.client.model {


    [XmlRootNode(name="InlineResponse200Results")]
    public class InlineResponse200Results {
        /* If needed, file to be processed by the accelerator. */
        [XmlElement(name="datafile")]
        public var datafile: String = null;
        /*  */
        [XmlElement(name="used")]
        public var used: Boolean = false;
        /* All parameters need for the excution in JSON format : {     \&quot;AcceleratorParam1\&quot;:\&quot;value1\&quot;,    \&quot;AcceleratorParam2\&quot;:\&quot;value2\&quot;,    \&quot;AcceleratorParam3\&quot;:\&quot;value3\&quot;} */
        [XmlElement(name="parameters")]
        public var parameters: String = null;
        /*  */
        [XmlElement(name="created")]
        public var created: String = null;
        /*  */
        [XmlElement(name="url")]
        public var url: String = null;
        /*  */
        [XmlElement(name="inerror")]
        public var inerror: Boolean = false;
        /*  */
        [XmlElement(name="parametersresult")]
        public var parametersresult: String = null;
        /*  */
        [XmlElement(name="errorcode")]
        public var errorcode: String = null;
        /*  */
        [XmlElement(name="processed_date")]
        public var processedDate: String = null;
        /*  */
        [XmlElement(name="processed")]
        public var processed: Boolean = false;
        /*  */
        [XmlElement(name="id")]
        public var id: String = null;

    public function toString(): String {
        var str: String = "InlineResponse200Results: ";
        str += " (datafile: " + datafile + ")";
        str += " (used: " + used + ")";
        str += " (parameters: " + parameters + ")";
        str += " (created: " + created + ")";
        str += " (url: " + url + ")";
        str += " (inerror: " + inerror + ")";
        str += " (parametersresult: " + parametersresult + ")";
        str += " (errorcode: " + errorcode + ")";
        str += " (processedDate: " + processedDate + ")";
        str += " (processed: " + processed + ")";
        str += " (id: " + id + ")";
        return str;
    }

}

}
