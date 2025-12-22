import sys
import os
import zlib
import struct
import argparse
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.table import Table
from rich import box

import pikepdf
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import scrypt

# --- CẤU HÌNH ---
MAGIC_TAG = b"GHOST_ICC"
console = Console()

# --- ASCII ART BANNER ---
BANNER = """
[bold cyan]
  ▄████  ██░ ██  ▒█████    ██████ ▄▄▄█████▓
 ██▒ ▀█▒▓██░ ██▒▒██▒  ██▒▒██    ▒ ▓  ██▒ ▓▒
▒██░▄▄▄░▒██▀▀██░▒██░  ██▒░ ▓██▄   ▒ ▓██░ ▒░
░▓█  ██▓░▓█ ░██ ▒██   ██░  ▒   ██▒░ ▓██▓ ░ 
░▒▓███▀▒░▓█▒░██▓░ ████▓▒░▒██████▒▒  ▒██▒ ░ 
 ░▒   ▒  ▒ ░░▒░▒░ ▒░▒░▒░ ▒ ▒▓▒ ▒ ░  ▒ ░░   
  ░   ░  ▒ ░▒░ ░  ░ ▒ ▒░ ░ ░▒  ░ ░    ░    
░ ░   ░  ░  ░░ ░░ ░ ░ ▒  ░  ░  ░    ░      
      ░  ░  ░  ░    ░ ░        ░           
[/bold cyan]
[bold white on blue] UNIVERSAL PDF STEGANOGRAPHY TOOL [/bold white on blue]
"""

def derive_key(password, salt):
    return scrypt(password, salt, 32, N=2**14, r=8, p=1)

def prepare_payload(file_path, password=None):
    """Đóng gói dữ liệu (Có mã hóa hoặc Không)"""
    filename = os.path.basename(file_path)
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    # Nén dữ liệu
    compressed_payload = zlib.compress(file_data, level=9)
    
    # Tạo metadata: [LenName(1)][Name][Data]
    filename_bytes = filename.encode('utf-8')
    payload = struct.pack('B', len(filename_bytes)) + filename_bytes + compressed_payload

    if password:
        # Chế độ AN TOÀN (Encrypted)
        mode = b'\x01' # Marker: Mode 1 = Encrypted
        salt = get_random_bytes(16)
        key = derive_key(password, salt)
        nonce = get_random_bytes(12)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(payload)
        # Format: [MAGIC] [Mode] [Salt] [Nonce] [Tag] [Ciphertext]
        final_blob = MAGIC_TAG + mode + salt + nonce + tag + ciphertext
    else:
        # Chế độ KHÔNG MẬT KHẨU (Plain)
        mode = b'\x00' # Marker: Mode 0 = Plain
        # Format: [MAGIC] [Mode] [Payload]
        final_blob = MAGIC_TAG + mode + payload

    return final_blob, len(file_data)

def parse_payload(blob, password=None):
    """Giải nén/Giải mã dữ liệu"""
    if not blob.startswith(MAGIC_TAG):
        return None, None, "Invalid Signature"
    
    offset = len(MAGIC_TAG)
    mode = blob[offset:offset+1]
    offset += 1
    
    decrypted_payload = b""

    if mode == b'\x01': # Encrypted Mode
        if not password:
            return None, None, "Password Required"
        
        salt = blob[offset : offset+16]
        nonce = blob[offset+16 : offset+28]
        tag = blob[offset+28 : offset+44]
        ciphertext = blob[offset+44:]
        
        try:
            key = derive_key(password, salt)
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            decrypted_payload = cipher.decrypt_and_verify(ciphertext, tag)
        except Exception:
            return None, None, "Wrong Password or Corrupted Data"

    elif mode == b'\x00': # Plain Mode
        decrypted_payload = blob[offset:]
    else:
        return None, None, "Unknown Mode"

    # Phân tích cấu trúc [LenName][Name][ZlibData]
    try:
        fname_len = decrypted_payload[0]
        filename = decrypted_payload[1 : 1+fname_len].decode('utf-8')
        compressed_data = decrypted_payload[1+fname_len:]
        original_data = zlib.decompress(compressed_data)
        return filename, original_data, "Success"
    except Exception as e:
        return None, None, f"Decompression Error: {str(e)}"

def embed_process(pdf_in, file_in, pdf_out, password=None):
    with console.status(f"[bold green]Đang nhúng dữ liệu vào {pdf_in}...") as status:
        try:
            # 1. Prepare
            blob, orig_size = prepare_payload(file_in, password)
            
            # 2. Open PDF
            pdf = pikepdf.Pdf.open(pdf_in)
            
            # 3. Inject into OutputIntents (ICC Profile camouflage)
            secret_stream = pikepdf.Stream(pdf, blob, Type="/Metadata", Subtype="/XML")
            
            if "/OutputIntents" not in pdf.Root:
                pdf.Root.OutputIntents = []
                
            intent_entry = pikepdf.Dictionary(
                Type="/OutputIntent",
                S="/GTS_PDFX",
                OutputConditionIdentifier="Ghost_Profile_v2",
                DestOutputProfile=secret_stream
            )
            pdf.Root.OutputIntents.append(intent_entry)
            
            # 4. Save (Disable stream compression to keep file size natural)
            pdf.save(pdf_out, object_stream_mode=pikepdf.ObjectStreamMode.disable)
            
            console.print(f"[bold green]✔ Thành công![/bold green]")
            
            # In bảng thống kê
            table = Table(box=box.ROUNDED)
            table.add_column("Thuộc tính", style="cyan")
            table.add_column("Giá trị", style="magenta")
            table.add_row("File gốc", os.path.basename(pdf_in))
            table.add_row("Dữ liệu ẩn", os.path.basename(file_in))
            table.add_row("Kích thước dữ liệu", f"{orig_size} bytes")
            table.add_row("Mật khẩu", "Có (AES-256)" if password else "Không (Plaintext)")
            table.add_row("Output", pdf_out)
            console.print(table)
            
        except Exception as e:
            console.print(f"[bold red]✘ Lỗi: {e}[/bold red]")

def extract_process(pdf_in, out_dir, password=None):
    with console.status(f"[bold yellow]Đang quét file {pdf_in}...") as status:
        try:
            pdf = pikepdf.Pdf.open(pdf_in)
            found_blob = None
            
            # Quét OutputIntents trước
            if "/OutputIntents" in pdf.Root:
                for intent in pdf.Root.OutputIntents:
                    if "/DestOutputProfile" in intent:
                        raw = intent.DestOutputProfile.read_bytes()
                        if raw.startswith(MAGIC_TAG):
                            found_blob = raw
                            break
            
            # Nếu không thấy, quét toàn bộ (Deep Scan)
            if not found_blob:
                status.update("[bold yellow]Quét sâu toàn bộ object (Deep Scan)...")
                for obj in pdf.objects:
                    if isinstance(obj, pikepdf.Stream):
                        raw = obj.read_bytes()
                        if raw.startswith(MAGIC_TAG):
                            found_blob = raw
                            break
                            
            if not found_blob:
                console.print("[bold red]✘ Không tìm thấy dữ liệu ẩn của Ghost tool![/bold red]")
                return

            # Xử lý blob tìm được
            fname, data, msg = parse_payload(found_blob, password)
            
            if msg == "Password Required":
                console.print("[bold red]! File này có mật khẩu.[/bold red]")
                # Nếu chạy mode interactive thì hỏi pass, nếu CLI thì báo lỗi
                if password is None:
                    inp_pass = Prompt.ask("Nhập mật khẩu giải mã", password=True)
                    fname, data, msg = parse_payload(found_blob, inp_pass)

            if fname:
                out_path = os.path.join(out_dir, fname)
                with open(out_path, 'wb') as f:
                    f.write(data)
                console.print(f"[bold green]✔ Trích xuất thành công: {out_path}[/bold green]")
            else:
                console.print(f"[bold red]✘ Thất bại: {msg}[/bold red]")

        except Exception as e:
            console.print(f"[bold red]✘ Lỗi: {e}[/bold red]")

def interactive_mode():
    """Giao diện Wizard hỏi đáp"""
    console.print(BANNER)
    console.print("[1] Ẩn dữ liệu (Embed)", style="bold green")
    console.print("[2] Trích xuất dữ liệu (Extract)", style="bold yellow")
    console.print("[3] Thoát", style="bold red")
    
    choice = Prompt.ask("Lựa chọn", choices=["1", "2", "3"], default="1")
    
    if choice == "3":
        sys.exit()
        
    if choice == "1":
        pdf_in = Prompt.ask("Đường dẫn PDF gốc")
        while not os.path.exists(pdf_in):
            console.print("[red]File không tồn tại![/red]")
            pdf_in = Prompt.ask("Đường dẫn PDF gốc")
            
        file_in = Prompt.ask("File cần ẩn")
        while not os.path.exists(file_in):
            console.print("[red]File không tồn tại![/red]")
            file_in = Prompt.ask("File cần ẩn")
            
        pdf_out = Prompt.ask("Tên file PDF đầu ra", default="output_stego.pdf")
        
        use_pass = Confirm.ask("Bạn có muốn đặt mật khẩu không?")
        password = None
        if use_pass:
            password = Prompt.ask("Nhập mật khẩu", password=True)
            
        embed_process(pdf_in, file_in, pdf_out, password)
        
    elif choice == "2":
        pdf_in = Prompt.ask("File PDF cần giải mã")
        out_dir = Prompt.ask("Thư mục lưu file", default=".")
        password = Prompt.ask("Mật khẩu (Enter để bỏ qua)", password=True)
        if password == "": password = None
        
        extract_process(pdf_in, out_dir, password)

def main():
    parser = argparse.ArgumentParser(description="Ghost ICC Stego Tool")
    subparsers = parser.add_subparsers(dest='cmd')
    
    # CLI Arguments setup
    embed_p = subparsers.add_parser('embed')
    embed_p.add_argument('pdf_in')
    embed_p.add_argument('payload')
    embed_p.add_argument('pdf_out')
    embed_p.add_argument('-p', '--password', default=None, help="Để trống nếu không muốn đặt pass")

    extract_p = subparsers.add_parser('extract')
    extract_p.add_argument('pdf_in')
    extract_p.add_argument('-o', '--outdir', default='.')
    extract_p.add_argument('-p', '--password', default=None)

    # Nếu không có tham số -> Chạy Interactive Mode
    if len(sys.argv) == 1:
        interactive_mode()
    else:
        # Chạy CLI Mode (để dùng trong script/automation)
        args = parser.parse_args()
        if args.cmd == 'embed':
            embed_process(args.pdf_in, args.payload, args.pdf_out, args.password)
        elif args.cmd == 'extract':
            extract_process(args.pdf_in, args.outdir, args.password)

if __name__ == "__main__":
    main()