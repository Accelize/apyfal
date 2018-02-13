/* 
 * Accelize Accelerator WS
 *
 * No descripton provided (generated by Swagger Codegen https://github.com/swagger-api/swagger-codegen)
 *
 * OpenAPI spec version: 1.0
 * 
 * Generated by: https://github.com/swagger-api/swagger-codegen.git
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package swagger

type InlineResponse2003Results struct {

	// If needed, file to be processed by the accelerator.
	Datafile string `json:"datafile,omitempty"`

	// All parameters need for the excution in JSON format : {     \"AcceleratorParam1\":\"value1\",    \"AcceleratorParam2\":\"value2\",    \"AcceleratorParam3\":\"value3\"}
	Parameters string `json:"parameters,omitempty"`

	// 
	Id string `json:"id,omitempty"`

	// 
	Url string `json:"url,omitempty"`

	// 
	Inerror bool `json:"inerror,omitempty"`

	// 
	Parametersresult string `json:"parametersresult,omitempty"`

	// 
	ProcessedDate string `json:"processed_date,omitempty"`

	// If needed, file  processed by the accelerator.
	Datafileresult string `json:"datafileresult,omitempty"`

	// 
	Processed bool `json:"processed,omitempty"`

	// Id of the configuration to use for this process
	Configuration string `json:"configuration,omitempty"`
}
