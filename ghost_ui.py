import os
import sys
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich import box
from ghost_core import GhostCore

console = Console()

BANNER = """
[bold cyan]
  ▄████  ██░ ██  ▒█████    ██████ ▄▄▄█████▓
 ██▒ ▀█▒▓██░ ██▒▒██▒  ██▒▒██    ▒ ▓  ██▒ ▓▒
▒██░▄▄▄░▒██▀▀██░▒██░  ██▒░ ▓██▄   ▒ ▓██░ ▒░
░▓█  ██▓░▓█ ░██ ▒██   ██░  ▒   ██▒░ ▓██▓ ░ 
░▒▓███▀▒░▓█▒░██▓░ ████▓▒░▒██████▒▒  ▒██▒ ░ 
 ░▒   ▒  ▒ ░░▒░▒░ ▒░▒░▒░ ▒ ▒▓▒ ▒ ░  ▒ ░░   
[/bold cyan]
[bold white on blue] GHOST STEGO - LOOP EDITION [/bold white on blue]
"""

class GhostUI:
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def pause(self):
        console.print("\n[dim]Nhấn Enter để quay lại menu...[/dim]")
        input()

    def print_banner(self):
        self.clear_screen()
        console.print(BANNER)

    def handle_embed(self):
        console.print(Panel("[bold green]CHẾ ĐỘ ẨN DỮ LIỆU (EMBED)[/bold green]", border_style="green"))
        
        pdf_in = Prompt.ask("📂 Đường dẫn PDF gốc")
        while not os.path.exists(pdf_in):
            console.print("[red]File không tồn tại![/red]")
            pdf_in = Prompt.ask("📂 Đường dẫn PDF gốc")
            
        file_in = Prompt.ask("📄 File hoặc Thư mục cần ẩn")
        while not os.path.exists(file_in):
            console.print("[red]Đường dẫn không tồn tại![/red]")
            file_in = Prompt.ask("📄 File hoặc Thư mục cần ẩn")
            
        pdf_out = Prompt.ask("💾 Tên file PDF đầu ra", default="output.pdf")
        
        password = None
        if Confirm.ask("🔒 Bạn có muốn đặt mật khẩu không?"):
            password = Prompt.ask("🔑 Nhập mật khẩu", password=True)

        # Gọi Core để xử lý
        try:
            with console.status("[bold green]Đang xử lý..."):
                orig_size = GhostCore.embed(pdf_in, file_in, pdf_out, password)
            
            console.print(f"\n[bold green]✔ Thành công![/bold green]")
            table = Table(box=box.SIMPLE)
            table.add_column("Thông tin", style="cyan")
            table.add_column("Giá trị", style="yellow")
            table.add_row("Input", pdf_in)
            table.add_row("Payload", file_in)
            table.add_row("Output", pdf_out)
            table.add_row("Size ẩn", f"{orig_size} bytes")
            table.add_row("Bảo mật", "AES-256" if password else "None")
            console.print(table)
            
        except Exception as e:
            console.print(f"\n[bold red]✘ Lỗi: {e}[/bold red]")

    def handle_extract(self):
        console.print(Panel("[bold yellow]CHẾ ĐỘ TRÍCH XUẤT (EXTRACT)[/bold yellow]", border_style="yellow"))
        
        pdf_in = Prompt.ask("📂 File PDF cần giải mã")
        while not os.path.exists(pdf_in):
            console.print("[red]File không tồn tại![/red]")
            pdf_in = Prompt.ask("📂 File PDF cần giải mã")

        out_dir = Prompt.ask("💾 Thư mục lưu file", default=".")
        password = Prompt.ask("🔑 Mật khẩu (Enter nếu không có)", password=True)
        if password == "": password = None

        try:
            with console.status("[bold yellow]Đang quét và giải mã..."):
                blob = GhostCore.extract_search(pdf_in)
                
                if not blob:
                    console.print("[bold red]✘ Không tìm thấy dữ liệu ẩn trong file này![/bold red]")
                    return

                # Nếu Core báo cần pass mà user chưa nhập -> Hỏi lại
                try:
                    fname, data = GhostCore.parse_payload(blob, password)
                except PermissionError:
                    console.print("[bold red]! File này yêu cầu mật khẩu.[/bold red]")
                    password = Prompt.ask("🔑 Mời nhập lại mật khẩu", password=True)
                    fname, data = GhostCore.parse_payload(blob, password)

            # Lưu file
            out_path = os.path.join(out_dir, fname)
            with open(out_path, 'wb') as f:
                f.write(data)
            
            console.print(f"\n[bold green]✔ Trích xuất thành công: {out_path}[/bold green]")
            
        except Exception as e:
            console.print(f"\n[bold red]✘ Thất bại: {e}[/bold red]")

    def main_loop(self):
        while True:
            self.print_banner()
            console.print("[1] Ẩn dữ liệu (Embed)", style="bold green")
            console.print("[2] Trích xuất (Extract)", style="bold yellow")
            console.print("[3] Thoát (Exit)", style="bold red")
            
            choice = Prompt.ask("\n👉 Lựa chọn của bạn", choices=["1", "2", "3"], default="1")
            
            if choice == "3":
                console.print("[bold cyan]Tạm biệt! Hẹn gặp lại.[/bold cyan]")
                sys.exit()
            elif choice == "1":
                self.handle_embed()
            elif choice == "2":
                self.handle_extract()
            
            self.pause()