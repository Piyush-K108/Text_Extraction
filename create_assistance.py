from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

openai_key = os.getenv('API_KEY')
client = OpenAI(api_key=openai_key)


assistant = client.beta.assistants.create(
  name="Financial Analyst Assistant",
  instructions=(
    "You are an expert financial analyst who can extract data from files for business-related documents. "
    "Your task is to return the extracted data in the following JSON format: "
    "{ 'file_type': <type_of_file>, 'data': {<extracted_data>} }. "
    "Identify the file type (e.g., 'invoice', 'ledger','Cash Flow Statement') and extract the whole data points from the file don't exclude anything."
    "Ensure the JSON is concise, structured, and includes nothing beyond the 'file_type' and 'data'."
  ),
  model="gpt-4o",
  tools=[{"type": "file_search"}],
)

print(assistant)