from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.chains import LLMChain
from tenacity import retry, stop_after_attempt, wait_exponential
    
def parse_output_format(output_format_prompt):
    response_schemas = []
    
    for line in output_format_prompt.split("\n"):
        if ":" in line:
            name, schema_str = line.split(":", 1)
            name = name.strip()                
            
            schema_str = schema_str.strip()
            #print(schema_str)
            
            if "(" in schema_str:
                schema_type, args_str = schema_str.split("(", 1)
                schema_type = schema_type.strip()
                schema_args = [arg.strip() for arg in args_str.strip(")").split(",")]
            else:
                schema_type = schema_str
                schema_args = []

            response_schemas.append(ResponseSchema(name=name, description=','.join(schema_args), type=schema_type))
            #print(output_format_prompt)

    return response_schemas

class GPTApi:
    def __init__(self, api_key, model_name):
        self.llm = ChatOpenAI(openai_api_key=api_key, model_name=model_name, temperature=0.0)

    #@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=60))
    def send_request(self, data, output_format_prompt=None):
        try:
            if output_format_prompt is not None:
                response_schemas = parse_output_format(output_format_prompt)
                output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    
                prompt = ChatPromptTemplate.from_messages([
                    HumanMessagePromptTemplate.from_template("{instruction_prompt}\n\n{input_data}\n\nOutput Format:\n{output_format_prompt}\nThe output must be in JSON format.")
                    ])
                
                chain = LLMChain(llm=self.llm, prompt=prompt, output_parser=output_parser)        
    
                response = chain.run({
                        "instruction_prompt": data["instruction_prompt"],
                        "input_data": data["input_data"],
                        "output_format_prompt": data["output_format_prompt"]
                    })
                return response
                
            else:
                prompt = ChatPromptTemplate.from_messages([
                    HumanMessagePromptTemplate.from_template("{instruction_prompt}\n\n{input_data}")
                    ])            
                chain = LLMChain(llm=self.llm, prompt=prompt)        
                response = chain.run({
                        "instruction_prompt": data["instruction_prompt"],
                        "input_data": data["input_data"],                    
                    })
                response_return = {}
                response_return['response'] = response
    
                return response_return
        except Exception as e:
            response_return = {"error": f'에러가 발생했습니다. Maitec.Lab@gmail.com으로 문의하여 주시기 바랍니다. 에러 내용: {e}'}
            return response_return

