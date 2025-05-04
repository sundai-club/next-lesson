import streamlit as st
st.set_page_config(page_title="Next Lesson", page_icon="static/favicon.png")
import google.generativeai as genai
import os
import tempfile

from dotenv import load_dotenv
load_dotenv()

# Define your prompts here
PROMPT1 = open('prompts/assess_submission.txt').read()
PROMPT2 = open('prompts/combine.txt').read()
PROMPT3 = open('prompts/refine.txt').read()
PROMPT4 = open('prompts/action_items.txt').read()

st.title("Next Lesson")
col1, col2 = st.columns([3, 1])
with col1:
    # st.header("Make your next lesson impactful")
    st.write("Upload multiple students' submissions and one or more rubric files for analysis. You will get an analysis of overall trends in student data and customized suggestions to implement in your next lesson!")
    st.write("\n---\n*We do not store any uploaded or processed data; all files are processed in-memory and are not retained.  \nAI processing is performed using the Google Gemini API.*\n")
with col2:
    st.image("static/image.png")

# # Multifile Gemini Processing Section
# st.header("Plan your next lesson")
with st.form("multifile_gemini_form"):
    st.subheader("Student Submissions")
    submissions = st.file_uploader(
        "Upload student submissions in the form of scanned documents, PNG files, or PDFs. Upload one file per student, multiple files are allowed (.docx files are not supported).",
        accept_multiple_files=True,
        key="submissions_uploader"
    )
    st.subheader("Rubric File or Answer Key")
    rubrics = st.file_uploader(
        "Upload a rubric, lesson file(s), an ideal student submission, or an answer key in any format (multiple files allowed).",
        accept_multiple_files=True,
        key="rubrics_uploader"
    )
    st.subheader("Future Lesson Plan (Optional)")
    next_lesson_materials = st.file_uploader(
        "Optionally upload materials for your next lesson to inform tailored solutions to gaps in student understanding. If specific questions are noted, Next Lesson will make even more specific suggestions to inform your implementation of that lesson (multiple files allowed).",
        accept_multiple_files=True,
        key="next_lesson_materials_uploader"
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
                submission_mime = submission_file.type
                submission_name = submission_file.name
                # Check if .docx file is uploaded
                if submission_name.lower().endswith('.docx'):
                    st.error(".docx to PDF conversion is not supported. Please upload a PDF.")
                    continue
                submission_part = {
                    "mime_type": submission_mime,
                    "data": submission_bytes
                }
                rubric_parts = []
                for rubric_file in rubrics:
                    try:
                        rubric_file.seek(0)
                        rubric_bytes = rubric_file.read()
                        rubric_mime = rubric_file.type
                        rubric_name = rubric_file.name
                        # Check if .docx file is uploaded
                        if rubric_name.lower().endswith('.docx'):
                            st.error(".docx to PDF conversion is not supported. Please upload a PDF.")
                            continue
                        rubric_parts.append({
                            "mime_type": rubric_mime,
                            "data": rubric_bytes
                        })
                    except Exception as e:
                        st.error(f"Failed to read rubric {rubric_file.name}: {e}")
                # Compose the prompt as a text part
                prompt_part = {"text": PROMPT1}
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
                prompt_part = {"text": f"{PROMPT2}\n\nREVIEWS:\n{joint_output}"}
                response = model.generate_content([
                    {"role": "user", "parts": [prompt_part]}
                ])
                step2_output = response.text
                # Step 3: Process step2_output with PROMPT3
                prompt3_part = {"text": f"{PROMPT3}\n\nANALYSIS:\n\n{step2_output}"}
                response3 = model.generate_content([
                    {"role": "user", "parts": [prompt3_part]}
                ])
                step3_output = response3.text
                # Step 4: Generate action items with PROMPT4 and next lesson materials if provided
                prompt4_text = f"{PROMPT4}\n\nANALYSIS:\n\n{step2_output}"
                prompt4_parts = [
                    {"text": prompt4_text}
                ]
                if next_lesson_materials:
                    for material_file in next_lesson_materials:
                        try:
                            material_file.seek(0)
                            material_bytes = material_file.read()
                            material_mime = material_file.type
                            material_name = material_file.name
                            # Check if .docx file is uploaded
                            if material_name.lower().endswith('.docx'):
                                st.error(".docx to PDF conversion is not supported. Please upload a PDF.")
                                continue
                            prompt4_parts.append({
                                "mime_type": material_mime,
                                "data": material_bytes
                            })
                        except Exception as e:
                            st.error(f"Failed to read next lesson material {material_file.name}: {e}")
                response4 = model.generate_content([
                    {"role": "user", "parts": prompt4_parts}
                ])
                st.success("Processing complete!")
                st.write("### Analysis and Suggestions")
                st.write(step3_output)
                st.write("---")
                st.write("### Action Items")
                st.write(response4.text)
            except Exception as e:
                st.error(f"Gemini API call failed at final step: {e}")
else:
    if submitted:
        st.warning("Please upload at least one submission and one rubric file.")
