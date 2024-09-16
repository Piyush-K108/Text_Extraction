from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

openai_key = os.getenv('API_KEY')
client = OpenAI(api_key=openai_key)


def create(instructions):
    assistant = client.beta.assistants.create(
        name="Financial Analyst Assistant2",
        instructions=(instructions),
        model="gpt-4o",
        tools=[{"type": "file_search"}, {"type": "code_interpreter"}],
    )
    print(assistant)



instructions = """
        You are an expert financial analyst tasked with extracting data from business-related documents. 
        Your goal is to return only the extracted data in JSON format, without adding any extra text, explanations, or words—just the JSON with the following structure:
       {
            "file_type": "<type_of_file>",
            "data": {
                "Total_Amount": "<amount>",
                "Payment_Date": "<date>",
                "Payment_Reference_Number": "<payment_reference_number>",
                "Invoice_Number": "<invoice_number>",
                "Payment_Currency": "<payment_currency>",
                "Partner_details": "<partner_details>",
                "Bank_Account_Details": "<bank_account_details>",
                "additional_fields": {
                    "<field_name>": "<value>",
                    "<field_name>": "<value>",
                }
            }
        }

        Identify the file type: Based on the document's content.
        Extract all data: Include everything from the file, formatted as key-value pairs, without excluding any details.
        Return only the JSON: No text or comments, just the JSON structure.
"""

create(instructions)
