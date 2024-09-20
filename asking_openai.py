import json
from openai import OpenAI
import os
import pandas as pd
from dotenv import load_dotenv
import re
import pytesseract
import concurrent.futures
from pytesseract import image_to_string
from PIL import Image, ImageEnhance, ImageFilter
import requests
import concurrent.futures
from pytesseract import image_to_string
import os
from io import BytesIO
load_dotenv()
pytesseract.pytesseract.tesseract_cmd = 'tesseract'


def json_to_file(json_data, txt, file_id, thread_id, run_id, output_file='Json_output.json'):
    try:
        # Add additional fields to JSON data
        json_data['file_id'] = file_id
        json_data['orignal_txt'] = txt
        json_data['thread_id'] = thread_id
        json_data['run_id'] = run_id

        # Check if the file exists
        file_exists = os.path.isfile(output_file)

        # Open the file in append or write mode with UTF-8 encoding
        with open(output_file, 'a' if file_exists else 'w', encoding='utf-8') as f:
            # If appending, add a newline before appending new JSON data
            if file_exists:
                f.write("\n")
            # Write the updated JSON data with ensure_ascii=False for proper encoding
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        print(f"Data successfully written to {output_file}")

    except Exception as e:
        print(f"Error occurred: {str(e)}")



def process_questions_files(file_paths,txt):
    try:
        # Load API key and Assistant ID from environment variables
        openai_key = os.getenv('API_KEY')
        assistant_id = os.getenv('ASSISTANT_ID3')

        # Initialize OpenAI client
        client = OpenAI(api_key=openai_key)

        file = client.files.create(
            file=open(file_paths, "rb"),
            purpose='assistants'
        )

        assistant = client.beta.assistants.update(
            assistant_id=assistant_id,
            tool_resources={
                "code_interpreter": {
                    "file_ids": [file.id]
                }
            }
        )
        print(f'Your File ID is: {file.id}\n')
        # Create a thread for conversation and attach the file to the message
        thread = client.beta.threads.create()
        print(f'Your thread ID is: {thread.id}\n')

        # Send the user message to extract JSON data from the file
       
        text = f"Just follow the instructions given, and my question is: {txt}. Please provide the data and insights based on the question in josn object only."

        messages = client.beta.threads.messages.create(
            thread_id=thread.id,
            role='user',
            content=text,

        )

        # Poll for the assistant's response
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant_id,

        )
        print(f'Your Run object is: {run}\n')
        print(f'Your Run ID is: {run.id}\n')

        token_usage = run.usage
        messages = list(client.beta.threads.messages.list(
            thread_id=thread.id, run_id=run.id))
        try:
            print("My Json")
            json = messages[0].content
            json_data = eval(json)

            json_data['token_usage'] = {
                "prompt_tokens": token_usage.prompt_tokens,
                "completion_tokens": token_usage.completion_tokens,
                "total_tokens": token_usage.total_tokens
            }
            json_to_file(json_data,txt=txt, output_file=f'{thread.id}_output_MY.json',
                         file_id=file.id, thread_id=thread.id, run_id=run.id)

        except Exception as e:
            print("My Error", e)

        if len(messages) > 0 and len(messages[0].content) > 0:
            messages_content = messages[0].content[0].text

            # Print the extracted JSON content

            for content_block in messages[0].content:
                if hasattr(content_block, 'text') and hasattr(content_block.text, 'value'):
                    messages_content = content_block.text.value
                    break  # Exit the loop once the text is found

            print("Extracted JSON content:\n", messages_content)

            try:
                cleaned_json_string = messages_content.strip("```json").strip()
                cleaned_json_string = cleaned_json_string.replace(
                    'null', 'None')
                json_data = eval(cleaned_json_string)
            except Exception as e:
                print("Error", e)
                json_data = message_to_json(messages_content)

            json_data['token_usage'] = {
                "prompt_tokens": token_usage.prompt_tokens,
                "completion_tokens": token_usage.completion_tokens,
                "total_tokens": token_usage.total_tokens
            }

            json_to_file(json_data,txt=txt, output_file=f'{thread.id}_output.json',
                         file_id=file.id, thread_id=thread.id, run_id=run.id)

            return json_data
        else:
            print("No messages content found.")
            return None

    except Exception as e:
        print(f"Error in process_files: {str(e)}")
        print(
            f"Error in process_files: {str(e)}")
        return None


def message_to_json(messages_content):
    json_match = re.search(r"```json(.*?)```", messages_content, re.DOTALL)

    if json_match:
        json_string = json_match.group(1).strip()
        json_string = json_string.replace('null', 'None')

        # Optionally, you can load this string into a dictionary
        print(json_string)
        try:
            json_data = eval(json_string)
        except Exception as e:
            try:
                json_data = json.loads(json_string)
                print(f"Error parsing JSON: {str(e)}")
            except:
                print(f"Error parsing JSON2: {str(e)}")
    else:
        print("No JSON found in the content.")
    return json_data
