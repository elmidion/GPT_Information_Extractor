import pandas as pd

class FileHandler:
    def __init__(self, data_file):
        self.data_file = data_file
    
    def get_column_names(self):
        data_df = pd.read_excel(self.data_file)
        return list(data_df.columns)
    
    def extract_data(self, id_column, input_column, instruction_prompt, output_format_prompt):
        data_df = pd.read_excel(self.data_file, engine='openpyxl')
        
        extracted_data = []
        for _, row in data_df.iterrows():
            extracted_data.append({
                "id": row[id_column],
                "input_data": row[input_column],
                "instruction_prompt": instruction_prompt,
                "output_format_prompt": output_format_prompt
            })
        
        return extracted_data
    
    def get_data_df(self):
        return pd.read_excel(self.data_file)
