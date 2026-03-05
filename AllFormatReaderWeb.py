import streamlit as st
import pandas as pd
from pypdf import PdfReader
from docx import Document
from pptx import Presentation
import io
import re
from datetime import datetime

def run():
    st.markdown('<p class="sub-header">📂 Universal File Reader</p>', unsafe_allow_html=True)
    
    st.info("""
    **Supported Formats:**
    - 📄 **Documents:** PDF, DOCX, TXT
    - 📊 **Presentations:** PPTX
    - 📈 **Spreadsheets:** XLSX, CSV
    - 🖼️ **Images:** JPG, PNG (metadata only)
    """)
    
    # File upload with multiple files support
    uploaded_files = st.file_uploader(
        "Upload files to read",
        type=["pdf", "docx", "pptx", "xlsx", "csv", "txt", "jpg", "png"],
        accept_multiple_files=True,
        help="You can upload multiple files at once"
    )
    
    if uploaded_files:
        # Create tabs for each file
        file_names = [f.name for f in uploaded_files]
        tabs = st.tabs(file_names)
        
        for idx, (tab, uploaded_file) in enumerate(zip(tabs, uploaded_files)):
            with tab:
                file_type = uploaded_file.name.split('.')[-1].lower()
                
                st.markdown(f"**File:** {uploaded_file.name}")
                st.markdown(f"**Size:** {(uploaded_file.size / 1024):.2f} KB")
                st.markdown(f"**Type:** {file_type.upper()}")
                st.divider()
                
                try:
                    # --- PDF READER with enhanced features ---
                    if file_type == "pdf":
                        reader = PdfReader(uploaded_file)
                        total_pages = len(reader.pages)
                        
                        # PDF metadata
                        if reader.metadata:
                            with st.expander("📋 Document Metadata"):
                                for key, value in reader.metadata.items():
                                    if value:
                                        st.text(f"{key}: {value}")
                        
                        # Page navigation
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            page_num = st.number_input(
                                f"Select Page (1-{total_pages})",
                                min_value=1,
                                max_value=total_pages,
                                value=1,
                                key=f"pdf_page_{idx}"
                            )
                        with col2:
                            st.metric("Total Pages", total_pages)
                        
                        # Extract text
                        text = reader.pages[page_num-1].extract_text()
                        
                        # Search functionality
                        search_term = st.text_input("🔍 Search in page", "", key=f"pdf_search_{idx}")
                        if search_term:
                            # Highlight matches (simple approach)
                            text = re.sub(
                                f'({re.escape(search_term)})',
                                r'**\1**',
                                text,
                                flags=re.IGNORECASE
                            )
                        
                        st.text_area("Page Content", text, height=500, key=f"pdf_content_{idx}")
                        
                        # Download page as text
                        if st.button(f"📥 Download Page {page_num} as TXT", key=f"pdf_dl_{idx}"):
                            st.download_button(
                                "Click to Download",
                                text,
                                f"page_{page_num}.txt",
                                "text/plain"
                            )
                    
                    # --- WORD DOCUMENT with formatting ---
                    elif file_type == "docx":
                        doc = Document(uploaded_file)
                        
                        # Document stats
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Paragraphs", len(doc.paragraphs))
                        with col2:
                            tables_count = len(doc.tables)
                            st.metric("Tables", tables_count)
                        with col3:
                            # Count words
                            word_count = sum(len(p.text.split()) for p in doc.paragraphs)
                            st.metric("Words", word_count)
                        
                        # Document content
                        full_text = []
                        for para in doc.paragraphs:
                            if para.text.strip():
                                full_text.append(para.text)
                        
                        text_content = '\n\n'.join(full_text)
                        st.text_area("Document Content", text_content, height=500, key=f"docx_content_{idx}")
                        
                        # Tables in document
                        if doc.tables:
                            with st.expander("📊 Tables in Document"):
                                for i, table in enumerate(doc.tables):
                                    st.markdown(f"**Table {i+1}**")
                                    data = []
                                    for row in table.rows:
                                        data.append([cell.text for cell in row.cells])
                                    if data:
                                        df = pd.DataFrame(data)
                                        st.dataframe(df, use_container_width=True)
                    
                    # --- POWERPOINT with slide thumbnails ---
                    elif file_type == "pptx":
                        prs = Presentation(uploaded_file)
                        
                        st.metric("Total Slides", len(prs.slides))
                        
                        # Slide navigation
                        slide_num = st.number_input(
                            "Select Slide",
                            min_value=1,
                            max_value=len(prs.slides),
                            value=1,
                            key=f"ppt_slide_{idx}"
                        )
                        
                        slide = prs.slides[slide_num-1]
                        
                        # Extract slide content
                        slide_text = []
                        for shape in slide.shapes:
                            if hasattr(shape, "text") and shape.text.strip():
                                slide_text.append(shape.text)
                        
                        if slide_text:
                            st.markdown(f"**Slide {slide_num} Content:**")
                            for text in slide_text:
                                st.info(text[:200] + "..." if len(text) > 200 else text)
                        else:
                            st.caption("(No text on this slide)")
                        
                        # Slide notes
                        if slide.has_notes_slide:
                            notes = slide.notes_slide.notes_text_frame.text
                            if notes:
                                with st.expander("📝 Slide Notes"):
                                    st.write(notes)
                        
                        # All slides view
                        with st.expander("📑 View All Slides"):
                            for i, s in enumerate(prs.slides):
                                st.markdown(f"**Slide {i+1}**")
                                slide_content = []
                                for shape in s.shapes:
                                    if hasattr(shape, "text") and shape.text.strip():
                                        slide_content.append(shape.text)
                                if slide_content:
                                    for text in slide_content[:3]:  # Limit to first 3 items
                                        st.caption(text[:100])
                                if len(slide_content) > 3:
                                    st.caption(f"... and {len(slide_content)-3} more items")
                                st.divider()
                    
                    # --- EXCEL with sheet navigation ---
                    elif file_type == "xlsx":
                        excel_file = pd.ExcelFile(uploaded_file)
                        
                        # Sheet selection
                        sheet_names = excel_file.sheet_names
                        selected_sheet = st.selectbox(
                            "Select Sheet",
                            sheet_names,
                            key=f"excel_sheet_{idx}"
                        )
                        
                        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
                        
                        # Data stats
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Rows", df.shape[0])
                        with col2:
                            st.metric("Columns", df.shape[1])
                        with col3:
                            st.metric("Memory", f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB")
                        
                        # Data preview
                        st.dataframe(df, use_container_width=True)
                        
                        # Data summary
                        with st.expander("📊 Data Summary"):
                            st.write(df.describe())
                        
                        # Column info
                        with st.expander("📋 Column Information"):
                            for col in df.columns:
                                st.text(f"{col}: {df[col].dtype} - {df[col].count()} non-null values")
                    
                    # --- CSV with encoding options ---
                    elif file_type == "csv":
                        # Encoding selection
                        encoding = st.selectbox(
                            "File Encoding",
                            ["utf-8", "latin-1", "cp1252", "iso-8859-1"],
                            key=f"csv_enc_{idx}"
                        )
                        
                        try:
                            # Reset file pointer
                            uploaded_file.seek(0)
                            df = pd.read_csv(uploaded_file, encoding=encoding)
                            
                            # Data stats
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Rows", df.shape[0])
                            with col2:
                                st.metric("Columns", df.shape[1])
                            
                            # Data preview
                            st.dataframe(df, use_container_width=True)
                            
                            # Quick stats
                            with st.expander("📊 Quick Statistics"):
                                st.write(df.describe())
                            
                            # Download as Excel
                            if st.button("📥 Download as Excel", key=f"csv_dl_{idx}"):
                                output = io.BytesIO()
                                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                    df.to_excel(writer, index=False)
                                st.download_button(
                                    "Click to Download Excel",
                                    output.getvalue(),
                                    uploaded_file.name.replace('.csv', '.xlsx'),
                                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                        
                        except UnicodeDecodeError:
                            st.error("Failed to read with selected encoding. Try another encoding.")
                    
                    # --- TEXT FILE with line numbers ---
                    elif file_type == "txt":
                        stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
                        content = stringio.read()
                        
                        # Text stats
                        lines = content.split('\n')
                        words = content.split()
                        chars = len(content)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Lines", len(lines))
                        with col2:
                            st.metric("Words", len(words))
                        with col3:
                            st.metric("Characters", chars)
                        
                        # Show with line numbers
                        show_line_numbers = st.checkbox("Show Line Numbers", True, key=f"txt_ln_{idx}")
                        
                        if show_line_numbers:
                            numbered_content = ""
                            for i, line in enumerate(lines, 1):
                                numbered_content += f"{i:4d} | {line}\n"
                            st.text_area("File Content", numbered_content, height=500, key=f"txt_content_{idx}")
                        else:
                            st.text_area("File Content", content, height=500, key=f"txt_content_{idx}")
                    
                    # --- IMAGE files (metadata only) ---
                    elif file_type in ["jpg", "png"]:
                        from PIL import Image
                        import PIL.ExifTags
                        
                        img = Image.open(uploaded_file)
                        
                        # Image info
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Format", img.format)
                        with col2:
                            st.metric("Size", f"{img.size[0]}x{img.size[1]}")
                        with col3:
                            st.metric("Mode", img.mode)
                        
                        # Show image
                        st.image(img, caption=uploaded_file.name, use_container_width=True)
                        
                        # EXIF data
                        try:
                            exif = img._getexif()
                            if exif:
                                with st.expander("📷 EXIF Data"):
                                    for tag_id, value in exif.items():
                                        tag = PIL.ExifTags.TAGS.get(tag_id, tag_id)
                                        if value and str(value).strip():
                                            st.text(f"{tag}: {value}")
                        except:
                            st.caption("No EXIF data available")
                
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
    
    else:
        # Show example when no file is uploaded
        st.markdown("### 📋 Quick Guide")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("""
            **📄 Documents**
            - PDF with page navigation
            - DOCX with tables
            - TXT with line numbers
            """)
        
        with col2:
            st.info("""
            **📊 Data Files**
            - Excel with sheet selection
            - CSV with encoding options
            - Data statistics
            """)
        
        with col3:
            st.info("""
            **🖼️ Media Files**
            - PPTX slide viewer
            - Image preview & EXIF
            - Metadata display
            """)