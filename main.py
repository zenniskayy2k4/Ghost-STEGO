import argparse
import sys
import os
import zipfile
from ghost_ui import GhostUI
from ghost_core import GhostCore

def main():
    # Cấu hình tham số dòng lệnh (CLI arguments)
    parser = argparse.ArgumentParser(description="Ghost Stegography PDF Tool")
    subparsers = parser.add_subparsers(dest='cmd')
    
    embed_p = subparsers.add_parser('embed', help="Chế độ dòng lệnh: Ẩn file")
    embed_p.add_argument('pdf_in')
    embed_p.add_argument('payload', nargs='+', help="Danh sách file hoặc folder cần ẩn")
    embed_p.add_argument('pdf_out')
    embed_p.add_argument('-p', '--password', default=None)

    extract_p = subparsers.add_parser('extract', help="Chế độ dòng lệnh: Trích xuất file ẩn")
    extract_p.add_argument('pdf_in')
    extract_p.add_argument('-o', '--outdir', default='.')
    extract_p.add_argument('-p', '--password', default=None)

    args = parser.parse_args()

    # Nếu có tham số dòng lệnh -> Chạy 1 lần rồi thoát (cho script)
    # Nếu không có tham số -> Chạy giao diện vòng lặp (cho người dùng)
    if args.cmd:
        try:
            if args.cmd == 'embed':
                # 1. Kiểm tra File PDF gốc có tồn tại không
                if not os.path.exists(args.pdf_in):
                    print(f"Error: File PDF gốc không tồn tại: '{args.pdf_in}'")
                    sys.exit(1)

                # 2. Kiểm tra danh sách Payload có tồn tại không
                clean_payloads = []
                for path in args.payload:

                    path = path.strip('"').strip("'")
                    if not os.path.exists(path):
                        print(f"Error: Không tìm thấy file/folder: '{path}'")
                        sys.exit(1)
                    clean_payloads.append(path)

                # 3. Thực hiện Embed
                GhostCore.embed(args.pdf_in, clean_payloads, args.pdf_out, args.password)
                abs_path = os.path.abspath(args.pdf_out)
                print(f"Success: {abs_path}")

            elif args.cmd == 'extract':
                blob = GhostCore.extract_search(args.pdf_in)
                if not blob:
                    print("Error: Không tìm thấy dữ liệu ẩn trong file này!")
                    sys.exit(1)
                
                # Logic xử lý pass cho CLI
                fname, data = GhostCore.parse_payload(blob, args.password)
                if not os.path.exists(args.outdir):
                    os.makedirs(args.outdir, exist_ok=True)
                    
                out_path = os.path.join(args.outdir, fname)
                
                # 1. Ghi file (có thể là zip hoặc file thường) xuống đĩa trước
                with open(out_path, 'wb') as f:
                    f.write(data)

                final_path = out_path
                
                if fname.lower().endswith('.zip'):
                    try:
                        extract_folder = os.path.splitext(out_path)[0]
                        
                        with zipfile.ZipFile(out_path, 'r') as zip_ref:
                            zip_ref.extractall(extract_folder)
                        
                        os.remove(out_path)
                        final_path = extract_folder
                    except zipfile.BadZipFile:
                        pass # Nếu lỗi zip thì giữ nguyên file gốc
                    
                print(f"Success: {os.path.abspath(final_path)}")

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        app = GhostUI()
        app.main_loop()

if __name__ == "__main__":
    main()