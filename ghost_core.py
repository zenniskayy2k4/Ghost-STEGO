import os
import zlib
import struct
import pikepdf
import shutil
import tempfile
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import scrypt

# Cấu hình
MAGIC_TAG = b"GHOST_ICC"

class GhostCore:
    @staticmethod
    def derive_key(password, salt):
        return scrypt(password, salt, 32, N=2**14, r=8, p=1)

    @staticmethod
    def process_input(input_path):
        """
        Nếu là File: Trả về đường dẫn file và False (không phải file tạm).
        Nếu là Folder: Nén lại thành Zip, trả về đường dẫn Zip và True (là file tạm).
        """
        if os.path.isfile(input_path):
            return input_path, False
        
        elif os.path.isdir(input_path):
            # Tạo file zip tạm thời
            temp_dir = tempfile.gettempdir()
            folder_name = os.path.basename(os.path.normpath(input_path))
            base_name = os.path.join(temp_dir, folder_name)
            
            # Tạo zip: base_name + .zip
            zip_path = shutil.make_archive(base_name, 'zip', input_path)
            return zip_path, True
        else:
            raise FileNotFoundError(f"Đường dẫn không tồn tại: {input_path}")
    
    @staticmethod
    def prepare_payload(input_path, password=None):
        """Chuẩn bị blob dữ liệu để nhúng"""
        # 1. Xử lý file/folder
        actual_file, is_temp = GhostCore.process_input(input_path)
        
        try:
            filename = os.path.basename(actual_file)
            with open(actual_file, 'rb') as f:
                file_data = f.read()
            
            # Nén lần 2 (Zlib) - Dù Zip đã nén nhưng Zlib giúp đóng gói gọn hơn cho cấu trúc binary
            compressed_payload = zlib.compress(file_data, level=9)
            
            # Metadata
            filename_bytes = filename.encode('utf-8')
            payload = struct.pack('B', len(filename_bytes)) + filename_bytes + compressed_payload

            if password:
                mode = b'\x01'
                salt = get_random_bytes(16)
                key = GhostCore.derive_key(password, salt)
                nonce = get_random_bytes(12)
                cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
                ciphertext, tag = cipher.encrypt_and_digest(payload)
                final_blob = MAGIC_TAG + mode + salt + nonce + tag + ciphertext
            else:
                mode = b'\x00'
                final_blob = MAGIC_TAG + mode + payload
                
            return final_blob, len(file_data)
        
        finally:
            # Dọn dẹp file zip tạm nếu có
            if is_temp and os.path.exists(actual_file):
                os.remove(actual_file)

    @staticmethod
    def parse_payload(blob, password=None):
        """Phân tích blob dữ liệu lấy từ PDF"""
        if not blob.startswith(MAGIC_TAG):
            raise ValueError("Invalid Signature")
        
        offset = len(MAGIC_TAG)
        mode = blob[offset:offset+1]
        offset += 1
        
        decrypted_payload = b""

        if mode == b'\x01': # Encrypted
            if not password:
                raise PermissionError("Password Required")
            
            salt = blob[offset : offset+16]
            nonce = blob[offset+16 : offset+28]
            tag = blob[offset+28 : offset+44]
            ciphertext = blob[offset+44:]
            
            try:
                key = GhostCore.derive_key(password, salt)
                cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
                decrypted_payload = cipher.decrypt_and_verify(ciphertext, tag)
            except Exception:
                raise ValueError("Wrong Password or Corrupted Data")

        elif mode == b'\x00': # Plain
            decrypted_payload = blob[offset:]
        else:
            raise ValueError("Unknown Mode")

        # Giải nén cấu trúc
        try:
            fname_len = decrypted_payload[0]
            filename = decrypted_payload[1 : 1+fname_len].decode('utf-8')
            compressed_data = decrypted_payload[1+fname_len:]
            original_data = zlib.decompress(compressed_data)
            return filename, original_data
        except Exception as e:
            raise RuntimeError(f"Decompression Error: {str(e)}")

    @staticmethod
    def embed(pdf_in, file_in, pdf_out, password=None):
        blob, orig_size = GhostCore.prepare_payload(file_in, password)
        
        pdf = pikepdf.Pdf.open(pdf_in)
        
        # Tạo OutputIntent giả
        secret_stream = pikepdf.Stream(pdf, blob, Type="/Metadata", Subtype="/XML")
        
        if "/OutputIntents" not in pdf.Root:
            pdf.Root.OutputIntents = []
            
        intent_entry = pikepdf.Dictionary(
            Type="/OutputIntent",
            S="/GTS_PDFX",
            OutputConditionIdentifier="Ghost_Profile",
            DestOutputProfile=secret_stream
        )
        pdf.Root.OutputIntents.append(intent_entry)
        
        # Lưu file (Disable compression để giữ size thật)
        pdf.save(pdf_out, object_stream_mode=pikepdf.ObjectStreamMode.disable)
        return orig_size

    @staticmethod
    def extract_search(pdf_in):
        """Tìm blob dữ liệu trong PDF"""
        pdf = pikepdf.Pdf.open(pdf_in)
        
        # Quét OutputIntents (Nhanh)
        if "/OutputIntents" in pdf.Root:
            for intent in pdf.Root.OutputIntents:
                if "/DestOutputProfile" in intent:
                    raw = intent.DestOutputProfile.read_bytes()
                    if raw.startswith(MAGIC_TAG):
                        return raw
        
        # Quét sâu (Chậm)
        for obj in pdf.objects:
            if isinstance(obj, pikepdf.Stream):
                raw = obj.read_bytes()
                if raw.startswith(MAGIC_TAG):
                    return raw
        return None