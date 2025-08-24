import os
import json
from collections import OrderedDict
from django.utils.text import slugify
import streamlit as st

# App title
st.title("📜 Gurbani Text Converter")

# Metadata
SOURCE_NAME = "Gurbani Files"
SOURCE_LINK = "http://www.gurbanifiles.org"

# Define work metadata
work = {
    "originalTitle": "ਗੁਰੂ ਗ੍ਰੰਥ ਸਾਹਿਬ ਜੀ",
    "englishTitle": "Guru Granth Sahib",
    "author": "Not available",
    "dirname": "guru_granth_sahib",
    "source": SOURCE_NAME,
    "sourceLink": SOURCE_LINK,
    "language": "punjabi",
    "text": {},
}

def convert_jagged_list_to_dict(lines):
    node = {str(i): line for i, line in enumerate(lines)}
    node = OrderedDict(sorted(node.items(), key=lambda item: int(item[0])))
    for key, value in node.items():
        if isinstance(value, list):
            node[key] = value[0] if len(value) == 1 else convert_jagged_list_to_dict(value)
    return node

def process_text_file(uploaded_file):
    lines = [line.strip() for line in uploaded_file.read().decode("utf-8").splitlines() if line.strip()]
    return convert_jagged_list_to_dict(lines)

# File uploader
uploaded_file = st.file_uploader("Upload your complete_text.txt file", type="txt")

if uploaded_file:
    st.success("File uploaded successfully!")
    work["text"] = process_text_file(uploaded_file)

    # Display preview
    st.subheader("📖 Text Preview")
    st.json(work["text"])

    # Generate filename
    filename = f"{slugify(work['source'])}__{slugify(work['englishTitle'][:100])}__{slugify(work['language'])}.json"
    filename = filename.replace(" ", "")

    # Download button
    st.download_button(
        label="📥 Download JSON",
        data=json.dumps(work, ensure_ascii=False, indent=2),
        file_name=filename,
        mime="application/json"
    )
else:
    st.info("Please upload a file to begin.")
