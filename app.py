import streamlit as st
import google.generativeai as genai
import os

from dotenv import load_dotenv
load_dotenv()

# Define your prompts here
PROMPT1 = open('prompts/assess_submission.txt').read()
PROMPT1 = open('prompts/combine.txt').read()

st.title("Next Lesson")
st.header("Make your next lesson impactful")

# # Multifile Gemini Processing Section
# st.header("Plan your next lesson")
st.write("Upload multiple students' submissions and one or more rubric files for analysis. You will get a next lesson's plan.")

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
    submitted = st.form_submit_button("Process!")

if submitted and submissions and rubrics:
    # Read all rubric contents
    rubric_contents = []
    for file in rubrics:
        try:
            content = file.read()
            try:
                content = content.decode("utf-8")
            except Exception:
                content = str(content)
            rubric_contents.append(f"Rubric: {file.name}\n{content}")
        except Exception as e:
            st.error(f"Failed to read rubric {file.name}: {e}")

    # Step 1: Process each submission with all rubrics using PROMPT2
    step1_outputs = []
    for submission_file in submissions:
        try:
            submission_content = submission_file.read()
            try:
                submission_content = submission_content.decode("utf-8")
            except Exception:
                submission_content = str(submission_content)
            submission_block = f"Submission: {submission_file.name}\n{submission_content}"
            # Combine submission with all rubrics
            combined_input = "\n\n".join(rubric_contents + [submission_block])
            # Prepare Gemini API
            api_key = os.getenv("GEMINI_API_KEY")
            model_id = os.getenv("GEMINI_MODEL")
            if not api_key:
                st.error("Gemini API key not found. Set GEMINI_API_KEY as env var or in Streamlit secrets.")
                break
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_id)
            try:
                response = model.generate_content([
                    {"role": "user", "parts": [
                        {"text": f"Prompt: {PROMPT2}\n\nFiles:\n{combined_input}"}
                    ]}
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
            api_key = os.getenv("GEMINI_API_KEY")
            model_id = os.getenv("GEMINI_MODEL")
            if not api_key:
                st.error("Gemini API key not found. Set GEMINI_API_KEY as env var or in Streamlit secrets.")
            else:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_id)
                response = model.generate_content([
                    {"role": "user", "parts": [
                        {"text": f"Prompt: {PROMPT2}\n\nFiles:\n{joint_output}"}
                    ]}
                ])
                st.success("Processing complete!")
                st.write(response.text)
        except Exception as e:
            st.error(f"Gemini API call failed at final step: {e}")
else:
    if submitted:
        st.warning("Please upload at least one submission and one rubric file.")
