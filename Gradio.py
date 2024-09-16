import json
from run_assistance import json_to_csv, process_files, save_output_to_txt, process_code_file, process_image_file
import gradio as gr
import email
from email import policy
import os
import csv
import pandas as pd
import json
import numpy as np


def table_to_json(input_file):
    try:
        print(input_file)

        # Check file extension and read accordingly
        if input_file.endswith('.csv'):
            df = pd.read_csv(input_file)
        elif input_file.endswith('.xlsx') or input_file.endswith('.xls'):
            df = pd.read_excel(input_file)
        else:
            return "Unsupported file format. Please use a CSV or Excel file."

        # Replace NaN with None
        df = df.replace({np.nan: None})

        # Convert DataFrame to JSON format
        json_data = df.to_dict(orient='records')

        # Generate a unique name for the output JSON file based on the input file name
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        json_file = f'{base_name}_output.json'

        # Write JSON data to a file
        with open(json_file, 'w') as f:
            json.dump(json_data, f, indent=4)

        print(f"JSON file created: {json_file}")
        return json_data

    except Exception as e:
        return f"Error occurred: {str(e)}"


def csv_to_txt(csv_file, txt_file):
    """Convert a CSV file to a TXT file."""
    try:
        with open(csv_file, 'r', encoding='utf-8') as csvf, open(txt_file, 'w', encoding='utf-8') as txtf:
            reader = csv.reader(csvf)
            for row in reader:
                # Write the row values separated by tabs or spaces
                txtf.write("\t".join(row) + "\n")
        print(f"Converted {csv_file} to {txt_file}")
    except Exception as e:
        print(f"Error converting CSV to TXT: {str(e)}")


def excel_to_txt(excel_file, txt_file):
    """Convert an Excel file to a TXT file."""
    try:
        # Read the Excel file using pandas
        # Read all sheets into a dictionary
        df = pd.read_excel(excel_file, sheet_name=None)
        with open(txt_file, 'w', encoding='utf-8') as txtf:
            for sheet_name, data in df.items():
                txtf.write(f"Sheet: {sheet_name}\n")
                data.to_csv(txtf, sep='\t', index=False,
                            header=True)  # Tab-separated values
                txtf.write("\n\n")  # Separate sheets with some space
        print(f"Converted Excel {excel_file} to {txt_file}")
    except Exception as e:
        print(f"Error converting Excel to TXT: {str(e)}")


def get_attachments_from_eml(basename, eml_file):
    # Directory where attachments will be saved
    output_dir = 'attachments/'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    attachment_paths = []

    with open(eml_file, 'rb') as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    for part in msg.walk():
        # Check if the part is an attachment
        if part.get_content_disposition() == 'attachment':
            filename = part.get_filename()
            if filename:
                # Prefix the basename to the filename to avoid naming conflicts
                name, ext = os.path.splitext(filename)
                ext = ext.lower()

                full_filename = f"{basename}_{name}{ext}"
                attachment_path = os.path.join(output_dir, full_filename)

                # Save the attachment
                with open(attachment_path, 'wb') as fp:
                    fp.write(part.get_payload(decode=True))

                # if ext == '.csv' or ext == '.xls' or ext == '.xlsx':
                #     txt_filename = os.path.splitext(full_filename)[0] + '.txt'
                #     txt_path = os.path.join(output_dir, txt_filename)

                #     if ext == '.csv':
                #         csv_to_txt(full_filename, txt_path)
                #     elif ext in ['.xls', '.xlsx']:
                #         excel_to_txt(output_dir+"/"+full_filename, txt_path)

                #     attachment_paths.append(txt_path)
                #     print(f"Saved and converted {ext.upper()} to TXT: {txt_path}")
                # else:

                attachment_paths.append(attachment_path)
                print(f"Saved attachment: {attachment_path}")

    # Return the list of attachment paths
    return attachment_paths


def get_text_from_eml(basename, eml):
    output_dir = 'data/email_data/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(eml, 'rb') as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    email_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                email_body = part.get_payload(decode=True).decode(
                    part.get_content_charset())
                break
    else:
        email_body = msg.get_payload(decode=True).decode(
            msg.get_content_charset())

    text_file_path = os.path.join(output_dir, f'{basename}_text.txt')

    with open(text_file_path, 'w') as f:
        f.write(email_body)

    return text_file_path

# Gradio interface


def gradio_interface(files):
    result_json = []
    eml_result = []
    try:

        for file in files:

            extension = os.path.basename(file).split('.')[-1]
            file_name = os.path.basename(file)
            basename = os.path.splitext(file_name)[0]

            if extension == 'eml':
                eml_text_path = get_text_from_eml(basename, file.name)
                eml_files = get_attachments_from_eml(basename, file.name)

                if eml_files:
                    print("files")
                    for attachment in eml_files:
                        att_extension = os.path.basename(
                            attachment).split('.')[-1]
                        att_basename = os.path.splitext(
                            os.path.basename(attachment))[0]
                        print(att_basename, att_extension)

                        # Process each attachment based on its extension

                        if att_extension == 'csv' or att_extension in ['xls', 'xlsx']:
                            print("hii2")
                            result2 = table_to_json(attachment)
                            eml_result.append(result2)
                        elif att_extension == 'png' or att_extension == 'jpeg':
                            result = process_image_file(attachment)
                        else:
                            result2 = process_files(eml_files)
                            eml_result.append(result2)

                result2 = process_files([eml_text_path])
                eml_result.append(result2)
                result = eml_result
            elif extension == 'csv' or extension in ['xls', 'xlsx']:
                result = table_to_json(file.name)

            elif extension == 'png' or extension == 'jpg' or extension == 'jpeg':
                result = process_image_file(file.name)

            else:
                result = process_files(file.name)
            if result is not None:

                result_json.append(result)

    except Exception as e:
        save_output_to_txt(
            f"Error in gradio_interface: {str(e)}", file_path="error_log.txt")

    return result_json


demo = gr.Interface(
    fn=gradio_interface,
    inputs=gr.File(label="Upload Files", file_count="multiple"),
    outputs=gr.JSON(label="Extracted JSON Data"),
    description="Upload multiple Files to extract structured data and analyze missing values on a per-file basis and overall."
)


if __name__ == "__main__":
    demo.launch()
