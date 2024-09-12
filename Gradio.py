from run_assistance import json_to_csv, process_files, save_output_to_txt
import gradio as gr
import email
from email import policy
import os


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
                full_filename = f"{basename}_{filename}"
                attachment_path = os.path.join(output_dir, full_filename)

                # Save the attachment
                with open(attachment_path, 'wb') as fp:
                    fp.write(part.get_payload(decode=True))

                # Append the attachment path to the list
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

    try:

        for file in files:
            
            extension = os.path.basename(file).split('.')[-1]
            file_name = os.path.basename(file)
            basename = os.path.splitext(file_name)[0]

            if extension == 'eml':
                eml_text_path = get_text_from_eml(basename, file.name)
                # eml_files = get_attachments_from_eml(basename, file.name)

                # if eml_files:process_files(eml_files)

                result = process_files([eml_text_path])
            else:

                result = process_files([file.name])
            if result is not None:

                result_json.append(result)

    except Exception as e:
        save_output_to_txt(
            f"Error in gradio_interface: {str(e)}", file_path="error_log.txt")

    return result_json


demo = gr.Interface(
    fn=gradio_interface,
    inputs=gr.File(label="Upload PDF(s)", file_count="multiple"),
    outputs=gr.JSON(label="Extracted JSON Data"),
    description="Upload multiple Files to extract structured data and analyze missing values on a per-file basis and overall."
)


if __name__ == "__main__":
    demo.launch()
