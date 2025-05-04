import streamlit as st
import google.generativeai as genai
import os

from dotenv import load_dotenv
load_dotenv()

# Define your prompts here
PROMPT1 = open('prompts/assess_submission.txt').read()
PROMPT2 = open('prompts/combine.txt').read()

st.title("Make your next lesson count")
col1, col2 = st.columns([3, 1])
with col1:
    # st.header("Make your next lesson impactful")
    st.write("Upload multiple students' submissions and one or more rubric files for analysis. You will get a next lesson's plan.")
    st.write("\n---\n*We do not store any uploaded or processed data; all files are processed in-memory and are not retained.  \nAI processing is performed using the Google Gemini API.*\n")
with col2:
    st.image("static/image.png")

# # Multifile Gemini Processing Section
# st.header("Plan your next lesson")
with st.form("multifile_gemini_form"):
    st.subheader("Student Submissions")
    submissions = st.file_uploader(
        "Upload student submissions (one file per student, multiple files allowed)",
        accept_multiple_files=True,
        key="submissions_uploader"
    )
    st.subheader("Rubric Files")
    rubrics = st.file_uploader(
        "Upload rubric or lesson file(s) in any format (one or more files allowed)",
        accept_multiple_files=True,
        key="rubrics_uploader"
    )
    submitted = st.form_submit_button("Build your next lesson")

if submitted and submissions and rubrics:
    # Prepare Gemini API
    api_key = os.getenv("GEMINI_API_KEY")
    model_id = os.getenv("GEMINI_MODEL")
    if not api_key:
        st.error("Gemini API key not found. Set GEMINI_API_KEY as env var or in Streamlit secrets.")
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_id)
        # Step 1: Process each submission with all rubrics using PROMPT2
        step1_outputs = []
        for submission_file in submissions:
            try:
                # Reset file pointer and read bytes
                submission_file.seek(0)
                submission_bytes = submission_file.read()
                submission_part = {
                    "mime_type": submission_file.type,
                    "data": submission_bytes
                }
                rubric_parts = []
                for rubric_file in rubrics:
                    try:
                        rubric_file.seek(0)
                        rubric_bytes = rubric_file.read()
                        rubric_parts.append({
                            "mime_type": rubric_file.type,
                            "data": rubric_bytes
                        })
                    except Exception as e:
                        st.error(f"Failed to read rubric {rubric_file.name}: {e}")
                # Compose the prompt as a text part
                prompt_part = {"text": f"Prompt: {PROMPT2}\n\nAnalyze the following student submission and rubrics."}
                # Gemini multimodal: prompt, rubric files, submission file
                parts = [prompt_part] + rubric_parts + [submission_part]
                try:
                    response = model.generate_content([
                        {"role": "user", "parts": parts}
                    ])
                    step1_outputs.append(response.text)
                except Exception as e:
                    st.error(f"Gemini API call failed for submission {submission_file.name}: {e}")
            except Exception as e:
                st.error(f"Failed to read submission {submission_file.name}: {e}")
        # Step 2: Process joint output of previous step with PROMPT2
        if step1_outputs:
            joint_output = "\n\n".join(step1_outputs)
            try:
                # Compose multimodal input for joint step (text only)
                prompt_part = {"text": f"Prompt: {PROMPT2}\n\nFiles:\n{joint_output}"}
                response = model.generate_content([
                    {"role": "user", "parts": [prompt_part]}
                ])
                st.success("Processing complete!")
                st.write(response.text)
            except Exception as e:
                st.error(f"Gemini API call failed at final step: {e}")
else:
    if submitted:
        st.warning("Please upload at least one submission and one rubric file.")
