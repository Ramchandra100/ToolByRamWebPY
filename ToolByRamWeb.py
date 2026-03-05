import streamlit as st
import pandas as pd
from PIL import Image
from pypdf import PdfWriter, PdfReader
import imageio_ffmpeg
import subprocess
import os
import io
import shutil
import tempfile
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="ToolByRam - Cloud Suite",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# IMPORT MODULES
# =============================================================================
# Import the modules after page config
import AllFormatReaderWeb
import ExcelVaultWeb

# =============================================================================
# CUSTOM CSS FOR MODERN UI
# =============================================================================
st.markdown("""
<style>
    /* Main container styling */
    .main {
        padding: 0rem 1rem;
    }
    
    /* Header styles */
    .main-header {
        font-size: 42px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 20px;
    }
    
    .sub-header {
        font-size: 24px;
        color: #4a5568;
        font-weight: 600;
        margin-bottom: 15px;
    }
    
    /* Card styling */
    .css-1r6slb0 {
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f7fafc 0%, #edf2f7 100%);
    }
    
    /* Success/Info/Warning boxes */
    .stAlert {
        border-radius: 8px;
        border-left: 4px solid;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        background-color: #f7fafc;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* File uploader */
    .uploadedFile {
        border: 2px dashed #667eea;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = []
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="color: #667eea; font-size: 36px; margin-bottom: 0;">🛠️</h1>
        <h2 style="color: #4a5568; margin-top: 0;">ToolByRam</h2>
        <p style="color: #718096;">Resident Engineer Suite</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Dashboard
    if st.button("🏠 Dashboard", use_container_width=True):
        st.session_state.current_page = "Dashboard"
    
    # File Tools Section
    st.markdown("**📁 File Tools**")
    if st.button("📂 Universal Reader", use_container_width=True):
        st.session_state.current_page = "Universal Reader"
    if st.button("🔐 Excel Vault", use_container_width=True):
        st.session_state.current_page = "Excel Vault"
    
    # PDF Tools Section
    st.markdown("**📄 PDF Tools**")
    if st.button("📄 PDF Toolkit", use_container_width=True):
        st.session_state.current_page = "PDF Toolkit"
    
    # Video Tools Section
    st.markdown("**🎥 Video Tools**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎬 Merger", use_container_width=True):
            st.session_state.current_page = "Video Merger"
        if st.button("✂️ Trimmer", use_container_width=True):
            st.session_state.current_page = "Video Trimmer"
    with col2:
        if st.button("📉 Compressor", use_container_width=True):
            st.session_state.current_page = "Video Compressor"
        if st.button("🔊 Audio", use_container_width=True):
            st.session_state.current_page = "Audio Handler"
    
    # Data Tools Section
    st.markdown("**📇 Data Tools**")
    if st.button("📇 CSV to VCF", use_container_width=True):
        st.session_state.current_page = "CSV to VCF"
    
    # Settings
    st.markdown("**⚙️ System**")
    if st.button("⚙️ Settings", use_container_width=True):
        st.session_state.current_page = "Settings"
    
    st.divider()
    
    # Settings toggle
    dark_mode = st.toggle("🌙 Dark Mode", st.session_state.dark_mode)
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.rerun()
    
    # Recent files section
    if st.session_state.processed_files:
        st.markdown("**📁 Recent Files**")
        for file in st.session_state.processed_files[-5:]:
            st.caption(f"• {file}")
    
    st.divider()
    st.caption("v2.0 | Cloud Edition")
    st.caption(f"Session started: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_ffmpeg():
    """Get FFmpeg executable path"""
    return imageio_ffmpeg.get_ffmpeg_exe()

def cleanup_temp_files():
    """Clean up temporary files"""
    if os.path.exists(st.session_state.temp_dir):
        shutil.rmtree(st.session_state.temp_dir)
    st.session_state.temp_dir = tempfile.mkdtemp()

def add_to_recent(filename):
    """Add file to recent list"""
    if filename not in st.session_state.processed_files:
        st.session_state.processed_files.append(filename)

def create_metric_card(title, value, delta=None):
    """Create a styled metric card"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.metric(title, value, delta)

# =============================================================================
# PAGE ROUTING
# =============================================================================

# DASHBOARD
if st.session_state.current_page == "Dashboard":
    st.markdown('<p class="main-header">Welcome Back, Engineer! 👋</p>', unsafe_allow_html=True)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Files Processed", len(st.session_state.processed_files), "Today")
    with col2:
        st.metric("Available Tools", "9", "+3 this week")
    with col3:
        st.metric("Storage Used", "0 MB", "of 1 GB")
    with col4:
        st.metric("Session Time", "Active", "Now")
    
    st.divider()
    
    # Quick actions
    st.markdown('<p class="sub-header">Quick Actions</p>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Merge PDFs", use_container_width=True):
            st.session_state.current_page = "PDF Toolkit"
            st.rerun()
    
    with col2:
        if st.button("🎬 Merge Videos", use_container_width=True):
            st.session_state.current_page = "Video Merger"
            st.rerun()
    
    with col3:
        if st.button("📇 Convert CSV", use_container_width=True):
            st.session_state.current_page = "CSV to VCF"
            st.rerun()
    
    with col4:
        if st.button("📂 Read File", use_container_width=True):
            st.session_state.current_page = "Universal Reader"
            st.rerun()
    
    # Featured tools
    st.markdown('<p class="sub-header">🌟 Featured Tools</p>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown("""
            <div style="padding: 20px; border-radius: 10px; background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);">
                <h3>🔐 Excel Vault Pro</h3>
                <p>Secure your sensitive Excel data with military-grade AES-256 encryption. Encrypt specific columns, batch process files, and more.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Try Excel Vault →", key="feature_excel"):
                st.session_state.current_page = "Excel Vault"
                st.rerun()
    
    with col2:
        with st.container():
            st.markdown("""
            <div style="padding: 20px; border-radius: 10px; background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);">
                <h3>📂 Universal Reader</h3>
                <p>View any document format in your browser - PDF, Word, Excel, PowerPoint, images, and more. No download required.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Try Universal Reader →", key="feature_reader"):
                st.session_state.current_page = "Universal Reader"
                st.rerun()
    
    st.divider()
    
    # Usage tips
    with st.expander("💡 Pro Tips", expanded=False):
        st.info("""
        - **Excel Vault**: Encrypt sensitive columns in Excel files with password protection
        - **Universal Reader**: Preview any document before processing
        - Video tools work best with files under 200MB
        - Recent files are tracked in the sidebar for quick access
        - Dark mode available in settings
        """)

# UNIVERSAL READER
elif st.session_state.current_page == "Universal Reader":
    AllFormatReaderWeb.run()

# EXCEL VAULT
elif st.session_state.current_page == "Excel Vault":
    ExcelVaultWeb.run()

# =============================================================================
# PDF TOOLKIT
# =============================================================================
elif st.session_state.current_page == "PDF Toolkit":
    st.markdown('<p class="sub-header">📄 PDF Toolkit Pro</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔄 Merge", "🖼️ Images to PDF", "✂️ Split", 
        "🔒 Lock", "🔓 Unlock", "📝 Extract Text"
    ])
    
    # TAB 1: MERGE PDFs
    with tab1:
        st.markdown("### Merge Multiple PDFs")
        files = st.file_uploader(
            "Upload PDFs to merge",
            type="pdf",
            accept_multiple_files=True,
            key="pdf_merge",
            help="Select multiple PDF files in the order you want them merged"
        )
        
        if files:
            st.info(f"📊 Selected {len(files)} PDFs")
            
            # Reorder functionality
            if len(files) > 1:
                st.markdown("**Drag to reorder (if needed):**")
                file_order = st.multiselect(
                    "Reorder files",
                    options=[f.name for f in files],
                    default=[f.name for f in files],
                    key="pdf_order"
                )
                
                if file_order:
                    # Reorder files based on selection
                    ordered_files = []
                    for name in file_order:
                        for f in files:
                            if f.name == name:
                                ordered_files.append(f)
                                break
                    files = ordered_files
            
            if st.button("🔄 Merge PDFs", use_container_width=True):
                with st.spinner("Merging PDFs..."):
                    try:
                        merger = PdfWriter()
                        for pdf in files:
                            merger.append(pdf)
                        
                        buf = io.BytesIO()
                        merger.write(buf)
                        
                        st.success("✅ PDFs merged successfully!")
                        st.download_button(
                            "📥 Download Merged PDF",
                            buf.getvalue(),
                            "merged.pdf",
                            "application/pdf",
                            use_container_width=True
                        )
                        
                        add_to_recent("merged.pdf")
                    except Exception as e:
                        st.error(f"Error merging PDFs: {str(e)}")
    
    # TAB 2: IMAGES TO PDF
    with tab2:
        st.markdown("### Convert Images to PDF")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            imgs = st.file_uploader(
                "Upload Images",
                type=["jpg", "jpeg", "png", "bmp", "tiff"],
                accept_multiple_files=True,
                key="pdf_img",
                help="Upload one or more images to convert to PDF"
            )
        
        with col2:
            st.markdown("**Page Settings**")
            page_size = st.selectbox(
                "Page Size",
                ["A4", "Letter", "Legal"],
                help="Select the output page size"
            )
            orientation = st.radio(
                "Orientation",
                ["Portrait", "Landscape"],
                horizontal=True
            )
        
        if imgs and st.button("📄 Convert to PDF", use_container_width=True):
            with st.spinner(f"Converting {len(imgs)} images to PDF..."):
                try:
                    # Set page dimensions based on selection
                    if page_size == "A4":
                        if orientation == "Portrait":
                            page_dim = (595, 842)  # A4 portrait
                        else:
                            page_dim = (842, 595)  # A4 landscape
                    elif page_size == "Letter":
                        if orientation == "Portrait":
                            page_dim = (612, 792)  # Letter portrait
                        else:
                            page_dim = (792, 612)  # Letter landscape
                    else:  # Legal
                        if orientation == "Portrait":
                            page_dim = (612, 1008)  # Legal portrait
                        else:
                            page_dim = (1008, 612)  # Legal landscape
                    
                    pages = []
                    progress_bar = st.progress(0)
                    
                    for i, img_file in enumerate(imgs):
                        img = Image.open(img_file)
                        
                        # Convert RGBA to RGB if necessary
                        if img.mode == 'RGBA':
                            img = img.convert('RGB')
                        
                        # Calculate aspect ratio
                        img.thumbnail(page_dim, Image.Resampling.LANCZOS)
                        
                        # Create white background
                        page = Image.new('RGB', page_dim, 'white')
                        
                        # Center image on page
                        x = (page_dim[0] - img.width) // 2
                        y = (page_dim[1] - img.height) // 2
                        page.paste(img, (x, y))
                        
                        pages.append(page)
                        progress_bar.progress((i + 1) / len(imgs))
                    
                    # Save PDF
                    buf = io.BytesIO()
                    if pages:
                        pages[0].save(
                            buf,
                            "PDF",
                            save_all=True,
                            append_images=pages[1:],
                            quality=95
                        )
                        
                        st.success(f"✅ Successfully converted {len(imgs)} images to PDF!")
                        st.download_button(
                            "📥 Download PDF",
                            buf.getvalue(),
                            "images.pdf",
                            "application/pdf",
                            use_container_width=True
                        )
                        
                        add_to_recent("images.pdf")
                except Exception as e:
                    st.error(f"Error converting images: {str(e)}")
    
    # TAB 3: SPLIT PDF
    with tab3:
        st.markdown("### Extract Specific Pages")
        f = st.file_uploader("Upload PDF", type="pdf", key="pdf_split")
        
        if f:
            # Read PDF to show page count
            reader = PdfReader(f)
            total_pages = len(reader.pages)
            st.info(f"📄 This PDF has {total_pages} pages")
            
            split_method = st.radio(
                "Split Method",
                ["Page Range", "Individual Pages", "Every N Pages"],
                horizontal=True
            )
            
            if split_method == "Page Range":
                col1, col2 = st.columns(2)
                with col1:
                    start_page = st.number_input("Start Page", min_value=1, max_value=total_pages, value=1)
                with col2:
                    end_page = st.number_input("End Page", min_value=start_page, max_value=total_pages, value=min(start_page+1, total_pages))
                
                if st.button("✂️ Extract Pages", use_container_width=True):
                    with st.spinner("Extracting pages..."):
                        writer = PdfWriter()
                        for page_num in range(start_page - 1, end_page):
                            writer.add_page(reader.pages[page_num])
                        
                        buf = io.BytesIO()
                        writer.write(buf)
                        
                        st.success(f"✅ Extracted pages {start_page}-{end_page}")
                        st.download_button(
                            "📥 Download Extracted PDF",
                            buf.getvalue(),
                            f"pages_{start_page}-{end_page}.pdf",
                            "application/pdf",
                            use_container_width=True
                        )
            
            elif split_method == "Individual Pages":
                page_nums = st.multiselect(
                    "Select pages to extract",
                    options=list(range(1, total_pages + 1))
                )
                
                if page_nums and st.button("✂️ Extract Pages", use_container_width=True):
                    with st.spinner("Extracting pages..."):
                        writer = PdfWriter()
                        for page_num in page_nums:
                            writer.add_page(reader.pages[page_num - 1])
                        
                        buf = io.BytesIO()
                        writer.write(buf)
                        
                        st.success(f"✅ Extracted {len(page_nums)} pages")
                        st.download_button(
                            "📥 Download Extracted PDF",
                            buf.getvalue(),
                            "extracted_pages.pdf",
                            "application/pdf",
                            use_container_width=True
                        )
    
    # TAB 4: LOCK PDF
    with tab4:
        st.markdown("### Add Password Protection")
        f = st.file_uploader("PDF to Lock", type="pdf", key="pdf_lock")
        
        if f:
            col1, col2 = st.columns(2)
            with col1:
                password = st.text_input("Set Password", type="password", help="Choose a strong password")
            with col2:
                confirm_password = st.text_input("Confirm Password", type="password")
            
            encryption_level = st.select_slider(
                "Encryption Level",
                options=["Low (40-bit)", "Medium (128-bit)", "High (256-bit)"],
                value="Medium (128-bit)"
            )
            
            if st.button("🔒 Lock PDF", use_container_width=True):
                if not password:
                    st.error("Please enter a password")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    with st.spinner("Encrypting PDF..."):
                        reader = PdfReader(f)
                        writer = PdfWriter()
                        
                        for page in reader.pages:
                            writer.add_page(page)
                        
                        # Set encryption based on level
                        if "Low" in encryption_level:
                            writer.encrypt(password, algorithm='RC4-40')
                        elif "Medium" in encryption_level:
                            writer.encrypt(password, algorithm='RC4-128')
                        else:
                            writer.encrypt(password, algorithm='AES-256')
                        
                        buf = io.BytesIO()
                        writer.write(buf)
                        
                        st.success("✅ PDF locked successfully!")
                        st.download_button(
                            "📥 Download Locked PDF",
                            buf.getvalue(),
                            "locked.pdf",
                            "application/pdf",
                            use_container_width=True
                        )
    
    # TAB 5: UNLOCK PDF
    with tab5:
        st.markdown("### Remove Password Protection")
        f = st.file_uploader("Locked PDF", type="pdf", key="pdf_unlock")
        
        if f:
            password = st.text_input("Current Password", type="password", key="p_unlock")
            
            if st.button("🔓 Unlock PDF", use_container_width=True) and password:
                with st.spinner("Decrypting PDF..."):
                    reader = PdfReader(f)
                    
                    try:
                        if reader.decrypt(password):
                            writer = PdfWriter()
                            for page in reader.pages:
                                writer.add_page(page)
                            
                            buf = io.BytesIO()
                            writer.write(buf)
                            
                            st.success("✅ PDF unlocked successfully!")
                            st.download_button(
                                "📥 Download Unlocked PDF",
                                buf.getvalue(),
                                "unlocked.pdf",
                                "application/pdf",
                                use_container_width=True
                            )
                        else:
                            st.error("❌ Incorrect password")
                    except:
                        st.error("❌ Failed to decrypt PDF. Wrong password or corrupted file.")
    
    # TAB 6: EXTRACT TEXT
    with tab6:
        st.markdown("### Extract Text from PDF")
        f = st.file_uploader("Upload PDF", type="pdf", key="pdf_text")
        
        if f:
            reader = PdfReader(f)
            total_pages = len(reader.pages)
            
            col1, col2 = st.columns(2)
            with col1:
                extract_all = st.checkbox("Extract all pages", value=True)
            
            if not extract_all:
                with col2:
                    page_range = st.text_input("Page range (e.g., 1-5,7,9)", "1-3")
            
            if st.button("📝 Extract Text", use_container_width=True):
                with st.spinner("Extracting text..."):
                    extracted_text = ""
                    
                    if extract_all:
                        for i, page in enumerate(reader.pages):
                            text = page.extract_text()
                            extracted_text += f"\n--- Page {i+1} ---\n{text}\n"
                    else:
                        # Parse page range
                        pages_to_extract = set()
                        for part in page_range.split(','):
                            if '-' in part:
                                start, end = map(int, part.split('-'))
                                pages_to_extract.update(range(start, end + 1))
                            else:
                                pages_to_extract.add(int(part))
                        
                        for page_num in pages_to_extract:
                            if 1 <= page_num <= total_pages:
                                text = reader.pages[page_num - 1].extract_text()
                                extracted_text += f"\n--- Page {page_num} ---\n{text}\n"
                    
                    st.text_area("Extracted Text", extracted_text, height=400)
                    
                    # Download as text file
                    st.download_button(
                        "📥 Download as TXT",
                        extracted_text,
                        "extracted_text.txt",
                        "text/plain",
                        use_container_width=True
                    )

# =============================================================================
# VIDEO MERGER
# =============================================================================
elif st.session_state.current_page == "Video Merger":
    st.markdown('<p class="sub-header">🎥 Ultra Video Merger</p>', unsafe_allow_html=True)
    
    st.warning("""
    ⚠️ **Note:** Cloud processing has limitations:
    - Maximum file size: 200MB per video
    - Supported format: MP4
    - Processing time depends on file size
    """)
    
    videos = st.file_uploader(
        "Upload Videos (MP4)",
        type="mp4",
        accept_multiple_files=True,
        help="Select videos in the order you want them merged"
    )
    
    if videos:
        st.info(f"📊 Selected {len(videos)} videos")
        
        # Show video details
        for i, video in enumerate(videos):
            st.caption(f"{i+1}. {video.name} ({(video.size / (1024*1024)):.2f} MB)")
        
        merge_option = st.radio(
            "Merge Option",
            ["Direct Merge (Fastest)", "Re-encode (Better Compatibility)"],
            horizontal=True,
            help="Direct merge is faster but may have compatibility issues. Re-encode ensures compatibility but takes longer."
        )
        
        if st.button("🎬 Merge Videos", use_container_width=True):
            with st.spinner("Merging videos... This may take a few minutes..."):
                try:
                    temp_dir = st.session_state.temp_dir
                    list_path = os.path.join(temp_dir, "mylist.txt")
                    
                    # Save uploaded videos
                    with open(list_path, "w") as f:
                        for i, vid in enumerate(videos):
                            video_path = os.path.join(temp_dir, f"video{i}.mp4")
                            with open(video_path, "wb") as out:
                                out.write(vid.read())
                            f.write(f"file 'video{i}.mp4'\n")
                    
                    output_file = os.path.join(temp_dir, "merged_output.mp4")
                    
                    if merge_option == "Direct Merge (Fastest)":
                        cmd = [
                            get_ffmpeg(), "-f", "concat", "-safe", "0",
                            "-i", list_path, "-c", "copy", "-y", output_file
                        ]
                    else:
                        cmd = [
                            get_ffmpeg(), "-f", "concat", "-safe", "0",
                            "-i", list_path, "-c:v", "libx264", "-crf", "23",
                            "-preset", "medium", "-c:a", "aac", "-y", output_file
                        ]
                    
                    process = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if process.returncode == 0 and os.path.exists(output_file):
                        with open(output_file, "rb") as f:
                            video_data = f.read()
                        
                        st.success("✅ Videos merged successfully!")
                        st.download_button(
                            "📥 Download Merged Video",
                            video_data,
                            "merged_video.mp4",
                            "video/mp4",
                            use_container_width=True
                        )
                        
                        add_to_recent("merged_video.mp4")
                    else:
                        st.error(f"Error merging videos: {process.stderr}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                finally:
                    cleanup_temp_files()

# =============================================================================
# VIDEO TRIMMER
# =============================================================================
elif st.session_state.current_page == "Video Trimmer":
    st.markdown('<p class="sub-header">✂️ Video Trimmer</p>', unsafe_allow_html=True)
    
    vid = st.file_uploader("Upload Video", type="mp4", key="trim_v")
    
    if vid:
        st.info(f"📁 File: {vid.name} ({(vid.size / (1024*1024)):.2f} MB)")
        
        col1, col2 = st.columns(2)
        with col1:
            start = st.text_input("Start Time (HH:MM:SS)", "00:00:00")
        with col2:
            end = st.text_input("End Time (HH:MM:SS)", "00:00:10")
        
        # Quick time presets
        st.markdown("**Quick Presets:**")
        preset_cols = st.columns(3)
        with preset_cols[0]:
            if st.button("First 30s"):
                start, end = "00:00:00", "00:00:30"
        with preset_cols[1]:
            if st.button("Last 30s"):
                start, end = "00:00:30", "00:01:00"
        with preset_cols[2]:
            if st.button("Middle 30s"):
                start, end = "00:00:15", "00:00:45"
        
        if st.button("✂️ Trim Video", use_container_width=True):
            with st.spinner("Trimming video..."):
                try:
                    temp_dir = st.session_state.temp_dir
                    input_path = os.path.join(temp_dir, "temp_input.mp4")
                    output_path = os.path.join(temp_dir, "trimmed.mp4")
                    
                    with open(input_path, "wb") as f:
                        f.write(vid.read())
                    
                    cmd = [
                        get_ffmpeg(), "-ss", start, "-to", end,
                        "-i", input_path, "-c", "copy", "-y", output_path
                    ]
                    
                    process = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if process.returncode == 0 and os.path.exists(output_path):
                        with open(output_path, "rb") as f:
                            video_data = f.read()
                        
                        st.success("✅ Video trimmed successfully!")
                        st.download_button(
                            "📥 Download Trimmed Video",
                            video_data,
                            "trimmed_video.mp4",
                            "video/mp4",
                            use_container_width=True
                        )
                        
                        add_to_recent("trimmed_video.mp4")
                    else:
                        st.error(f"Error trimming video: {process.stderr}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                finally:
                    cleanup_temp_files()

# =============================================================================
# VIDEO COMPRESSOR
# =============================================================================
elif st.session_state.current_page == "Video Compressor":
    st.markdown('<p class="sub-header">📉 Video Compressor</p>', unsafe_allow_html=True)
    
    vid = st.file_uploader("Upload Video", type="mp4", key="comp_v")
    
    if vid:
        original_size = vid.size / (1024 * 1024)  # MB
        st.info(f"📁 Original size: {original_size:.2f} MB")
        
        col1, col2 = st.columns(2)
        with col1:
            compression_level = st.select_slider(
                "Compression Level",
                options=["Low (Better Quality)", "Medium (Balanced)", "High (Smaller File)"],
                value="Medium (Balanced)"
            )
        
        with col2:
            speed = st.select_slider(
                "Processing Speed",
                options=["Slow (Best Quality)", "Medium", "Fast", "Ultrafast"],
                value="Medium"
            )
        
        # Map selections to FFmpeg parameters
        crf_map = {
            "Low (Better Quality)": 18,
            "Medium (Balanced)": 23,
            "High (Smaller File)": 28
        }
        
        preset_map = {
            "Slow (Best Quality)": "slow",
            "Medium": "medium",
            "Fast": "fast",
            "Ultrafast": "ultrafast"
        }
        
        crf = crf_map[compression_level]
        preset = preset_map[speed]
        
        # Estimated size
        estimated_size = original_size * (crf / 23) * 0.7
        st.info(f"📊 Estimated compressed size: {estimated_size:.2f} MB ({(1 - estimated_size/original_size)*100:.1f}% reduction)")
        
        if st.button("📉 Compress Video", use_container_width=True):
            with st.spinner("Compressing video... This may take a while..."):
                try:
                    temp_dir = st.session_state.temp_dir
                    input_path = os.path.join(temp_dir, "temp_comp.mp4")
                    output_path = os.path.join(temp_dir, "compressed.mp4")
                    
                    with open(input_path, "wb") as f:
                        f.write(vid.read())
                    
                    cmd = [
                        get_ffmpeg(), "-i", input_path,
                        "-vcodec", "libx264", "-crf", str(crf),
                        "-preset", preset, "-y", output_path
                    ]
                    
                    process = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if process.returncode == 0 and os.path.exists(output_path):
                        compressed_size = os.path.getsize(output_path) / (1024 * 1024)
                        
                        with open(output_path, "rb") as f:
                            video_data = f.read()
                        
                        st.success(f"✅ Video compressed successfully!")
                        st.info(f"📊 Original: {original_size:.2f} MB → Compressed: {compressed_size:.2f} MB ({(1 - compressed_size/original_size)*100:.1f}% reduction)")
                        
                        st.download_button(
                            "📥 Download Compressed Video",
                            video_data,
                            "compressed_video.mp4",
                            "video/mp4",
                            use_container_width=True
                        )
                        
                        add_to_recent("compressed_video.mp4")
                    else:
                        st.error(f"Error compressing video: {process.stderr}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                finally:
                    cleanup_temp_files()

# =============================================================================
# AUDIO HANDLER
# =============================================================================
elif st.session_state.current_page == "Audio Handler":
    st.markdown('<p class="sub-header">🔊 Audio Handler</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔇 Mute Video", "🔄 Replace Audio"])
    
    # TAB 1: MUTE VIDEO
    with tab1:
        st.markdown("### Remove Audio from Video")
        vid = st.file_uploader("Upload Video", type="mp4", key="mute_v")
        
        if vid and st.button("🔇 Mute Video", use_container_width=True):
            with st.spinner("Processing..."):
                try:
                    temp_dir = st.session_state.temp_dir
                    input_path = os.path.join(temp_dir, "temp_video.mp4")
                    output_path = os.path.join(temp_dir, "muted.mp4")
                    
                    with open(input_path, "wb") as f:
                        f.write(vid.read())
                    
                    cmd = [
                        get_ffmpeg(), "-i", input_path,
                        "-c", "copy", "-an", "-y", output_path
                    ]
                    
                    process = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if process.returncode == 0 and os.path.exists(output_path):
                        with open(output_path, "rb") as f:
                            video_data = f.read()
                        
                        st.success("✅ Audio removed successfully!")
                        st.download_button(
                            "📥 Download Muted Video",
                            video_data,
                            "muted_video.mp4",
                            "video/mp4",
                            use_container_width=True
                        )
                        
                        add_to_recent("muted_video.mp4")
                    else:
                        st.error(f"Error: {process.stderr}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                finally:
                    cleanup_temp_files()
    
    # TAB 2: REPLACE AUDIO
    with tab2:
        st.markdown("### Replace Video Audio")
        col1, col2 = st.columns(2)
        
        with col1:
            vid = st.file_uploader("Upload Video", type="mp4", key="replace_v")
        
        with col2:
            aud = st.file_uploader("Upload New Audio", type=["mp3", "wav", "m4a"], key="replace_a")
        
        if vid and aud:
            st.info("The new audio will loop to match video duration if needed")
            
            if st.button("🔄 Replace Audio", use_container_width=True):
                with st.spinner("Replacing audio..."):
                    try:
                        temp_dir = st.session_state.temp_dir
                        video_path = os.path.join(temp_dir, "temp_video.mp4")
                        audio_path = os.path.join(temp_dir, "temp_audio.mp3")
                        output_path = os.path.join(temp_dir, "audio_replaced.mp4")
                        
                        with open(video_path, "wb") as f:
                            f.write(vid.read())
                        
                        with open(audio_path, "wb") as f:
                            f.write(aud.read())
                        
                        # Replace audio (loop if needed, match shortest duration)
                        cmd = [
                            get_ffmpeg(), "-i", video_path,
                            "-stream_loop", "-1", "-i", audio_path,
                            "-map", "0:v", "-map", "1:a",
                            "-c:v", "copy", "-shortest", "-y", output_path
                        ]
                        
                        process = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if process.returncode == 0 and os.path.exists(output_path):
                            with open(output_path, "rb") as f:
                                video_data = f.read()
                            
                            st.success("✅ Audio replaced successfully!")
                            st.download_button(
                                "📥 Download Video with New Audio",
                                video_data,
                                "video_with_new_audio.mp4",
                                "video/mp4",
                                use_container_width=True
                            )
                            
                            add_to_recent("video_with_new_audio.mp4")
                        else:
                            st.error(f"Error: {process.stderr}")
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                    finally:
                        cleanup_temp_files()

# =============================================================================
# CSV TO VCF CONVERTER
# =============================================================================
elif st.session_state.current_page == "CSV to VCF":
    st.markdown('<p class="sub-header">📇 CSV to VCF Contact Converter</p>', unsafe_allow_html=True)
    
    st.info("""
    **Format Requirements:**
    - CSV file should have 'Name' and 'Phone' columns
    - Optional columns: 'Email', 'Company', 'Title'
    - Phone numbers should include country code if possible
    """)
    
    f = st.file_uploader("Upload CSV", type="csv")
    
    if f:
        try:
            df = pd.read_csv(f)
            
            # Show preview
            st.markdown("**📊 Data Preview:**")
            st.dataframe(df.head(), use_container_width=True)
            
            # Column mapping
            st.markdown("**🔧 Column Mapping:**")
            col1, col2 = st.columns(2)
            
            with col1:
                name_col = st.selectbox(
                    "Select Name Column",
                    options=df.columns.tolist(),
                    index=df.columns.get_loc('Name') if 'Name' in df.columns else 0
                )
                
                phone_col = st.selectbox(
                    "Select Phone Column",
                    options=df.columns.tolist(),
                    index=df.columns.get_loc('Phone') if 'Phone' in df.columns else 0
                )
            
            with col2:
                email_col = st.selectbox(
                    "Select Email Column (Optional)",
                    options=["None"] + df.columns.tolist(),
                    index=df.columns.get_loc('Email') + 1 if 'Email' in df.columns else 0
                )
                
                company_col = st.selectbox(
                    "Select Company Column (Optional)",
                    options=["None"] + df.columns.tolist(),
                    index=df.columns.get_loc('Company') + 1 if 'Company' in df.columns else 0
                )
            
            # Contact grouping option
            group_name = st.text_input("Contact Group (Optional)", "")
            
            if st.button("📇 Convert to VCF", use_container_width=True):
                with st.spinner("Converting contacts..."):
                    try:
                        vcard_data = ""
                        success_count = 0
                        error_count = 0
                        
                        for idx, row in df.iterrows():
                            try:
                                name = str(row[name_col]).strip()
                                phone = str(row[phone_col]).strip()
                                
                                if name and phone and name.lower() != 'nan' and phone.lower() != 'nan':
                                    # Clean phone number
                                    phone = ''.join(filter(lambda x: x.isdigit() or x == '+', phone))
                                    
                                    vcard = f"BEGIN:VCARD\nVERSION:3.0\n"
                                    vcard += f"FN:{name}\n"
                                    vcard += f"N:{name};;;\n"
                                    
                                    # Add phone
                                    vcard += f"TEL;TYPE=CELL:{phone}\n"
                                    
                                    # Add email if available
                                    if email_col != "None" and email_col in row:
                                        email = str(row[email_col]).strip()
                                        if email and email.lower() != 'nan':
                                            vcard += f"EMAIL:{email}\n"
                                    
                                    # Add company if available
                                    if company_col != "None" and company_col in row:
                                        company = str(row[company_col]).strip()
                                        if company and company.lower() != 'nan':
                                            vcard += f"ORG:{company}\n"
                                    
                                    # Add group if specified
                                    if group_name:
                                        vcard += f"CATEGORIES:{group_name}\n"
                                    
                                    vcard += "END:VCARD\n\n"
                                    vcard_data += vcard
                                    success_count += 1
                            except:
                                error_count += 1
                        
                        if success_count > 0:
                            st.success(f"✅ Successfully converted {success_count} contacts!")
                            if error_count > 0:
                                st.warning(f"⚠️ Failed to convert {error_count} rows due to invalid data")
                            
                            # Create filename with date
                            filename = f"contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.vcf"
                            
                            st.download_button(
                                "📥 Download VCF File",
                                vcard_data,
                                filename,
                                "text/vcard",
                                use_container_width=True
                            )
                            
                            add_to_recent(filename)
                        else:
                            st.error("No valid contacts found to convert")
                    
                    except Exception as e:
                        st.error(f"Error during conversion: {str(e)}")
        
        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")

# =============================================================================
# SETTINGS PAGE
# =============================================================================
elif st.session_state.current_page == "Settings":
    st.markdown('<p class="sub-header">⚙️ Settings</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["General", "Storage", "About"])
    
    with tab1:
        st.markdown("### General Settings")
        
        # Theme settings
        dark_mode = st.toggle("Dark Mode", st.session_state.dark_mode)
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            st.rerun()
        
        # Language (future expansion)
        language = st.selectbox("Language", ["English", "Spanish", "French", "German"])
        
        # Auto-cleanup
        auto_cleanup = st.toggle("Auto-cleanup temporary files", value=True)
        
        if st.button("Save Settings", use_container_width=True):
            st.success("✅ Settings saved successfully!")
    
    with tab2:
        st.markdown("### Storage Management")
        
        # Storage stats
        temp_size = 0
        if os.path.exists(st.session_state.temp_dir):
            for file in os.listdir(st.session_state.temp_dir):
                file_path = os.path.join(st.session_state.temp_dir, file)
                if os.path.isfile(file_path):
                    temp_size += os.path.getsize(file_path)
        
        temp_size_mb = temp_size / (1024 * 1024)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Temporary Files Size", f"{temp_size_mb:.2f} MB")
        with col2:
            st.metric("Files Processed", len(st.session_state.processed_files))
        
        # Cleanup buttons
        if st.button("🧹 Clean Temporary Files", use_container_width=True):
            cleanup_temp_files()
            st.success("✅ Temporary files cleaned!")
            st.rerun()
        
        if st.button("🗑️ Clear Recent Files List", use_container_width=True):
            st.session_state.processed_files = []
            st.success("✅ Recent files cleared!")
    
    with tab3:
        st.markdown("### About ToolByRam")
        
        st.markdown("""
        **Version:** 2.0.0
        
        **Developer:** Resident Engineer
        
        **Description:** A comprehensive cloud-based toolkit for engineers
        
        **Features:**
        - Universal File Reader (PDF, DOCX, PPTX, XLSX, CSV, TXT, Images)
        - Excel Vault (AES-256 encryption for Excel files)
        - PDF Toolkit (Merge, Split, Lock, Unlock, Convert)
        - Video Processing (Merge, Trim, Compress)
        - Audio Handler (Mute, Replace Audio)
        - CSV to VCF Contact Converter
        
        **Technologies:**
        - Streamlit
        - Python
        - FFmpeg
        - PyPDF
        - Pandas
        - Cryptography
        
        **Support:** For issues or feature requests, please contact the developer.
        """)

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
col1, col2, col3 = st.columns(3)
with col2:
    st.caption("© 2024 ToolByRam - Resident Engineer Suite. All rights reserved.")