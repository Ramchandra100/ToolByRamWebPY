import streamlit as st
import pandas as pd
from PIL import Image
from pypdf import PdfWriter, PdfReader
import imageio_ffmpeg
import subprocess
import os
import io
import shutil
import AllFormatReaderWeb

# =============================================================================
# 1. PAGE CONFIGURATION
# =============================================================================
st.set_page_config(page_title="ToolByRam - Cloud Suite", page_icon="🛠️", layout="wide")

# Custom CSS to look like your Desktop App
st.markdown("""
<style>
    .main-header {font-size: 40px; color: #4da6ff; font-weight: bold;}
    .sub-header {font-size: 18px; color: gray;}
    .stButton>button {width: 100%; border-radius: 5px; height: 3em;}
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation (The "Launcher")
with st.sidebar:
    st.title("ToolByRam 🛠️")
    st.write("Resident Engineer Suite")
    st.divider()
    selected_tool = st.radio("Select Tool:", [
        "🏠 Dashboard",
        "📄 PDF Toolkit",
        "🎥 Video Merger",
        "✂️ Video Trimmer",
        "📉 Video Compressor",
        "🔊 Audio Handler",
        "📇 CSV to VCF"
    ])
    st.divider()
    st.info("v1.0 | Cloud Edition")

# Helper to get ffmpeg path
def get_ffmpeg():
    return imageio_ffmpeg.get_ffmpeg_exe()

# =============================================================================
# TOOL 1: DASHBOARD
# =============================================================================
if selected_tool == "🏠 Dashboard":
    st.markdown('<p class="main-header">Welcome, Resident Engineer</p>', unsafe_allow_html=True)
    st.write("Select a tool from the sidebar to begin.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🎥 **Video Tools**\n\nMerge, Trim, Compress, and Audio Swap.")
    with col2:
        st.info("📄 **PDF Suite**\n\nMerge, Split, Encrypt, Decrypt, Images->PDF.")
    with col3:
        st.info("📇 **Data Tools**\n\nConvert Site CSVs to Phone Contacts.")

# =============================================================================
# TOOL 2: PDF TOOLKIT (Ported from PdfToolKit_Web.py)
# =============================================================================
elif selected_tool == "📄 PDF Toolkit":
    st.header("📄 PDF Toolkit Pro")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Merge", "Images", "Split", "Lock", "Unlock"])
    
    with tab1: # MERGE
        files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True, key="pdf_merge")
        if st.button("Merge PDFs") and files:
            merger = PdfWriter()
            for pdf in files: merger.append(pdf)
            buf = io.BytesIO()
            merger.write(buf)
            st.success("Merged!")
            st.download_button("Download", buf.getvalue(), "merged.pdf", "application/pdf")

    with tab2: # IMAGES
        imgs = st.file_uploader("Upload Images", type=["jpg","png"], accept_multiple_files=True, key="pdf_img")
        if st.button("Convert to PDF (A4)") and imgs:
            a4 = (595, 842)
            pages = []
            for i in imgs:
                img = Image.open(i)
                # Aspect Ratio Logic
                ratio = img.width / img.height
                a4_ratio = a4[0] / a4[1]
                if ratio > a4_ratio:
                    nw, nh = a4[0], int(a4[0]/ratio)
                else:
                    nh, nw = a4[1], int(a4[1]*ratio)
                img = img.resize((nw, nh), Image.Resampling.LANCZOS)
                page = Image.new("RGB", a4, "white")
                page.paste(img, ((a4[0]-nw)//2, (a4[1]-nh)//2))
                pages.append(page)
            
            buf = io.BytesIO()
            if pages:
                pages[0].save(buf, "PDF", save_all=True, append_images=pages[1:])
                st.download_button("Download PDF", buf.getvalue(), "images.pdf", "application/pdf")

    with tab3: # SPLIT
        f = st.file_uploader("Upload PDF", type="pdf", key="pdf_split")
        rng = st.text_input("Range (e.g. 1-3)")
        if st.button("Extract") and f and rng:
            r = PdfReader(f)
            w = PdfWriter()
            # Simple parser
            if "-" in rng:
                s, e = map(int, rng.split("-"))
                for i in range(s-1, e): w.add_page(r.pages[i])
            else:
                w.add_page(r.pages[int(rng)-1])
            buf = io.BytesIO()
            w.write(buf)
            st.download_button("Download", buf.getvalue(), "extracted.pdf", "application/pdf")

    with tab4: # LOCK
        f = st.file_uploader("PDF to Lock", type="pdf", key="pdf_lock")
        pwd = st.text_input("Set Password", type="password")
        if st.button("Lock") and f and pwd:
            r = PdfReader(f)
            w = PdfWriter()
            for p in r.pages: w.add_page(p)
            w.encrypt(pwd)
            buf = io.BytesIO()
            w.write(buf)
            st.download_button("Download Locked", buf.getvalue(), "locked.pdf", "application/pdf")

    with tab5: # UNLOCK
        f = st.file_uploader("Locked PDF", type="pdf", key="pdf_unlock")
        pwd = st.text_input("Current Password", type="password", key="p_unlock")
        if st.button("Unlock") and f and pwd:
            r = PdfReader(f)
            if r.decrypt(pwd):
                w = PdfWriter()
                for p in r.pages: w.add_page(p)
                buf = io.BytesIO()
                w.write(buf)
                st.download_button("Download Unlocked", buf.getvalue(), "unlocked.pdf", "application/pdf")
            else:
                st.error("Wrong Password")

# =============================================================================
# TOOL 3: VIDEO MERGER
# =============================================================================
elif selected_tool == "🎥 Video Merger":
    st.header("🎥 Ultra Video Merger")
    st.warning("Note: Cloud processing is limited. Use files under 200MB.")
    
    videos = st.file_uploader("Upload Videos (MP4)", type="mp4", accept_multiple_files=True)
    
    if st.button("Merge Videos") and videos:
        # Save uploads to temp files
        os.makedirs("temp_merge", exist_ok=True)
        list_path = "temp_merge/mylist.txt"
        
        with open(list_path, "w") as f:
            for i, vid in enumerate(videos):
                path = f"temp_merge/vid{i}.mp4"
                with open(path, "wb") as out:
                    out.write(vid.read())
                f.write(f"file 'vid{i}.mp4'\n")
        
        output_file = "merged_output.mp4"
        cmd = [get_ffmpeg(), "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", "-y", output_file]
        subprocess.run(cmd)
        
        with open(output_file, "rb") as f:
            st.download_button("Download Merged Video", f, "merged.mp4")
        
        # Cleanup
        shutil.rmtree("temp_merge")

# =============================================================================
# TOOL 4: VIDEO TRIMMER
# =============================================================================
elif selected_tool == "✂️ Video Trimmer":
    st.header("✂️ Video Trimmer")
    vid = st.file_uploader("Upload Video", type="mp4", key="trim_v")
    start = st.text_input("Start Time (HH:MM:SS)", "00:00:00")
    end = st.text_input("End Time (HH:MM:SS)", "00:00:10")
    
    if st.button("Trim Video") and vid:
        with open("temp_input.mp4", "wb") as f: f.write(vid.read())
        
        output_file = "trimmed.mp4"
        cmd = [get_ffmpeg(), "-ss", start, "-to", end, "-i", "temp_input.mp4", "-c", "copy", "-y", output_file]
        subprocess.run(cmd)
        
        with open(output_file, "rb") as f:
            st.download_button("Download Trimmed Video", f, "trimmed.mp4")
        os.remove("temp_input.mp4")

# =============================================================================
# TOOL 5: VIDEO COMPRESSOR
# =============================================================================
elif selected_tool == "📉 Video Compressor":
    st.header("📉 Video Compressor")
    vid = st.file_uploader("Upload Video", type="mp4", key="comp_v")
    speed = st.select_slider("Speed vs Quality", options=["medium", "fast", "faster", "ultrafast"], value="ultrafast")
    
    if st.button("Compress") and vid:
        with open("temp_comp.mp4", "wb") as f: f.write(vid.read())
        
        output_file = "compressed.mp4"
        # CRF 28 is the sweet spot for engineering videos
        cmd = [get_ffmpeg(), "-i", "temp_comp.mp4", "-vcodec", "libx264", "-crf", "28", "-preset", speed, "-y", output_file]
        subprocess.run(cmd)
        
        with open(output_file, "rb") as f:
            st.download_button("Download Compressed Video", f, "compressed.mp4")
        os.remove("temp_comp.mp4")

# =============================================================================
# TOOL 6: AUDIO HANDLER
# =============================================================================
elif selected_tool == "🔊 Audio Handler":
    st.header("🔊 Audio Handler")
    vid = st.file_uploader("Upload Video", type="mp4", key="aud_v")
    mode = st.radio("Mode", ["Mute Video", "Replace Audio"])
    
    aud = None
    if mode == "Replace Audio":
        aud = st.file_uploader("Upload New Audio", type=["mp3", "wav"])
    
    if st.button("Process Audio") and vid:
        with open("temp_aud_v.mp4", "wb") as f: f.write(vid.read())
        output_file = "audio_processed.mp4"
        
        if mode == "Mute Video":
            cmd = [get_ffmpeg(), "-i", "temp_aud_v.mp4", "-c", "copy", "-an", "-y", output_file]
        
        elif mode == "Replace Audio" and aud:
            with open("temp_audio.mp3", "wb") as f: f.write(aud.read())
            # Logic: Loop audio, replace existing, cut to shortest
            cmd = [get_ffmpeg(), "-i", "temp_aud_v.mp4", "-stream_loop", "-1", "-i", "temp_audio.mp3", 
                   "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-shortest", "-y", output_file]
        
        subprocess.run(cmd)
        with open(output_file, "rb") as f:
            st.download_button("Download Result", f, "processed.mp4")
        
        if os.path.exists("temp_aud_v.mp4"): os.remove("temp_aud_v.mp4")
        if os.path.exists("temp_audio.mp3"): os.remove("temp_audio.mp3")

# =============================================================================
# TOOL 7: CSV TO VCF
# =============================================================================
elif selected_tool == "📇 CSV to VCF":
    st.header("📇 Site CSV to Contacts")
    st.info("Ensure CSV has columns: 'Name' and 'Phone'")
    
    f = st.file_uploader("Upload CSV", type="csv")
    if st.button("Convert") and f:
        try:
            df = pd.read_csv(f, dtype=str)
            if 'Name' not in df.columns or 'Phone' not in df.columns:
                st.error("Missing 'Name' or 'Phone' columns.")
            else:
                vcard_data = ""
                count = 0
                for _, row in df.iterrows():
                    name = str(row['Name']).strip()
                    phone = str(row['Phone']).strip()
                    if name and phone and name.lower() != 'nan':
                        vcard_data += f"BEGIN:VCARD\nVERSION:3.0\nFN:{name}\nTEL;TYPE=CELL:{phone}\nEND:VCARD\n"
                        count += 1
                
                st.success(f"Converted {count} contacts!")
                st.download_button("Download VCF", vcard_data, "contacts.vcf", "text/vcard")
        except Exception as e:
            st.error(f"Error: {e}")

# =============================================================================
# TOOL: UNIVERSAL READER
# =============================================================================
elif selected_tool == "📂 Universal Reader":
    AllFormatReaderWeb.run()            
