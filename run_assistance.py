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


def json_to_file(json_data, vector_id, thread_id, run_id, output_file='Json_output.json'):
    try:
        # Add additional fields to JSON data
        json_data['vector_id'] = vector_id
        json_data['thread_id'] = thread_id
        json_data['run_id'] = run_id

        # Check if the file exists
        file_exists = os.path.isfile(output_file)

        # Open the file in append or write mode based on its existence
        with open(output_file, 'a' if file_exists else 'w') as f:
            # If appending, add a newline before appending new JSON data
            if file_exists:
                f.write("\n")
            # Write the updated JSON data
            json.dump(json_data, f, indent=4)

        print(f"Data successfully written to {output_file}")

    except Exception as e:
        print(f"Error occurred: {str(e)}")


def json_to_csv(json_data, vector_id, thread_id, run_id, output_file='Json_output.csv'):
    try:
        def flatten_json(data, parent_key='', sep='_'):
            items = []
            for k, v in data.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_json(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)

        # Flatten the JSON data
        flat_data = flatten_json(json_data)

        # Convert to DataFrame
        df = pd.DataFrame([flat_data])
        df['vector_store_id'] = vector_id
        df['thread_id'] = thread_id
        df['run_id'] = run_id

        # Check if the file exists
        file_exists = os.path.isfile(output_file)

        # Save to CSV, appending if file exists
        df.to_csv(output_file, mode='a', header=not file_exists, index=False)

        return 1
    except Exception as e:
        print(f"Error in json_to_csv: {str(e)}")
        save_output_to_txt(
            f"Error in json_to_csv: {str(e)}", file_path="error_log.txt")


def save_output_to_txt(output_data, file_path="output/output_file.txt"):
    try:
        with open(file_path, "w") as file:
            file.write(str(output_data))
    except Exception as e:
        print(f"Error saving to text file: {str(e)}")


def process_files(file_paths):    
   
    try:
        # Load API key and Assistant ID from environment variables
        openai_key = os.getenv('API_KEY')
        assistant_id = os.getenv('ASSISTANT_ID')

        # Initialize OpenAI client
        client = OpenAI(api_key=openai_key)

        # Create a vector store called "File Data Extractor"
        vector_store = client.beta.vector_stores.create(
            name="File Data Extractor")

        # Ready the files for upload to OpenAI
        file_streams = [open(path, "rb") for path in file_paths]

        # Upload files to the vector store and poll for completion
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            files=file_streams
        )
        print(f"vectore_store_id is : {vector_store.id} ")

        # Update the assistant with vector store information
        assistant = client.beta.assistants.update(
            assistant_id=assistant_id,
            tool_resources={"file_search": {
                "vector_store_ids": [vector_store.id]}}
        )
        print("Assistant updated with vector storage.")

        # Create a thread for conversation and attach the file to the message
        thread = client.beta.threads.create()
        print(f'Your thread ID is: {thread.id}\n')

        # Send the user message to extract JSON data from the file
        text = "Just follow the instructions given and extract everything, don't leave any data from the file; preserve the structure of the data and send unique values without adding any duplicate entries"
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
        # Retrieve messages from the assistant's response
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

            json_to_file(json_data, output_file=f'{thread.id}_output_MY.json',
                         vector_id=vector_store.id, thread_id=thread.id, run_id=run.id)

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

            # Save JSON to CSV
            # json_to_csv(json_data, output_file=f'{thread.id}_output.csv', vector_id=vector_store.id, thread_id=thread.id,run_id=run.id)
            json_to_file(json_data, output_file=f'{thread.id}_output.json',
                         vector_id=vector_store.id, thread_id=thread.id, run_id=run.id)
            print("JSON data has been saved to CSV.")

            # Save JSON content to a text file
            save_output_to_txt(json_data, file_path="output.txt")
            print("JSON data has been saved to output.txt.")

            return json_data
        else:
            print("No messages content found.")
            return None

    except Exception as e:
        print(f"Error in process_files: {str(e)}")
        save_output_to_txt(
            f"Error in process_files: {str(e)}", file_path="error_log.txt")
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


def process_code_file(file_path, file_name):
    openai_key = os.getenv('API_KEY')
    assistant_id = os.getenv('ASSISTANT_ID')

    # Initialize OpenAI client
    client = OpenAI(api_key=openai_key)

    file_id = ''

    try:
        # List existing files
        files = client.files.list()

        # Check if the file already exists
        for file in files.data:

            if file.filename == file_name:
                file_id = file.id
                print(f"File found: {file_id} ,{file.filename}")
                break
        else:
            # File not found, upload the new file
            print("Uploading new file...")
            print(file_path)
            # with open(file_path, "rb") as f:
            #     response = client.files.create(
            #     file=open(file_path, "rb"),
            #     purpose="assistants"
            #     )
            # file_id = response['id']
            # print(f"Uploaded file ID: {file_id}")

    except Exception as e:
        print(f"Error: {str(e)}")

    return file_id


def preprocess_image(image_path):
    """
    Preprocess the image to enhance text clarity for better OCR performance.
    """
    # Open the image file
    image = Image.open(image_path)
    # Convert the image to grayscale
    image = image.convert('L')
    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)
    # Sharpen the image
    image = image.filter(ImageFilter.SHARPEN)
    return image


def process_image_file(image_path):
    """
    Extracts text with layout structure preserved using Tesseract's layout control.
    """
    image = preprocess_image(image_path)

    # Use layout-preserving PSM modes in Tesseract (e.g., --psm 4 for column detection)
    # Try psm 4, psm 6, or psm 12 for structured layouts
    raw_text = image_to_string(image, lang='eng', config='--psm 4')

    file_name_without_ext = os.path.splitext(os.path.basename(image_path))[0]
    directory = 'images'
    output_txt_path = os.path.join(directory, f"{file_name_without_ext}.txt")

    # Create the directory if it does not exist
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(output_txt_path, "w") as f:
        f.write(raw_text)

    print(f"Extracted text saved to: {output_txt_path}")
    return output_txt_path



