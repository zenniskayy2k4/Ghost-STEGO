import argparse
import sys
from ghost_ui import GhostUI
from ghost_core import GhostCore

def main():
    # Cấu hình tham số dòng lệnh (CLI arguments)
    # Để nếu muốn chạy automation/script vẫn được
    parser = argparse.ArgumentParser(description="Ghost Stegography PDF Tool")
    subparsers = parser.add_subparsers(dest='cmd')
    
    embed_p = subparsers.add_parser('embed', help="Chế độ dòng lệnh: Ẩn file")
    embed_p.add_argument('pdf_in')
    embed_p.add_argument('payload')
    embed_p.add_argument('pdf_out')
    embed_p.add_argument('-p', '--password', default=None)

    extract_p = subparsers.add_parser('extract', help="Chế độ dòng lệnh: Trích xuất")
    extract_p.add_argument('pdf_in')
    extract_p.add_argument('-o', '--outdir', default='.')
    extract_p.add_argument('-p', '--password', default=None)

    args = parser.parse_args()

    # LOGIC CHÍNH:
    # Nếu có tham số dòng lệnh -> Chạy 1 lần rồi thoát (cho script)
    # Nếu không có tham số -> Chạy giao diện vòng lặp (cho người dùng)
    if args.cmd:
        try:
            if args.cmd == 'embed':
                GhostCore.embed(args.pdf_in, args.payload, args.pdf_out, args.password)
                print(f"[CLI] Success: {args.pdf_out}")
            elif args.cmd == 'extract':
                blob = GhostCore.extract_search(args.pdf_in)
                if not blob:
                    print("[CLI] Error: No data found")
                    sys.exit(1)
                
                # Logic xử lý pass đơn giản cho CLI
                fname, data = GhostCore.parse_payload(blob, args.password)
                import os
                with open(os.path.join(args.outdir, fname), 'wb') as f:
                    f.write(data)
                print(f"[CLI] Success: {fname}")
        except Exception as e:
            print(f"[CLI] Error: {e}")
            sys.exit(1)
    else:
        app = GhostUI()
        app.main_loop()

if __name__ == "__main__":
    main()