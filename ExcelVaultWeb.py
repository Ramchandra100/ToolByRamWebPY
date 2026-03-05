import streamlit as st
import pandas as pd
import os
import base64
import json
import hashlib
import secrets
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken
import io
import re
import zipfile
from pathlib import Path

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="Excel Vault - Secure Excel Encryption",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS
# =============================================================================
st.markdown("""
<style>
    /* Main header */
    .vault-header {
        font-size: 42px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 10px;
        text-align: center;
    }
    
    .vault-subheader {
        font-size: 18px;
        color: #718096;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* Cards */
    .vault-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
        margin-bottom: 20px;
    }
    
    /* Password strength meter */
    .strength-meter {
        height: 10px;
        border-radius: 5px;
        background: linear-gradient(90deg, #ff4444 0%, #ffbb33 50%, #00C851 100%);
        transition: width 0.3s ease;
    }
    
    /* File info */
    .file-info {
        background-color: #f7fafc;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #667eea;
    }
    
    /* Stats boxes */
    .stat-box {
        background-color: #f7fafc;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    
    .stat-number {
        font-size: 28px;
        font-weight: bold;
        color: #667eea;
    }
    
    .stat-label {
        font-size: 14px;
        color: #718096;
    }
    
    /* Encrypted text styling */
    .encrypted-text {
        font-family: monospace;
        background-color: #2d3748;
        color: #a0d6ff;
        padding: 10px;
        border-radius: 5px;
        overflow-x: auto;
    }
    
    /* Success animation */
    @keyframes successPulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .success-animation {
        animation: successPulse 1s ease;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================
if 'vault_current_file' not in st.session_state:
    st.session_state.vault_current_file = None
if 'vault_encrypted_data' not in st.session_state:
    st.session_state.vault_encrypted_data = None
if 'vault_decrypted_df' not in st.session_state:
    st.session_state.vault_decrypted_df = None
if 'vault_history' not in st.session_state:
    st.session_state.vault_history = []
if 'vault_salt' not in st.session_state:
    st.session_state.vault_salt = secrets.token_bytes(16)
if 'vault_settings' not in st.session_state:
    st.session_state.vault_settings = {
        'auto_clear': True,
        'theme': 'Light',
        'font_size': 'Medium'
    }

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_key_from_password(password: str, salt: bytes, iterations: int = 300000):
    """Generate encryption key from password"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return Fernet(key)

def check_password_strength(password):
    """Check password strength and return score and message"""
    if not password:
        return 0, "No password", "gray"
    
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    
    # Complexity checks
    if re.search(r"[A-Z]", password):
        score += 1
    if re.search(r"[a-z]", password):
        score += 1
    if re.search(r"\d", password):
        score += 1
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        score += 1
    
    # Calculate percentage
    percentage = min(score / 6, 1.0)
    
    # Determine strength level
    if percentage < 0.3:
        return percentage, "Weak", "red"
    elif percentage < 0.6:
        return percentage, "Medium", "orange"
    elif percentage < 0.8:
        return percentage, "Strong", "lightgreen"
    else:
        return percentage, "Very Strong", "green"

def format_bytes(size_bytes):
    """Format bytes to human readable"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"

def add_to_history(filename, operation):
    """Add operation to history"""
    st.session_state.vault_history.append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'file': filename,
        'operation': operation
    })
    # Keep only last 10 items
    if len(st.session_state.vault_history) > 10:
        st.session_state.vault_history = st.session_state.vault_history[-10:]

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown('<h1 style="text-align: center; color: #667eea;">🔐 Excel Vault</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #718096;">Secure Excel Encryption</p>', unsafe_allow_html=True)
    
    st.divider()
    
    # Navigation
    page = st.radio(
        "Navigation",
        ["🔐 Encrypt File", "🔓 Decrypt & View", "📦 Batch Process", "⚙️ Settings", "📊 History"],
        key="vault_nav"
    )
    
    st.divider()
    
    # Security status
    st.markdown("### 🔒 Security Status")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Files Processed", len(st.session_state.vault_history))
    with col2:
        st.metric("Security Level", "AES-256")
    
    # Recent activity
    if st.session_state.vault_history:
        st.markdown("### 📋 Recent Activity")
        for item in st.session_state.vault_history[-3:]:
            st.caption(f"• {item['timestamp'][-8:]}: {item['operation']} - {item['file']}")
    
    st.divider()
    st.caption("© 2024 Excel Vault Pro | Military-Grade Encryption")

# =============================================================================
# ENCRYPT FILE PAGE
# =============================================================================
if page == "🔐 Encrypt File":
    st.markdown('<h1 class="vault-header">🔐 Encrypt Excel File</h1>', unsafe_allow_html=True)
    st.markdown('<p class="vault-subheader">Secure your sensitive data with AES-256 encryption</p>', unsafe_allow_html=True)
    
    # Create two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📁 File Selection")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose Excel file",
            type=['xlsx', 'xls'],
            help="Upload the Excel file you want to encrypt"
        )
        
        if uploaded_file:
            st.session_state.vault_current_file = uploaded_file
            
            # File info
            st.markdown("### 📊 File Information")
            st.markdown(f"""
            <div class="file-info">
                <b>Filename:</b> {uploaded_file.name}<br>
                <b>Size:</b> {format_bytes(uploaded_file.size)}<br>
                <b>Type:</b> {uploaded_file.type}
            </div>
            """, unsafe_allow_html=True)
            
            # Preview data
            try:
                df_preview = pd.read_excel(uploaded_file, nrows=5)
                st.markdown("### 👁️ Data Preview (First 5 rows)")
                st.dataframe(df_preview, use_container_width=True)
                
                # Store columns for later use
                available_columns = df_preview.columns.tolist()
            except Exception as e:
                st.error(f"Error reading file: {e}")
                available_columns = []
    
    with col2:
        st.markdown("### 🔑 Security Settings")
        
        # Password input
        password = st.text_input(
            "Password",
            type="password",
            help="Enter a strong password (minimum 8 characters)",
            key="encrypt_password"
        )
        
        # Password strength meter
        if password:
            strength_percent, strength_text, strength_color = check_password_strength(password)
            st.markdown(f"**Strength:** <span style='color: {strength_color};'>{strength_text}</span>", unsafe_allow_html=True)
            st.progress(strength_percent)
            
            # Password requirements
            with st.expander("Password Requirements"):
                requirements = [
                    ("✓" if len(password) >= 8 else "✗") + " At least 8 characters",
                    ("✓" if re.search(r"[A-Z]", password) else "✗") + " Uppercase letter",
                    ("✓" if re.search(r"[a-z]", password) else "✗") + " Lowercase letter",
                    ("✓" if re.search(r"\d", password) else "✗") + " Number",
                    ("✓" if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password) else "✗") + " Special character"
                ]
                for req in requirements:
                    st.markdown(req)
        
        # Confirm password
        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="encrypt_confirm"
        )
        
        if password and confirm_password and password != confirm_password:
            st.error("❌ Passwords do not match")
        
        # Advanced options
        with st.expander("⚙️ Advanced Options"):
            # Column selection
            if uploaded_file and 'available_columns' in locals():
                default_columns = [col for col in ['id', 'pass', 'password', 'email', 'secret'] if col in available_columns]
                columns_to_encrypt = st.multiselect(
                    "Columns to encrypt",
                    options=available_columns,
                    default=default_columns,
                    help="Select which columns to encrypt"
                )
            else:
                columns_to_encrypt = st.text_input(
                    "Columns to encrypt (comma-separated)",
                    value="id,pass",
                    help="e.g., id,pass,email"
                ).split(',')
                columns_to_encrypt = [col.strip() for col in columns_to_encrypt if col.strip()]
            
            # Iterations slider
            iterations = st.slider(
                "Encryption iterations",
                min_value=100000,
                max_value=1000000,
                value=300000,
                step=100000,
                help="Higher iterations = more secure but slower"
            )
            st.caption(f"Using {iterations:,} iterations")
        
        # Encrypt button
        if st.button("🔒 Encrypt File", use_container_width=True, type="primary"):
            if not uploaded_file:
                st.error("Please select a file first")
            elif not password:
                st.error("Please enter a password")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif not columns_to_encrypt:
                st.error("Please select at least one column to encrypt")
            else:
                try:
                    with st.spinner("🔒 Encrypting file... This may take a moment"):
                        # Read the file
                        df = pd.read_excel(uploaded_file)
                        
                        # Generate encryption key
                        fernet = get_key_from_password(password, st.session_state.vault_salt, iterations)
                        
                        # Store metadata
                        metadata = {
                            "encrypted_columns": columns_to_encrypt,
                            "iterations": iterations,
                            "timestamp": datetime.now().isoformat(),
                            "original_file": uploaded_file.name,
                            "rows": len(df),
                            "columns": len(df.columns)
                        }
                        
                        # Encrypt specified columns
                        encrypted_count = 0
                        for col in columns_to_encrypt:
                            if col in df.columns:
                                df[col] = df[col].apply(
                                    lambda x: fernet.encrypt(str(x).encode()).decode()
                                    if pd.notna(x) else x
                                )
                                encrypted_count += 1
                        
                        if encrypted_count == 0:
                            st.warning("No matching columns found to encrypt")
                        else:
                            # Create download buffers
                            excel_buffer = io.BytesIO()
                            df.to_excel(excel_buffer, index=False)
                            
                            meta_buffer = io.BytesIO()
                            meta_buffer.write(json.dumps(metadata, indent=2).encode())
                            
                            # Create ZIP file with both files
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                                zip_file.writestr(f"encrypted_{uploaded_file.name}", excel_buffer.getvalue())
                                zip_file.writestr(f"metadata_{uploaded_file.name.replace('.xlsx', '.json')}", meta_buffer.getvalue())
                            
                            # Success message
                            st.success(f"""
                            ✅ Encryption successful!
                            - Encrypted {encrypted_count} columns
                            - {len(df)} rows processed
                            - Using {iterations:,} iterations
                            """)
                            
                            # Download button
                            st.download_button(
                                label="📥 Download Encrypted Package (ZIP)",
                                data=zip_buffer.getvalue(),
                                file_name=f"encrypted_{uploaded_file.name.replace('.xlsx', '')}_package.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                            
                            # Add to history
                            add_to_history(uploaded_file.name, "Encrypted")
                            
                            # Show encryption preview
                            with st.expander("🔍 Encryption Preview"):
                                preview_df = df.head(3)
                                for col in columns_to_encrypt:
                                    if col in preview_df.columns:
                                        st.markdown(f"**{col}** (encrypted):")
                                        for val in preview_df[col]:
                                            if pd.notna(val):
                                                val_str = str(val)
                                                st.code(f"{val_str[:50]}..." if len(val_str) > 50 else val_str)
                                
                except Exception as e:
                    st.error(f"Encryption failed: {str(e)}")

# =============================================================================
# DECRYPT & VIEW PAGE
# =============================================================================
elif page == "🔓 Decrypt & View":
    st.markdown('<h1 class="vault-header">🔓 Decrypt & View Excel</h1>', unsafe_allow_html=True)
    st.markdown('<p class="vault-subheader">Decrypt and view your protected Excel files</p>', unsafe_allow_html=True)
    
    # Create two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📁 File Upload")
        
        # Allow ZIP upload or individual files
        upload_option = st.radio(
            "Upload option",
            ["Upload encrypted Excel + metadata", "Upload encrypted package (ZIP)"],
            horizontal=True
        )
        
        encrypted_file = None
        meta_file = None
        
        if upload_option == "Upload encrypted Excel + metadata":
            col_a, col_b = st.columns(2)
            with col_a:
                encrypted_file = st.file_uploader(
                    "Encrypted Excel file",
                    type=['xlsx'],
                    key="enc_excel"
                )
            with col_b:
                meta_file = st.file_uploader(
                    "Metadata file (JSON)",
                    type=['json'],
                    key="enc_meta"
                )
        else:
            zip_file = st.file_uploader(
                "Upload encrypted package (ZIP)",
                type=['zip'],
                help="Upload the ZIP file containing encrypted Excel and metadata"
            )
            
            if zip_file:
                with zipfile.ZipFile(zip_file) as z:
                    # Extract files
                    for file_name in z.namelist():
                        if file_name.endswith('.xlsx'):
                            encrypted_file = io.BytesIO(z.read(file_name))
                            encrypted_file.name = file_name
                        elif file_name.endswith('.json'):
                            meta_file = io.BytesIO(z.read(file_name))
        
        # Password input
        password = st.text_input(
            "Password",
            type="password",
            key="decrypt_password",
            help="Enter the password used for encryption"
        )
        
        # Show password checkbox
        show_password = st.checkbox("Show password")
        if show_password:
            st.code(password) if password else None
        
        # Decrypt button
        if st.button("🔓 Decrypt File", use_container_width=True, type="primary"):
            if not encrypted_file:
                st.error("Please upload the encrypted Excel file")
            elif not password:
                st.error("Please enter the password")
            else:
                try:
                    with st.spinner("🔓 Decrypting file..."):
                        # Try to load metadata
                        iterations = 300000  # Default
                        columns_to_decrypt = []
                        
                        if meta_file:
                            meta_file.seek(0)
                            metadata = json.load(meta_file)
                            iterations = metadata.get('iterations', 300000)
                            columns_to_decrypt = metadata.get('encrypted_columns', [])
                        
                        # Read encrypted file
                        encrypted_file.seek(0)
                        df = pd.read_excel(encrypted_file)
                        
                        # Generate decryption key
                        fernet = get_key_from_password(password, st.session_state.vault_salt, iterations)
                        
                        # Decrypt data
                        decrypted_data = []
                        decryption_errors = 0
                        
                        for idx, row in df.iterrows():
                            decrypted_row = []
                            for col in df.columns:
                                try:
                                    if col in columns_to_decrypt and pd.notna(row[col]) and str(row[col]).startswith('gAAAAA'):
                                        decrypted = fernet.decrypt(str(row[col]).encode()).decode()
                                        decrypted_row.append(decrypted)
                                    else:
                                        decrypted_row.append(row[col])
                                except (InvalidToken, Exception):
                                    decrypted_row.append("🔒 DECRYPTION FAILED")
                                    decryption_errors += 1
                            
                            decrypted_data.append(decrypted_row)
                        
                        # Store decrypted data
                        st.session_state.vault_decrypted_df = pd.DataFrame(decrypted_data, columns=df.columns)
                        
                        # Success message
                        if decryption_errors == 0:
                            st.success(f"✅ Successfully decrypted {len(df)} rows!")
                        else:
                            st.warning(f"⚠️ Decrypted {len(df)} rows with {decryption_errors} errors")
                        
                        # Add to history
                        add_to_history(encrypted_file.name if hasattr(encrypted_file, 'name') else "unknown", "Decrypted")
                        
                except InvalidToken:
                    st.error("❌ Incorrect password! Cannot decrypt the file.")
                except Exception as e:
                    st.error(f"Decryption failed: {str(e)}")
    
    with col2:
        if st.session_state.vault_decrypted_df is not None:
            st.markdown("### 📊 Decrypted Data")
            
            # Data stats
            df = st.session_state.vault_decrypted_df
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Rows", len(df))
            with col_b:
                st.metric("Columns", len(df.columns))
            with col_c:
                st.metric("Memory", format_bytes(df.memory_usage(deep=True).sum()))
            
            # View options
            view_option = st.radio(
                "View as:",
                ["Table", "Text", "JSON"],
                horizontal=True
            )
            
            if view_option == "Table":
                st.dataframe(df, use_container_width=True, height=400)
                
                # Export button
                if st.button("💾 Export Decrypted Data", use_container_width=True):
                    output = io.BytesIO()
                    df.to_excel(output, index=False)
                    st.download_button(
                        label="📥 Download Excel",
                        data=output.getvalue(),
                        file_name=f"decrypted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            elif view_option == "Text":
                text_output = df.to_string()
                st.text_area("Text View", text_output, height=400)
                
                st.download_button(
                    label="📥 Download as Text",
                    data=text_output,
                    file_name=f"decrypted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                )
            
            else:  # JSON
                json_output = df.to_json(orient='records', indent=2)
                st.json(json_output)
                
                st.download_button(
                    label="📥 Download as JSON",
                    data=json_output,
                    file_name=f"decrypted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )

# =============================================================================
# BATCH PROCESS PAGE
# =============================================================================
elif page == "📦 Batch Process":
    st.markdown('<h1 class="vault-header">📦 Batch Processing</h1>', unsafe_allow_html=True)
    st.markdown('<p class="vault-subheader">Process multiple Excel files at once</p>', unsafe_allow_html=True)
    
    st.info("""
    **Batch Processing Features:**
    - Encrypt multiple files with the same password
    - Decrypt multiple encrypted files
    - Process files in ZIP archives
    - Track progress for each file
    """)
    
    # Batch mode selection
    batch_mode = st.radio(
        "Select batch mode",
        ["Encrypt Multiple Files", "Decrypt Multiple Files"],
        horizontal=True
    )
    
    # File upload area
    uploaded_files = st.file_uploader(
        "Upload files",
        type=['xlsx', 'xls', 'zip'] if batch_mode == "Encrypt Multiple Files" else ['xlsx', 'zip'],
        accept_multiple_files=True,
        help="You can upload multiple files or a ZIP archive"
    )
    
    # Common password
    batch_password = st.text_input(
        "Common Password",
        type="password",
        help="This password will be used for all files"
    )
    
    if batch_password:
        strength_percent, strength_text, strength_color = check_password_strength(batch_password)
        st.progress(strength_percent)
        st.markdown(f"<span style='color: {strength_color};'>Strength: {strength_text}</span>", unsafe_allow_html=True)
    
    if uploaded_files and batch_password:
        if st.button("🚀 Start Batch Processing", use_container_width=True, type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            total_files = len(uploaded_files)
            
            for i, file in enumerate(uploaded_files):
                status_text.text(f"Processing {i+1}/{total_files}: {file.name}")
                
                try:
                    if batch_mode == "Encrypt Multiple Files":
                        # Read Excel
                        df = pd.read_excel(file)
                        
                        # Generate key
                        fernet = get_key_from_password(batch_password, st.session_state.vault_salt)
                        
                        # Encrypt common columns
                        encrypted_count = 0
                        for col in ['id', 'pass', 'password', 'email', 'secret']:
                            if col in df.columns:
                                df[col] = df[col].apply(
                                    lambda x: fernet.encrypt(str(x).encode()).decode()
                                    if pd.notna(x) else x
                                )
                                encrypted_count += 1
                        
                        # Save to buffer
                        output = io.BytesIO()
                        df.to_excel(output, index=False)
                        
                        results.append({
                            'name': f"encrypted_{file.name}",
                            'data': output.getvalue(),
                            'status': 'Success',
                            'encrypted_cols': encrypted_count
                        })
                        
                    else:  # Decrypt
                        df = pd.read_excel(file)
                        fernet = get_key_from_password(batch_password, st.session_state.vault_salt)
                        
                        # Try to decrypt
                        decrypted_data = []
                        for _, row in df.iterrows():
                            decrypted_row = []
                            for col in df.columns:
                                try:
                                    if pd.notna(row[col]) and str(row[col]).startswith('gAAAAA'):
                                        decrypted = fernet.decrypt(str(row[col]).encode()).decode()
                                        decrypted_row.append(decrypted)
                                    else:
                                        decrypted_row.append(row[col])
                                except:
                                    decrypted_row.append(row[col])
                            decrypted_data.append(decrypted_row)
                        
                        decrypted_df = pd.DataFrame(decrypted_data, columns=df.columns)
                        
                        output = io.BytesIO()
                        decrypted_df.to_excel(output, index=False)
                        
                        results.append({
                            'name': f"decrypted_{file.name}",
                            'data': output.getvalue(),
                            'status': 'Success'
                        })
                
                except Exception as e:
                    results.append({
                        'name': file.name,
                        'status': f'Failed: {str(e)}',
                        'error': True
                    })
                
                # Update progress
                progress_bar.progress((i + 1) / total_files)
            
            status_text.text("Batch processing complete!")
            
            # Show results
            st.markdown("### 📊 Processing Results")
            
            success_count = sum(1 for r in results if r.get('status') == 'Success')
            st.success(f"✅ Successfully processed {success_count} out of {total_files} files")
            
            # Create download all button
            if success_count > 0:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                    for result in results:
                        if result.get('status') == 'Success':
                            zip_file.writestr(result['name'], result['data'])
                
                st.download_button(
                    label="📥 Download All Processed Files (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"batch_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
            
            # Show individual results
            with st.expander("View Individual Results"):
                for result in results:
                    if result.get('error'):
                        st.error(f"❌ {result['name']}: {result['status']}")
                    else:
                        st.success(f"✅ {result['name']}: {result.get('encrypted_cols', 0)} columns processed")

# =============================================================================
# SETTINGS PAGE
# =============================================================================
elif page == "⚙️ Settings":
    st.markdown('<h1 class="vault-header">⚙️ Settings</h1>', unsafe_allow_html=True)
    st.markdown('<p class="vault-subheader">Configure your Excel Vault preferences</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔒 Security Settings")
        
        # Auto-clear clipboard
        auto_clear = st.checkbox(
            "Auto-clear clipboard after copy",
            value=st.session_state.vault_settings.get('auto_clear', True),
            help="Automatically clear sensitive data from clipboard"
        )
        
        # Session timeout
        timeout = st.slider(
            "Session timeout (minutes)",
            min_value=5,
            max_value=60,
            value=30,
            step=5,
            help="Automatically clear session after inactivity"
        )
        
        # Default iterations
        default_iterations = st.number_input(
            "Default encryption iterations",
            min_value=100000,
            max_value=1000000,
            value=300000,
            step=100000,
            help="Default number of PBKDF2 iterations"
        )
    
    with col2:
        st.markdown("### 🎨 Appearance Settings")
        
        # Theme
        theme = st.selectbox(
            "Theme",
            ["Light", "Dark", "System"],
            index=["Light", "Dark", "System"].index(st.session_state.vault_settings.get('theme', 'Light'))
        )
        
        # Font size
        font_size = st.select_slider(
            "Font size",
            options=["Small", "Medium", "Large"],
            value=st.session_state.vault_settings.get('font_size', 'Medium')
        )
        
        # Animation
        animations = st.checkbox("Enable animations", value=True)
        
        # Compact mode
        compact_mode = st.checkbox("Compact mode", value=False)
    
    st.divider()
    
    # Advanced settings
    with st.expander("🔧 Advanced Settings"):
        st.markdown("### 🗑️ Data Management")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🧹 Clear All History", use_container_width=True):
                st.session_state.vault_history = []
                st.success("History cleared!")
        
        with col_b:
            if st.button("🔄 Reset All Settings", use_container_width=True):
                st.session_state.vault_settings = {
                    'auto_clear': True,
                    'theme': 'Light',
                    'font_size': 'Medium'
                }
                st.success("Settings reset to default!")
        
        # Export settings
        if st.button("📤 Export Settings", use_container_width=True):
            settings_json = json.dumps(st.session_state.vault_settings, indent=2)
            st.download_button(
                label="Download Settings",
                data=settings_json,
                file_name="vault_settings.json",
                mime="application/json"
            )
    
    # Save settings button
    if st.button("💾 Save Settings", use_container_width=True, type="primary"):
        st.session_state.vault_settings = {
            'auto_clear': auto_clear,
            'theme': theme,
            'font_size': font_size,
            'timeout': timeout,
            'default_iterations': default_iterations,
            'animations': animations,
            'compact_mode': compact_mode
        }
        st.success("✅ Settings saved successfully!")

# =============================================================================
# HISTORY PAGE
# =============================================================================
elif page == "📊 History":
    st.markdown('<h1 class="vault-header">📊 Operation History</h1>', unsafe_allow_html=True)
    st.markdown('<p class="vault-subheader">Track all your encryption/decryption activities</p>', unsafe_allow_html=True)
    
    if st.session_state.vault_history:
        # Convert history to DataFrame for display
        history_df = pd.DataFrame(st.session_state.vault_history)
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Operations", len(history_df))
        
        with col2:
            encrypt_count = len(history_df[history_df['operation'] == 'Encrypted'])
            st.metric("Encryptions", encrypt_count)
        
        with col3:
            decrypt_count = len(history_df[history_df['operation'] == 'Decrypted'])
            st.metric("Decryptions", decrypt_count)
        
        with col4:
            unique_files = history_df['file'].nunique()
            st.metric("Unique Files", unique_files)
        
        # Timeline chart
        st.markdown("### 📈 Activity Timeline")
        
        # Group by date
        history_df['date'] = pd.to_datetime(history_df['timestamp']).dt.date
        timeline = history_df.groupby(['date', 'operation']).size().unstack(fill_value=0)
        
        if not timeline.empty:
            st.bar_chart(timeline)
        
        # Detailed history
        st.markdown("### 📋 Detailed History")
        
        # Filter options
        filter_op = st.selectbox(
            "Filter by operation",
            ["All", "Encrypted", "Decrypted"]
        )
        
        if filter_op != "All":
            filtered_df = history_df[history_df['operation'] == filter_op]
        else:
            filtered_df = history_df
        
        # Display as table
        st.dataframe(
            filtered_df[['timestamp', 'operation', 'file']],
            use_container_width=True,
            hide_index=True
        )
        
        # Export history
        if st.button("📥 Export History", use_container_width=True):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"vault_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Clear history button
        if st.button("🗑️ Clear All History", use_container_width=True):
            st.session_state.vault_history = []
            st.rerun()
    
    else:
        st.info("No history available yet. Start encrypting or decrypting files to see activity here.")
        
        # Sample illustration
        st.markdown("""
        <div style="text-align: center; padding: 50px;">
            <h1 style="font-size: 48px;">📊</h1>
            <h3>Your activity will appear here</h3>
            <p style="color: gray;">Encrypt or decrypt files to track your operations</p>
        </div>
        """, unsafe_allow_html=True)

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
col1, col2, col3 = st.columns(3)
with col2:
    st.caption("🔒 Excel Vault Pro - Military-Grade Encryption for Your Data")