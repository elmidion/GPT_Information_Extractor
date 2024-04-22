import streamlit as st
from file_handler import FileHandler
from gpt_api import GPTApi, parse_output_format
from excel_generator import ExcelGenerator
from docx import Document
import io
from zipfile import BadZipFile
import os
from datetime import datetime
import pandas as pd

class Popup:
    def __init__(self, title, content, image=None):
        self.title = title
        self.content = content
        self.image = image
        self.show_popup = st.session_state.get(f"{title}_show_popup", False)
        self.container = st.container()

    def render(self):
        toggle_button = st.button(f"{self.title}")
        if toggle_button:
            self.show_popup = not self.show_popup
            st.session_state[f"{self.title}_show_popup"] = self.show_popup

        with self.container:
            if self.show_popup:
                if self.image:
                    st.image(self.image)
                st.write(self.content)

def read_file_content(file):
    file_extension = file.name.split(".")[-1].lower()
    
    if file_extension == "docx":
        try:
            document = Document(io.BytesIO(file.read()))
            return "\n".join([p.text for p in document.paragraphs])
        except BadZipFile:
            st.warning("The uploaded .docx file is not a valid ZIP file. Please check the file and try again.")
            return ""
    elif file_extension == "txt":
        return file.read().decode("utf-8")
    else:
        st.warning(f"Unsupported file format: {file_extension}. Please upload a .docx or .txt file.")
        return ""

def main():
    st.title("GPT Information Extractor")
    st.markdown("<small>made by MAITEC.Lab</small>", unsafe_allow_html=True)
    popup2 = Popup("사용 설명", "오류나 문의사항은 MAITEC.Lab@gmail.com 으로 보내주시면 감사하겠습니다.", image="GPT_Information_Extractor_설명.png")
    popup2.render()
    
    api_key = st.text_input("Enter GPT API Key (https://platform.openai.com/api-keys)", type="password")
    #model_name = st.selectbox("Select GPT Model", ["gpt-3.5-turbo", "gpt-4", "gpt-4-32k"])
    model_name = st.selectbox("Select GPT Model", ["gpt-3.5-turbo", "gpt-4"])
    instruction_file = st.file_uploader("Upload Instruction Prompt File (.docx)")    
    
    output_format_file = st.file_uploader("Upload Output Format Prompt File (.docx)")
    output_format_description ="""
                            *Output format prompt 형식 예시\n
                                Name: string
                                Blood type: string(A,B,O,AB)
                                Age: integer
                                Height: float
                                Married: boolean
                            """
    Data_type_description ="""
                            *string <- 문자열 / integer <- 정수형 / float <- 소수형 / boolean <- True or False만 갖는 논리형
                            """
    popup1 = Popup("Output format prompt 형식 예시", output_format_description + Data_type_description)
    popup1.render()

    if output_format_file is not None:
        output_format_prompt = read_file_content(output_format_file)
        
        # Parse the output format prompt
        response_schemas = parse_output_format(output_format_prompt)
        
        # Create a list to store the rows
        rows = []
        
        for schema in response_schemas:
            row = {
                "Column Name": schema.name,
                "Values": schema.description,
                "Data Type": schema.type
            }
            rows.append(row)
        
        # Create a DataFrame from the rows
        df = pd.DataFrame(rows)
        
        # Display the parsed response schemas as a table
        st.subheader("Parsed Output Format")
        st.table(df)
    else:
        output_format_prompt = None

    data_file = st.file_uploader("Upload Data Excel File (.xlsx)")    
    if data_file is not None:
        file_handler = FileHandler(data_file)
        column_names = file_handler.get_column_names()
        
        data_df = file_handler.get_data_df()
        id_column = st.selectbox("Select ID Column (인덱스용 컬럼)", [""] + column_names)
        if id_column:
            st.subheader("ID Column Preview (첫 세 줄)")
            st.write(data_df[id_column].head(3))            
            
        input_column = st.selectbox("Select Input Data Column (정보 추출할 컬럼 - 현재 한 컬럼만 가능)", [""] + column_names)
        if input_column:
            st.subheader("Input Data Column Preview (첫 세 줄)")
            st.write(data_df[input_column].head(3))
    else:
        id_column = st.selectbox("Select ID Column (인덱스용 컬럼)", [""])
        input_column = st.selectbox("Select Input Data Column (정보 추출할 컬럼 - 현재 한 컬럼만 가능)", [""])
    
    if st.button("Submit"):
        if api_key and instruction_file and data_file and id_column and input_column:
            instruction_prompt = read_file_content(instruction_file)
            #output_format_prompt = read_file_content(output_format_file)
            
            extracted_data = file_handler.extract_data(id_column, input_column, instruction_prompt, output_format_prompt)
            
            gpt_api = GPTApi(api_key, model_name)

            # 진행바 추가
            total_requests = len(extracted_data)
            progress_bar = st.progress(0)

            start_time = datetime.now()

            responses = []
            for i, data in enumerate(extracted_data):
                try:
                    response = gpt_api.send_request(data, output_format_prompt)
                except Exception as e:
                    #print(e)
                    st.error(f'에러가 발생했습니다. Maitec.Lab@gmail.com으로 문의하여 주시기 바랍니다. 에러 내용: {e}', icon="🚨")
                    response = {}
                responses.append({
                    "id": data["id"],
                    "response": response
                })

                # 진행 상황 업데이트
                progress_bar.progress((i + 1) / total_requests)

            # 진행바 완료
            progress_bar.empty()

            end_time = datetime.now()  # 끝 시간 기록
            elapsed_time = end_time - start_time  # 걸린 시간 계산
            
            #responses = gpt_api.send_requests(extracted_data, response_schemas)

            print("GPT응답샘플: ", responses[0])
            
            excel_generator = ExcelGenerator(responses, id_column)
            output_file = excel_generator.generate_excel()
            
            # Generate the output file name
            current_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file_name = f"{os.path.splitext(data_file.name)[0]}_{model_name}_responses_{current_datetime}.xlsx"
            
            st.download_button(
                label="Download Output Excel",
                data=output_file,
                file_name=output_file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.success(f"작업이 완료되었습니다. 위 버튼을 눌러 결과파일을 다운로드하시기 바랍니다. 걸린 시간: {elapsed_time}") 
        else:
            st.warning("Please provide all the required inputs.")



if __name__ == "__main__":
    main()
