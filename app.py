import streamlit as st
import google.generativeai as genai
import os

from dotenv import load_dotenv
load_dotenv()

st.title("Next Lesson")
st.write("Welcome to the Next Lesson app!")

# Multifile Gemini Processing Section
st.header("Multifile Processing")
st.write("Upload multiple files, enter a prompt, and process them with Gemini API.")

with st.form("multifile_gemini_form"):
    uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True)
    prompt = st.text_area("Enter your prompt", height=100)
    submitted = st.form_submit_button("Process with Gemini")

if submitted and uploaded_files and prompt:
    # Read all file contents
    file_contents = []
    for file in uploaded_files:
        try:
            content = file.read()
            # Try to decode as text, fallback to repr for binary
            try:
                content = content.decode("utf-8")
            except Exception:
                content = str(content)
            file_contents.append(f"File: {file.name}\n{content}")
        except Exception as e:
            st.error(f"Failed to read {file.name}: {e}")
    # Combine all file contents
    combined_content = "\n\n".join(file_contents)

    # Prepare Gemini API
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL")
    if not api_key:
        st.error("Gemini API key not found. Set GEMINI_API_KEY as env var or in Streamlit secrets.")
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model)
        try:
            response = model.generate_content([
                {"role": "user", "parts": [
                    {"text": f"Prompt: {prompt}\n\nFiles:\n{combined_content}"}
                ]}
            ])
            st.subheader("Gemini Output")
            st.write(response.text)
        except Exception as e:
            st.error(f"Gemini API error: {e}")
