using System;
using System.Text;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.Serialization;
using Newtonsoft.Json;

namespace IO.Swagger.Model {

  /// <summary>
  /// 
  /// </summary>
  [DataContract]
  public class InlineResponse2001 {
    /// <summary>
    /// 
    /// </summary>
    /// <value></value>
    [DataMember(Name="id", EmitDefaultValue=false)]
    [JsonProperty(PropertyName = "id")]
    public string Id { get; set; }

    /// <summary>
    /// 
    /// </summary>
    /// <value></value>
    [DataMember(Name="url", EmitDefaultValue=false)]
    [JsonProperty(PropertyName = "url")]
    public string Url { get; set; }

    /// <summary>
    /// 
    /// </summary>
    /// <value></value>
    [DataMember(Name="inerror", EmitDefaultValue=false)]
    [JsonProperty(PropertyName = "inerror")]
    public bool? Inerror { get; set; }

    /// <summary>
    /// 
    /// </summary>
    /// <value></value>
    [DataMember(Name="processed_date", EmitDefaultValue=false)]
    [JsonProperty(PropertyName = "processed_date")]
    public string ProcessedDate { get; set; }

    /// <summary>
    /// 
    /// </summary>
    /// <value></value>
    [DataMember(Name="parametersresult", EmitDefaultValue=false)]
    [JsonProperty(PropertyName = "parametersresult")]
    public string Parametersresult { get; set; }

    /// <summary>
    /// 
    /// </summary>
    /// <value></value>
    [DataMember(Name="errorcode", EmitDefaultValue=false)]
    [JsonProperty(PropertyName = "errorcode")]
    public string Errorcode { get; set; }

    /// <summary>
    /// 
    /// </summary>
    /// <value></value>
    [DataMember(Name="processed", EmitDefaultValue=false)]
    [JsonProperty(PropertyName = "processed")]
    public bool? Processed { get; set; }


    /// <summary>
    /// Get the string presentation of the object
    /// </summary>
    /// <returns>String presentation of the object</returns>
    public override string ToString()  {
      var sb = new StringBuilder();
      sb.Append("class InlineResponse2001 {\n");
      sb.Append("  Id: ").Append(Id).Append("\n");
      sb.Append("  Url: ").Append(Url).Append("\n");
      sb.Append("  Inerror: ").Append(Inerror).Append("\n");
      sb.Append("  ProcessedDate: ").Append(ProcessedDate).Append("\n");
      sb.Append("  Parametersresult: ").Append(Parametersresult).Append("\n");
      sb.Append("  Errorcode: ").Append(Errorcode).Append("\n");
      sb.Append("  Processed: ").Append(Processed).Append("\n");
      sb.Append("}\n");
      return sb.ToString();
    }

    /// <summary>
    /// Get the JSON string presentation of the object
    /// </summary>
    /// <returns>JSON string presentation of the object</returns>
    public string ToJson() {
      return JsonConvert.SerializeObject(this, Formatting.Indented);
    }

}
}
