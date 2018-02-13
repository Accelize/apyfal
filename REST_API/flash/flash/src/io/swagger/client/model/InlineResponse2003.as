package io.swagger.client.model {


    [XmlRootNode(name="InlineResponse2003")]
    public class InlineResponse2003 {
        /* If needed, file to be processed by the accelerator. */
        [XmlElement(name="datafile")]
        public var datafile: String = null;
        /*  */
        [XmlElement(name="id")]
        public var id: String = null;
        /* All parameters need for the excution in JSON format : {     \&quot;AcceleratorParam1\&quot;:\&quot;value1\&quot;,    \&quot;AcceleratorParam2\&quot;:\&quot;value2\&quot;,    \&quot;AcceleratorParam3\&quot;:\&quot;value3\&quot;} */
        [XmlElement(name="parameters")]
        public var parameters: String = null;
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
        [XmlElement(name="processed_date")]
        public var processedDate: String = null;
        /* If needed, file  processed by the accelerator. */
        [XmlElement(name="datafileresult")]
        public var datafileresult: String = null;
        /*  */
        [XmlElement(name="processed")]
        public var processed: Boolean = false;
        /* Id of the configuration to use for this process */
        [XmlElement(name="configuration")]
        public var configuration: String = null;

    public function toString(): String {
        var str: String = "InlineResponse2003: ";
        str += " (datafile: " + datafile + ")";
        str += " (id: " + id + ")";
        str += " (parameters: " + parameters + ")";
        str += " (url: " + url + ")";
        str += " (inerror: " + inerror + ")";
        str += " (parametersresult: " + parametersresult + ")";
        str += " (processedDate: " + processedDate + ")";
        str += " (datafileresult: " + datafileresult + ")";
        str += " (processed: " + processed + ")";
        str += " (configuration: " + configuration + ")";
        return str;
    }

}

}
