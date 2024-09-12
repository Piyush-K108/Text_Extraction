from run_assistance import json_to_csv, process_files
import gradio as gr
import tempfile


# Gradio interface
def gradio_interface(files):
    result_json = []

    # Process each file
    for file in files:
        result = process_files([file])
        result_json.append(result)

    return result_json

demo = gr.Interface(
    fn=gradio_interface,
    inputs=gr.File(label="Upload PDF(s)", file_count="multiple"),
    outputs=gr.JSON(label="Extracted JSON Data"),
    description="Upload multiple Files to extract structured data and analyze missing values on a per-file basis and overall."
)


if __name__ == "__main__":
    demo.launch()
