from openai import OpenAI
import os
import pandas as pd  
from dotenv import load_dotenv

load_dotenv()

def json_to_csv(json_data,vector_id,thread_id, output_file='output.csv'):
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
    df['vectore_store_id']=vector_id
    df['thread_id']=thread_id
    # Check if the file exists
    file_exists = os.path.isfile(output_file)

    # Save to CSV, appending if file exists
    df.to_csv(output_file, mode='a', header=not file_exists, index=False)

    return 1

def process_files(file_paths):
    # Load API key and Assistant ID from environment variables
    openai_key = os.getenv('API_KEY')
    assistant_id = os.getenv('ASSISTANT_ID')

    # Initialize OpenAI client
    client = OpenAI(api_key=openai_key)

    # Create a vector store called "File Data Extractor"
    vector_store = client.beta.vector_stores.create(name="File Data Extractor")

    # Ready the files for upload to OpenAI
    file_streams = [open(path, "rb") for path in file_paths]

    # Upload files to the vector store and poll for completion
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, 
        files=file_streams
    )
    print(f"File batch upload status: {file_batch.status}")

    # Update the assistant with vector store information
    assistant = client.beta.assistants.update(
        assistant_id=assistant_id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
    )
    print("Assistant updated with vector storage.")

    # Create a thread for conversation and attach the file to the message
    thread = client.beta.threads.create()
    print(f'Your thread ID is: {thread.id}\n')

    # Send the user message to extract JSON data from the file
    text = 'Give me json extracted from file'
    messages = client.beta.threads.messages.create(
        thread_id=thread.id,
        role='user',
        content=text
    )

    # Poll for the assistant's response
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    token_usage = run.token_usage

    # Retrieve messages from the assistant's response
    messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
    messages_content = messages[0].content[0].text

    # Print the extracted JSON content
    print("Extracted JSON content:\n", messages_content)

    # Save the extracted JSON to CSV
    json_data = eval(messages_content)  # Convert JSON string to dictionary

    json_data['token_usage'] = {
        "prompt_tokens": token_usage.prompt_tokens,
        "completion_tokens": token_usage.completion_tokens,
        "total_tokens": token_usage.total_tokens
    }

    json_to_csv(json_data, output_file='output.csv',vector_id=vector_store.id,thread_id=thread.id)
    print("JSON data has been saved to CSV.")

    # The thread now has a vector store with the file in its tool resources
    print(f"Vector store resources: {thread.tool_resources.file_search}")

    return json_data     
