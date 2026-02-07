import streamlit as st
import pandas as pd
from pypdf import PdfReader
from docx import Document
from pptx import Presentation
import io

def run():
    st.header("📂 Universal File Reader")
    st.info("Supported: PDF, DOCX, PPTX, XLSX, CSV, TXT")

    uploaded_file = st.file_uploader("Upload any document", type=["pdf", "docx", "pptx", "xlsx", "csv", "txt"])

    if uploaded_file:
        file_type = uploaded_file.name.split('.')[-1].lower()
        st.divider()
        st.subheader(f"Viewing: {uploaded_file.name}")

        try:
            # --- 1. PDF READER ---
            if file_type == "pdf":
                reader = PdfReader(uploaded_file)
                # Let user pick a page to read
                total_pages = len(reader.pages)
                page_num = st.number_input(f"Select Page (1-{total_pages})", min_value=1, max_value=total_pages, value=1)
                
                text = reader.pages[page_num-1].extract_text()
                st.text_area("Page Content", text, height=600)

            # --- 2. WORD DOCUMENT (DOCX) ---
            elif file_type == "docx":
                doc = Document(uploaded_file)
                full_text = []
                for para in doc.paragraphs:
                    full_text.append(para.text)
                st.text_area("Document Content", '\n'.join(full_text), height=600)

            # --- 3. POWERPOINT (PPTX) ---
            elif file_type == "pptx":
                prs = Presentation(uploaded_file)
                st.write(f"**Total Slides:** {len(prs.slides)}")
                
                for i, slide in enumerate(prs.slides):
                    st.markdown(f"### Slide {i+1}")
                    slide_text = []
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            slide_text.append(shape.text)
                    
                    if slide_text:
                        st.text_area(f"Content - Slide {i+1}", "\n".join(slide_text), height=150)
                    else:
                        st.caption("(No text on this slide)")

            # --- 4. EXCEL / CSV ---
            elif file_type in ["xlsx", "csv"]:
                if file_type == "xlsx":
                    df = pd.read_excel(uploaded_file)
                else:
                    df = pd.read_csv(uploaded_file)
                
                st.write(f"**Rows:** {df.shape[0]} | **Columns:** {df.shape[1]}")
                st.dataframe(df)

            # --- 5. TEXT FILE ---
            elif file_type == "txt":
                stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
                st.text_area("File Content", stringio.read(), height=600)

        except Exception as e:
            st.error(f"Error reading file: {e}")