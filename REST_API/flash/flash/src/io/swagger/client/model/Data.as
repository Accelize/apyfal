package io.swagger.client.model {

import flash.filesystem.File;

    [XmlRootNode(name="Data")]
    public class Data {
        /* If needed, file to be processed by the accelerator. */
        [XmlElement(name="datafile")]
        public var datafile: File = NaN;
        /* Id of the configuration to use for this process */
        [XmlElement(name="configuration")]
        public var configuration: String = null;
        /* All parameters need for the excution in JSON format : {     \&quot;AcceleratorParam1\&quot;:\&quot;value1\&quot;,    \&quot;AcceleratorParam2\&quot;:\&quot;value2\&quot;,    \&quot;AcceleratorParam3\&quot;:\&quot;value3\&quot;} */
        [XmlElement(name="parameters")]
        public var parameters: String = null;

    public function toString(): String {
        var str: String = "Data: ";
        str += " (datafile: " + datafile + ")";
        str += " (configuration: " + configuration + ")";
        str += " (parameters: " + parameters + ")";
        return str;
    }

}

}
