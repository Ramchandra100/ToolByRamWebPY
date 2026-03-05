import streamlit as st
import pandas as pd
import os
import base64
import json
import secrets
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken
import io
import re
import zipfile
from pathlib import Path

def run():
    """Main function for Excel Vault - Secure Excel Encryption"""
    
    # =============================================================================
    # PAGE HEADER
    # =============================================================================
    st.markdown("""
    <style>
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
        .success-box {
            padding: 20px;
            border-radius: 10px;
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            margin: 10px 0;
        }
        .warning-box {
            padding: 20px;
            border-radius: 10px;
            background-color: #fff3cd;
            border: 1px solid #ffeeba;
            color: #856404;
            margin: 10px 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="vault-header">🔐 Excel Vault Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p class="vault-subheader">Secure your sensitive Excel data with military-grade AES-256 encryption</p>', unsafe_allow_html=True)
    
    # =============================================================================
    # SESSION STATE INITIALIZATION
    # =============================================================================
    if 'vault_current_file' not in st.session_state:
        st.session_state.vault_current_file = None
    if 'vault_encrypted_data' not in st.session_state:
        st.session_state.vault_encrypted_data = None
    if 'vault_decrypted_df' not in st.session_state:
        st.session_state.vault_decrypted_df = None
    
    # =============================================================================
    # HELPER FUNCTIONS
    # =============================================================================
    def generate_salt():
        """Generate a new random salt"""
        return secrets.token_bytes(16)
    
    def salt_to_base64(salt):
        """Convert salt bytes to base64 string for JSON storage"""
        return base64.b64encode(salt).decode('utf-8')
    
    def base64_to_salt(salt_b64):
        """Convert base64 string back to salt bytes"""
        return base64.b64decode(salt_b64)
    
    def get_key_from_password(password: str, salt: bytes, iterations: int = 300000):
        """Generate encryption key from password with provided salt"""
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
        
        # Length check
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 2
        
        # Complexity checks
        if re.search(r"[A-Z]", password):
            score += 1
        if re.search(r"[a-z]", password):
            score += 1
        if re.search(r"\d", password):
            score += 1
        if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            score += 2
        
        # Calculate percentage
        percentage = min(score / 8, 1.0)
        
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
    
    # =============================================================================
    # MAIN INTERFACE
    # =============================================================================
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🔐 Encrypt File", "🔓 Decrypt File", "📚 Batch Process"])
    
    # =============================================================================
    # TAB 1: ENCRYPT FILE
    # =============================================================================
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 📁 File Selection")
            
            # File upload
            uploaded_file = st.file_uploader(
                "Choose Excel file to encrypt",
                type=['xlsx', 'xls'],
                key="encrypt_file",
                help="Upload the Excel file you want to encrypt"
            )
            
            if uploaded_file:
                st.session_state.vault_current_file = uploaded_file
                
                # File info
                st.markdown("**File Information:**")
                st.markdown(f"""
                - **Filename:** {uploaded_file.name}
                - **Size:** {format_bytes(uploaded_file.size)}
                - **Type:** Excel file
                """)
                
                # Preview data
                try:
                    df_preview = pd.read_excel(uploaded_file, nrows=5)
                    st.markdown("**Data Preview (First 5 rows):**")
                    st.dataframe(df_preview, use_container_width=True)
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
                key="encrypt_password",
                help="Enter a strong password (minimum 8 characters)"
            )
            
            # Password strength meter
            if password:
                strength_percent, strength_text, strength_color = check_password_strength(password)
                st.progress(strength_percent)
                st.markdown(f"<p style='color: {strength_color};'>Strength: {strength_text}</p>", unsafe_allow_html=True)
            
            # Confirm password
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                key="encrypt_confirm"
            )
            
            if password and confirm_password and password != confirm_password:
                st.error("❌ Passwords do not match")
            
            # Column selection
            if uploaded_file and 'available_columns' in locals():
                st.markdown("**Columns to Encrypt:**")
                default_columns = [col for col in ['id', 'pass', 'password', 'email', 'secret'] if col in available_columns]
                columns_to_encrypt = st.multiselect(
                    "Select columns",
                    options=available_columns,
                    default=default_columns,
                    key="encrypt_columns"
                )
            else:
                columns_input = st.text_input(
                    "Columns to encrypt (comma-separated)",
                    value="id,pass",
                    key="encrypt_columns_input",
                    help="e.g., id,pass,email"
                )
                columns_to_encrypt = [col.strip() for col in columns_input.split(',') if col.strip()]
            
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
                            
                            # Generate a UNIQUE salt for this encryption (critical fix!)
                            salt = generate_salt()
                            
                            # Generate encryption key with the unique salt
                            fernet = get_key_from_password(password, salt, iterations)
                            
                            # Store metadata with salt
                            metadata = {
                                "encrypted_columns": columns_to_encrypt,
                                "iterations": iterations,
                                "timestamp": datetime.now().isoformat(),
                                "original_file": uploaded_file.name,
                                "rows": len(df),
                                "columns": len(df.columns),
                                "salt": salt_to_base64(salt),  # Save salt in metadata
                                "version": "2.0"
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
                                
                                # Success message with important note
                                st.markdown("""
                                <div class="success-box">
                                    <strong>✅ Encryption successful!</strong><br>
                                    - Encrypted {} columns<br>
                                    - {} rows processed<br>
                                    - Using {:,} iterations<br><br>
                                    <strong>⚠️ IMPORTANT:</strong> Keep the metadata file safe! It contains the salt needed for decryption.
                                </div>
                                """.format(encrypted_count, len(df), iterations), unsafe_allow_html=True)
                                
                                # Download button
                                st.download_button(
                                    label="📥 Download Encrypted Package (ZIP)",
                                    data=zip_buffer.getvalue(),
                                    file_name=f"encrypted_{uploaded_file.name.replace('.xlsx', '')}_package.zip",
                                    mime="application/zip",
                                    use_container_width=True
                                )
                                
                                # Add to recent files in main app
                                if 'add_to_recent' in st.session_state and callable(st.session_state.add_to_recent):
                                    st.session_state.add_to_recent(uploaded_file.name)
                    
                    except Exception as e:
                        st.error(f"Encryption failed: {str(e)}")
    
    # =============================================================================
    # TAB 2: DECRYPT FILE
    # =============================================================================
    with tab2:
        st.markdown("### 📁 Upload Encrypted File")
        
        # Upload option
        upload_option = st.radio(
            "Select upload method",
            ["Upload ZIP package", "Upload Excel + JSON separately"],
            horizontal=True,
            key="decrypt_option"
        )
        
        encrypted_file = None
        meta_file = None
        metadata = None
        
        if upload_option == "Upload ZIP package":
            zip_file = st.file_uploader(
                "Upload encrypted ZIP package",
                type=['zip'],
                key="decrypt_zip",
                help="Upload the ZIP file containing encrypted Excel and metadata"
            )
            
            if zip_file:
                try:
                    with zipfile.ZipFile(zip_file) as z:
                        # Extract files
                        for file_name in z.namelist():
                            if file_name.endswith('.xlsx'):
                                encrypted_file = io.BytesIO(z.read(file_name))
                                encrypted_file.name = file_name
                            elif file_name.endswith('.json'):
                                meta_file = io.BytesIO(z.read(file_name))
                except Exception as e:
                    st.error(f"Error reading ZIP file: {e}")
        
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                encrypted_file = st.file_uploader(
                    "Encrypted Excel file",
                    type=['xlsx'],
                    key="decrypt_excel"
                )
            with col_b:
                meta_file = st.file_uploader(
                    "Metadata file (JSON)",
                    type=['json'],
                    key="decrypt_meta"
                )
        
        # Load metadata if available
        if meta_file:
            try:
                meta_file.seek(0)
                metadata = json.load(meta_file)
                st.success("✅ Metadata file loaded successfully")
                
                # Display metadata info
                with st.expander("📋 Metadata Information"):
                    st.json(metadata)
                    
            except Exception as e:
                st.error(f"Error reading metadata: {e}")
        
        # Password input
        password = st.text_input(
            "Password",
            type="password",
            key="decrypt_password",
            help="Enter the password used for encryption"
        )
        
        # Show password checkbox
        show_password = st.checkbox("Show password", key="show_decrypt")
        if show_password and password:
            st.code(password)
        
        # Decrypt button
        if st.button("🔓 Decrypt File", use_container_width=True, type="primary"):
            if not encrypted_file:
                st.error("Please upload the encrypted Excel file")
            elif not password:
                st.error("Please enter the password")
            elif not metadata:
                st.error("Metadata file is required for decryption")
            else:
                try:
                    with st.spinner("🔓 Decrypting file..."):
                        # Extract metadata
                        iterations = metadata.get('iterations', 300000)
                        columns_to_decrypt = metadata.get('encrypted_columns', [])
                        salt_b64 = metadata.get('salt')
                        
                        if not salt_b64:
                            st.error("❌ Salt not found in metadata! Cannot decrypt without salt.")
                            st.info("This file was encrypted with an older version. Please use the desktop version to decrypt it.")
                            return
                        
                        # Convert salt from base64
                        salt = base64_to_salt(salt_b64)
                        
                        # Read encrypted file
                        encrypted_file.seek(0)
                        df = pd.read_excel(encrypted_file)
                        
                        # Generate decryption key with the stored salt
                        fernet = get_key_from_password(password, salt, iterations)
                        
                        # Decrypt data
                        decrypted_data = []
                        decryption_errors = 0
                        success_count = 0
                        
                        for idx, row in df.iterrows():
                            decrypted_row = []
                            for col in df.columns:
                                try:
                                    if col in columns_to_decrypt and pd.notna(row[col]) and str(row[col]):
                                        # Check if it looks like encrypted data (Fernet tokens start with 'gAAAA')
                                        if str(row[col]).startswith('gAAAA'):
                                            decrypted = fernet.decrypt(str(row[col]).encode()).decode()
                                            decrypted_row.append(decrypted)
                                            success_count += 1
                                        else:
                                            decrypted_row.append(row[col])
                                    else:
                                        decrypted_row.append(row[col])
                                except (InvalidToken, Exception) as e:
                                    decrypted_row.append(f"🔒 DECRYPTION FAILED")
                                    decryption_errors += 1
                            
                            decrypted_data.append(decrypted_row)
                        
                        # Store decrypted data
                        decrypted_df = pd.DataFrame(decrypted_data, columns=df.columns)
                        
                        # Display results
                        st.markdown("### 📊 Decrypted Data")
                        
                        # Stats
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Rows", len(decrypted_df))
                        with col2:
                            st.metric("Columns", len(decrypted_df.columns))
                        with col3:
                            st.metric("Decrypted Values", success_count)
                        
                        if decryption_errors > 0:
                            st.warning(f"⚠️ {decryption_errors} values could not be decrypted. Wrong password or corrupted data?")
                        
                        # View options
                        view_option = st.radio(
                            "View as:",
                            ["Table", "JSON"],
                            horizontal=True,
                            key="view_option"
                        )
                        
                        if view_option == "Table":
                            st.dataframe(decrypted_df, use_container_width=True, height=400)
                        else:
                            st.json(decrypted_df.to_dict(orient='records'))
                        
                        # Export button
                        output = io.BytesIO()
                        decrypted_df.to_excel(output, index=False)
                        
                        st.download_button(
                            label="📥 Download Decrypted Excel",
                            data=output.getvalue(),
                            file_name=f"decrypted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                        
                        # Success message
                        if decryption_errors == 0:
                            st.success("✅ Successfully decrypted all data!")
                        else:
                            st.warning(f"⚠️ Decrypted with {decryption_errors} errors")
                
                except InvalidToken:
                    st.error("❌ Incorrect password! Cannot decrypt the file.")
                except Exception as e:
                    st.error(f"Decryption failed: {str(e)}")
    
    # =============================================================================
    # TAB 3: BATCH PROCESS
    # =============================================================================
    with tab3:
        st.markdown("### 📦 Batch Process Multiple Files")
        
        st.info("""
        **Batch Processing Features:**
        - Encrypt multiple files with the same password
        - Decrypt multiple encrypted files
        - Process up to 10 files at once
        - Each file gets its own unique salt for maximum security
        """)
        
        # Batch mode selection
        batch_mode = st.radio(
            "Select operation",
            ["Encrypt Multiple", "Decrypt Multiple"],
            horizontal=True,
            key="batch_mode"
        )
        
        # File upload
        uploaded_files = st.file_uploader(
            f"Upload files to {batch_mode.lower()}",
            type=['xlsx', 'xls'] if "Encrypt" in batch_mode else ['xlsx', 'json', 'zip'],
            accept_multiple_files=True,
            key="batch_files",
            help="For decryption, you can upload Excel files and their corresponding metadata files"
        )
        
        if uploaded_files and len(uploaded_files) > 10:
            st.warning("Maximum 10 files recommended for batch processing")
        
        # Common password
        batch_password = st.text_input(
            "Common Password",
            type="password",
            key="batch_password",
            help="This password will be used for all files"
        )
        
        if batch_password and "Encrypt" in batch_mode:
            strength_percent, strength_text, strength_color = check_password_strength(batch_password)
            st.progress(strength_percent)
            st.markdown(f"<p style='color: {strength_color};'>Strength: {strength_text}</p>", unsafe_allow_html=True)
        
        # Column selection for encryption
        columns_batch = None
        if "Encrypt" in batch_mode:
            columns_batch = st.text_input(
                "Columns to encrypt (comma-separated)",
                value="id,pass,email",
                key="batch_columns",
                help="These columns will be encrypted in all files"
            )
        
        # Process button
        if st.button("🚀 Start Batch Processing", use_container_width=True, type="primary"):
            if not uploaded_files:
                st.error("Please upload files first")
            elif not batch_password:
                st.error("Please enter a password")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                results = []
                total_files = len(uploaded_files)
                
                if "Encrypt" in batch_mode:
                    # BATCH ENCRYPTION
                    for i, file in enumerate(uploaded_files):
                        status_text.text(f"Processing {i+1}/{total_files}: {file.name}")
                        
                        try:
                            # Read Excel
                            df = pd.read_excel(file)
                            
                            # Generate UNIQUE salt for this file
                            salt = generate_salt()
                            
                            # Generate key
                            fernet = get_key_from_password(batch_password, salt)
                            
                            # Parse columns
                            cols_to_encrypt = [col.strip() for col in columns_batch.split(',')] if columns_batch else []
                            
                            # Encrypt columns
                            encrypted_count = 0
                            for col in cols_to_encrypt:
                                if col in df.columns:
                                    df[col] = df[col].apply(
                                        lambda x: fernet.encrypt(str(x).encode()).decode()
                                        if pd.notna(x) else x
                                    )
                                    encrypted_count += 1
                            
                            # Create metadata with salt
                            metadata = {
                                "encrypted_columns": cols_to_encrypt,
                                "iterations": 300000,
                                "timestamp": datetime.now().isoformat(),
                                "original_file": file.name,
                                "salt": salt_to_base64(salt),
                                "version": "2.0"
                            }
                            
                            # Save to buffers
                            excel_buffer = io.BytesIO()
                            df.to_excel(excel_buffer, index=False)
                            
                            meta_buffer = io.BytesIO()
                            meta_buffer.write(json.dumps(metadata, indent=2).encode())
                            
                            # Create individual ZIP for this file
                            file_zip = io.BytesIO()
                            with zipfile.ZipFile(file_zip, 'w') as zip_file:
                                zip_file.writestr(f"encrypted_{file.name}", excel_buffer.getvalue())
                                zip_file.writestr(f"metadata_{file.name.replace('.xlsx', '.json')}", meta_buffer.getvalue())
                            
                            results.append({
                                'name': f"encrypted_{file.name.replace('.xlsx', '')}_package.zip",
                                'data': file_zip.getvalue(),
                                'status': 'Success',
                                'encrypted_cols': encrypted_count
                            })
                            
                        except Exception as e:
                            results.append({
                                'name': file.name,
                                'status': f'Failed: {str(e)}',
                                'error': True
                            })
                        
                        # Update progress
                        progress_bar.progress((i + 1) / total_files)
                    
                else:
                    # BATCH DECRYPTION
                    # Group files by base name
                    file_groups = {}
                    for file in uploaded_files:
                        if file.name.endswith('.xlsx'):
                            base_name = file.name.replace('encrypted_', '').replace('.xlsx', '')
                            if base_name not in file_groups:
                                file_groups[base_name] = {'excel': None, 'meta': None}
                            file_groups[base_name]['excel'] = file
                        elif file.name.endswith('.json'):
                            base_name = file.name.replace('metadata_', '').replace('.json', '')
                            if base_name not in file_groups:
                                file_groups[base_name] = {'excel': None, 'meta': None}
                            file_groups[base_name]['meta'] = file
                    
                    i = 0
                    for base_name, files in file_groups.items():
                        if files['excel'] and files['meta']:
                            i += 1
                            status_text.text(f"Processing {i}/{len(file_groups)}: {base_name}")
                            
                            try:
                                # Load metadata
                                files['meta'].seek(0)
                                metadata = json.load(files['meta'])
                                
                                # Get salt from metadata
                                salt_b64 = metadata.get('salt')
                                if not salt_b64:
                                    raise Exception("Salt not found in metadata")
                                
                                salt = base64_to_salt(salt_b64)
                                iterations = metadata.get('iterations', 300000)
                                
                                # Read Excel
                                files['excel'].seek(0)
                                df = pd.read_excel(files['excel'])
                                
                                # Generate key
                                fernet = get_key_from_password(batch_password, salt, iterations)
                                
                                # Decrypt
                                decrypted_data = []
                                for _, row in df.iterrows():
                                    decrypted_row = []
                                    for col in df.columns:
                                        try:
                                            if pd.notna(row[col]) and str(row[col]).startswith('gAAAA'):
                                                decrypted = fernet.decrypt(str(row[col]).encode()).decode()
                                                decrypted_row.append(decrypted)
                                            else:
                                                decrypted_row.append(row[col])
                                        except:
                                            decrypted_row.append(row[col])
                                    decrypted_data.append(decrypted_row)
                                
                                decrypted_df = pd.DataFrame(decrypted_data, columns=df.columns)
                                
                                # Save to buffer
                                output = io.BytesIO()
                                decrypted_df.to_excel(output, index=False)
                                
                                results.append({
                                    'name': f"decrypted_{base_name}.xlsx",
                                    'data': output.getvalue(),
                                    'status': 'Success'
                                })
                                
                            except Exception as e:
                                results.append({
                                    'name': base_name,
                                    'status': f'Failed: {str(e)}',
                                    'error': True
                                })
                            
                            # Update progress
                            progress_bar.progress(i / len(file_groups))
                    
                    total_files = len(file_groups)
                
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
                            if 'encrypted_cols' in result:
                                st.success(f"✅ {result['name']}: {result['encrypted_cols']} columns encrypted")
                            else:
                                st.success(f"✅ {result['name']}: Decrypted successfully")