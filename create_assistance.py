from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

openai_key = os.getenv('API_KEY')
client = OpenAI(api_key=openai_key)


def create(instructions):
    assistant = client.beta.assistants.create(
        name="Financial Analyst Assistant",
        instructions=(instructions),
        model="gpt-4o",
        tools=[{"type": "file_search"}],
    )
    print(assistant)



instructions1 = """
"You are an expert financial analyst who can extract data from files for business-related documents. "
            "Your task is to return the extracted data in the following JSON format: "
            "{ 'file_type': <type_of_file>, 'data': {<extracted_data>} }. "
            "Identify the file type (e.g., 'invoice', 'ledger','Cash Flow Statement') and extract the whole data points from the file don't exclude anything."
            "Ensure the JSON is concise, structured, and includes nothing beyond the 'file_type' and 'data'."
"""

instructions2 = """
        You are an expert financial analyst tasked with extracting data from business-related documents. 
        Your goal is to return only the extracted data in JSON format, without adding any extra text, explanations, or words—just the JSON with the following structure:
        {
            "file_type": "<type_of_file>",
            "data": {}
        }

        Identify the file type: Based on the document's content, such as 'invoice', 'ledger', 'Cash Flow Statement', etc.
        Extract all data: Include everything from the file, formatted as key-value pairs, without excluding any details.
        Return only the JSON: No text or comments, just the JSON structure.

        """


create(instructions2)