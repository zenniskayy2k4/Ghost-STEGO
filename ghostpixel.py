import sys
import os
import zlib
import struct
import argparse
import pikepdf

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import scrypt

# --- CẤU HÌNH ---
# Magic Signature để nhận diện "Profile màu" của chúng ta
# Giả dạng header của ICC profile nhưng có đánh dấu riêng
MAGIC_TAG = b"GHOST_ICC"

def derive_key(password, salt):
    """Tạo key 32 bytes từ password bằng Scrypt (Chống Brute-force)"""
    return scrypt(password, salt, 32, N=2**14, r=8, p=1)

def encrypt_data(file_path, password):
    """
    Nén -> Encrypt (AES-GCM) -> Đóng gói
    """
    # 1. Đọc và nén file cần ẩn
    filename = os.path.basename(file_path)
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    # Nén mức cao nhất
    compressed_payload = zlib.compress(file_data, level=9)
    
    # Tạo header chứa tên file gốc (để khi giải nén còn biết tên)
    # Format: [LenTên(1)] [TênFile] [DataNén]
    filename_bytes = filename.encode('utf-8')
    payload = struct.pack('B', len(filename_bytes)) + filename_bytes + compressed_payload

    # 2. Mã hóa
    salt = get_random_bytes(16)
    key = derive_key(password, salt)
    nonce = get_random_bytes(12)
    
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(payload)
    
    # 3. Đóng gói binary blob
    # Structure: [MAGIC_TAG] + [Salt] + [Nonce] + [Tag] + [Ciphertext]
    final_blob = MAGIC_TAG + salt + nonce + tag + ciphertext
    return final_blob

def decrypt_data(blob, password):
    """
    Tách gói -> Decrypt -> Giải nén
    """
    try:
        # Kiểm tra Magic Tag
        if not blob.startswith(MAGIC_TAG):
            return None, None
            
        offset = len(MAGIC_TAG)
        salt = blob[offset : offset+16]
        nonce = blob[offset+16 : offset+28]
        tag = blob[offset+28 : offset+44]
        ciphertext = blob[offset+44:]
        
        # Giải mã
        key = derive_key(password, salt)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        decrypted_payload = cipher.decrypt_and_verify(ciphertext, tag)
        
        # Tách tên file và dữ liệu
        fname_len = decrypted_payload[0]
        filename = decrypted_payload[1 : 1+fname_len].decode('utf-8')
        compressed_data = decrypted_payload[1+fname_len:]
        
        # Giải nén
        original_data = zlib.decompress(compressed_data)
        
        return filename, original_data
        
    except Exception as e:
        # Sai pass hoặc lỗi data
        return None, None

def embed(pdf_in, file_to_hide, pdf_out, password):
    print(f"[*] Đang xử lý PDF: {pdf_in}")
    
    try:
        # 1. Mã hóa dữ liệu
        secret_blob = encrypt_data(file_to_hide, password)
        print(f"[*] Đã mã hóa dữ liệu ({len(secret_blob)} bytes).")

        # 2. Mở file PDF
        pdf = pikepdf.Pdf.open(pdf_in)

        # 3. Tạo một Stream Object mới chứa dữ liệu bí mật
        # Chúng ta ngụy trang nó thành một "OutputIntent" (Cấu hình in ấn)
        # Đây là cấu trúc hoàn toàn hợp lệ của PDF
        secret_stream = pikepdf.Stream(
            pdf, 
            secret_blob, 
            Type="/Metadata",   # Hoặc /EmbeddedFile, nhưng Metadata ít bị nghi ngờ
            Subtype="/XML"      # Fake subtype
        )

        # 4. Gắn Stream này vào Root của PDF dưới dạng một OutputIntent giả
        # Nếu PDF chưa có OutputIntents, tạo mới
        if "/OutputIntents" not in pdf.Root:
            pdf.Root.OutputIntents = []

        # Tạo Dictionary cấu hình cho Intent giả này
        intent_entry = pikepdf.Dictionary(
            Type="/OutputIntent",
            S="/GTS_PDFX",             # Chuẩn PDF/X (in ấn)
            OutputConditionIdentifier="Custom_Security_Profile",
            DestOutputProfile=secret_stream # Trỏ tới dữ liệu bí mật của ta
        )

        # Thêm vào mảng OutputIntents
        pdf.Root.OutputIntents.append(intent_entry)

        # 5. Lưu file
        # object_stream_mode=pikepdf.ObjectStreamMode.generate giúp nén cấu trúc PDF tối đa
        # pdf.save(pdf_out, object_stream_mode=pikepdf.ObjectStreamMode.generate)
        pdf.save(pdf_out, object_stream_mode=pikepdf.ObjectStreamMode.disable)

        print(f"[SUCCESS] Đã ẩn file vào cấu trúc OutputIntent của PDF: {pdf_out}")

    except Exception as e:
        print(f"[ERROR] Lỗi khi ẩn file: {e}")

def extract(pdf_in, out_dir, password):
    print(f"[*] Đang quét PDF: {pdf_in}")
    
    try:
        pdf = pikepdf.Pdf.open(pdf_in)
        
        found = False
        
        # 1. Tìm trong OutputIntents (Nơi ta giấu mặc định)
        if "/OutputIntents" in pdf.Root:
            for intent in pdf.Root.OutputIntents:
                try:
                    # Lấy stream profile
                    if "/DestOutputProfile" in intent:
                        stream_obj = intent.DestOutputProfile
                        raw_data = stream_obj.read_bytes()
                        
                        # Thử giải mã
                        fname, data = decrypt_data(raw_data, password)
                        if fname:
                            # Lưu file
                            out_path = os.path.join(out_dir, fname)
                            with open(out_path, 'wb') as f:
                                f.write(data)
                            print(f"[SUCCESS] Tìm thấy và giải mã thành công: {out_path}")
                            found = True
                            break
                except Exception:
                    continue
        
        # Fallback: Nếu không tìm thấy trong Intent, quét toàn bộ Objects (dành cho CTF nâng cao)
        if not found:
            print("[*] Không tìm thấy ở vị trí chuẩn, đang quét sâu toàn bộ PDF...")
            for obj in pdf.objects:
                try:
                    if isinstance(obj, pikepdf.Stream):
                        raw_data = obj.read_bytes()
                        if raw_data.startswith(MAGIC_TAG):
                            fname, data = decrypt_data(raw_data, password)
                            if fname:
                                out_path = os.path.join(out_dir, fname)
                                with open(out_path, 'wb') as f:
                                    f.write(data)
                                print(f"[SUCCESS] Tìm thấy dữ liệu ẩn sâu trong Object {obj.objid}: {out_path}")
                                found = True
                                break
                except:
                    continue

        if not found:
            print("[FAIL] Không tìm thấy dữ liệu ẩn hoặc sai mật khẩu.")

    except Exception as e:
        print(f"[ERROR] {e}")

def main():
    parser = argparse.ArgumentParser(description="Universal PDF Stego (ICC Profile Injection)")
    subparsers = parser.add_subparsers(dest='cmd', required=True)
    
    # Embed
    embed_p = subparsers.add_parser('embed')
    embed_p.add_argument('pdf_in')
    embed_p.add_argument('payload')
    embed_p.add_argument('pdf_out')
    embed_p.add_argument('-p', '--password', required=True)
    
    # Extract
    extract_p = subparsers.add_parser('extract')
    extract_p.add_argument('pdf_in')
    extract_p.add_argument('-o', '--outdir', default='.')
    extract_p.add_argument('-p', '--password', required=True)
    
    args = parser.parse_args()
    
    if args.cmd == 'embed':
        embed(args.pdf_in, args.payload, args.pdf_out, args.password)
    elif args.cmd == 'extract':
        extract(args.pdf_in, args.outdir, args.password)

if __name__ == "__main__":
    main()