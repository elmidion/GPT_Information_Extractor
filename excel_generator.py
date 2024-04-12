import io
import pandas as pd

class ExcelGenerator:
    def __init__(self, responses, id_column):
        self.responses = responses
        self.id_column = id_column
    
    def generate_excel(self):
        data = []
        for response in self.responses:
            row = response["response"]
            row[self.id_column] = response["id"]
            data.append(row)
        
        print(data)

        df = pd.DataFrame(data)
        
        # Reorder columns to make the ID column first
        columns = [self.id_column] + [col for col in df.columns if col != self.id_column]
        df = df[columns]
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Output")
        output.seek(0)
        
        return output.getvalue()