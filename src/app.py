import tempfile
import base64
import json
import textwrap
import pymupdf4llm
from constants import *
from extract import pdf_to_json
from openai import OpenAI

import streamlit as st
from table_qa import extract_text_from_pdf, generate_response_with_chatgpt


def extract_text_to_markdown(pdf_path: str):
    md_text = pymupdf4llm.to_markdown(pdf_path)
    return md_text



if __name__ == "__main__":
    st.set_page_config(page_title="PDF Extractor", layout="wide")
    st.title("📄 PDF to Structured JSON Extractor")

    with st.sidebar:
        st.header("📘 Project Info")
        st.markdown("""
        - 🔧 Extract text or images from PDFs  
        - 📑 Convert to structured JSON or Markdown  
        - 🖼️ View and download images  
        - 🎥 Watch a video demo
        """)

        st.subheader("> Data Modalities")
        extract_text = st.checkbox("Extract Text", value=True)
        extract_images = st.checkbox("Extract Images")
        extract_tables = st.checkbox("Extract Tables", disabled=True)

    tabs = st.tabs(["🎬 Demo Video", "🧾 Document Extraction Application"])

    with tabs[0]:

        st.subheader("🎬 Demonstration Video")
        st.video("data/doc_parser.mp4")


    with tabs[1]:
        uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

        if uploaded_file:
            with st.spinner("Processing PDF..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_filepath = tmp_file.name

                tabs = st.tabs(["🧾 Convert", "📂 Extracted Results", "💬 Table Q&A"])

                # --- TAB 2: Extracted Results ---
                with tabs[0]:

                    convert_type = st.radio("Choose Conversion Type:", ["Convert to JSON", "Convert to Markdown"])

                    if convert_type == "Convert to JSON":
                        if st.button("🔄 Convert PDF to JSON"):
                            with st.spinner("Processing PDF..."):
                                result = pdf_to_json(
                                    filepath=tmp_filepath,
                                    extract_text=extract_text,
                                    extract_images=extract_images,
                                    extract_tables=extract_tables
                                )

                            st.success("✅ Extraction complete!")

                            json_str = json.dumps(result, indent=2)
                            b64 = base64.b64encode(json_str.encode()).decode()
                            href = f'<a href="data:application/json;base64,{b64}" download="extracted_data.json">📥 Download JSON File</a>'
                            st.markdown(href, unsafe_allow_html=True)

                            st.subheader("📇 Metadata Preview")
                            st.json(result["metadata"])

                    elif convert_type == "Convert to Markdown":
                        if st.button("📝 Convert PDF to Markdown"):
                            with st.spinner("Extracting markdown..."):
                                markdown_text = extract_text_to_markdown(tmp_filepath)
                                st.markdown("### 🧾 Extracted Markdown")
                                st.code(markdown_text, language="markdown")

                                # Markdown download
                                b64_md = base64.b64encode(markdown_text.encode()).decode()
                                md_href = f'<a href="data:text/markdown;base64,{b64_md}" download="extracted_text.md">📥 Download Markdown File</a>'
                                st.markdown(md_href, unsafe_allow_html=True)

                # --- TAB 3: Demo Video ---
                with tabs[1]:


                    result = pdf_to_json(
                        filepath=tmp_filepath,
                        extract_text=extract_text,
                        extract_images=extract_images,
                        extract_tables=extract_tables
                    )

                    st.success("✅ PDF processed successfully!")

                    # JSON download again here (before images)
                    json_str = json.dumps(result, indent=2)
                    b64 = base64.b64encode(json_str.encode()).decode()
                    href = f'<a href="data:application/json;base64,{b64}" download="extracted_data.json">📥 Download Full JSON</a>'
                    st.markdown(href, unsafe_allow_html=True)

                    # Text
                    if extract_text:
                        st.subheader("📚 Extracted Text")
                        for page in result["pages"]:
                            st.markdown(f"**📄 Page {page['page_number']}**")
                            for block in page["content"]:
                                if block["type"] == "text":
                                    st.markdown(f"- {block['text']}")

                    # Images
                    if extract_images:
                        st.subheader("🖼️ Extracted Images")
                        for page in result["pages"]:
                            image_blocks = [
                                content["image_file"]
                                for content in page["content"]
                                if content["type"] == "image"
                            ]
                            if image_blocks:
                                st.markdown(f"**📄 Page {page['page_number']}**")
                                img_cols = st.columns(min(len(image_blocks), 3))
                                for idx, img_file in enumerate(image_blocks):
                                    with img_cols[idx % 3]:
                                        st.image(img_file, use_container_width=True)
                                        img_b64 = base64.b64encode(open(img_file, "rb").read()).decode()
                                        img_download = f'<a href="data:image/png;base64,{img_b64}" download="{Path(img_file).name}">📥 Download</a>'
                                        st.markdown(img_download, unsafe_allow_html=True)

                # --- TAB 4: Table Q&A ---
                with tabs[2]:
                    st.subheader("💬 Ask Questions About Tables in Your PDF")

                    api_key = st.text_input("🔑 Enter your OpenAI API Key", type="password")
                    qna_pdf = st.file_uploader("📥 Upload a PDF with tables", type="pdf", key="qna_pdf")

                    if api_key and qna_pdf:
                        with st.spinner("📊 Extracting tables..."):
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_qna_file:
                                tmp_qna_file.write(qna_pdf.read())
                                qna_path = tmp_qna_file.name

                            extracted_table_text = extract_text_from_pdf(qna_path)
                            st.session_state["table_data"] = extracted_table_text
                            st.success("✅ Tables extracted. You can now start chatting!")

                    if api_key and "table_data" in st.session_state:
                        client = OpenAI(api_key=api_key)
                        user_question = st.text_input("💭 Ask your question:")

                        if st.button("🔍 Get Answer"):
                            with st.spinner("Thinking..."):
                                prompt = st.session_state["table_data"] + "\n\n" + user_question
                                response = generate_response_with_chatgpt(client, prompt)

                                st.markdown("### 🤖 Response")
                                for line in textwrap.wrap(response, width=70):
                                    st.write(line)



