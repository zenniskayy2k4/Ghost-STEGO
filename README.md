# GhostStego - Công cụ ẩn dữ liệu vào file PDF (Output Intents Injection)

**GhostStego** là công cụ Steganography chuyên dụng cho định dạng PDF. Thay vì sử dụng các phương pháp truyền thống dễ bị phát hiện (như nối đuôi file), GhostStego sử dụng kỹ thuật **Output Intents Injection** để giấu dữ liệu vào cấu trúc cấu hình in ấn của file PDF.

## 🚀 Tính năng nổi bật

1.  **Siêu Tàng Hình (Anti-Forensics):**
    *   Dữ liệu được ngụy trang thành một **ICC Profile** (cấu hình màu sắc) hợp lệ.
    *   Không bị phát hiện bởi các lệnh quét cơ bản như `pdf-parser` (không báo lỗi cấu trúc).
    *   Không để lại dữ liệu thừa ở cuối file (EOF).

2.  **Bảo Mật & Toàn Vẹn:**
    *   **Mã hóa AES-256 GCM:** Bảo mật dữ liệu tuyệt đối.
    *   **Integrity Check:** Tự động phát hiện nếu dữ liệu ẩn bị chỉnh sửa/cắt xén.
    *   **Scrypt KDF:** Chống tấn công dò mật khẩu (Brute-force).

3.  **Tiện Ích Mạnh Mẽ:**
    *   **Hỗ trợ Thư mục (Folder):** Tự động nén cả thư mục thành file Zip trước khi giấu.
    *   **Giữ kích thước tự nhiên:** File PDF đầu ra tăng dung lượng hợp lý, không bị nén nhỏ bất thường.
    *   **Giao diện kép:** Hỗ trợ cả giao diện dòng lệnh (CLI) và giao diện tương tác (Interactive Menu).

---

## 🛠️ Yêu cầu cài đặt

### 1. Chuẩn bị môi trường
*   Python 3.8 trở lên.
*   Hệ điều hành: Windows, Linux hoặc macOS đều được.

### 2. Cài đặt thư viện phụ thuộc
Mở Terminal (hoặc CMD/PowerShell) và chạy lệnh sau để cài đặt các thư viện cần thiết:

```bash
pip install -r requirements.txt
```

*   `pycryptodome`: Dùng để mã hóa AES-GCM và tạo key Scrypt.
*   `pikepdf`: Dùng để phân tích cấu trúc PDF và trích xuất/thay thế stream hình ảnh.
*   `rich`: Dùng để xây dựng giao diện CLI đẹp mắt.
---

## 📖 Hướng dẫn sử dụng

### Cách 1: Chạy giao diện tương tác (Khuyên dùng)
Chỉ cần chạy file `main.py` không kèm tham số:

```bash
python main.py
```
Chương trình sẽ hiện Menu để bạn chọn:
1.  **Embed:** Nhập đường dẫn PDF gốc &rarr; Nhập file/folder cần giấu &rarr; Nhập mật khẩu.
2.  **Extract:** Nhập file PDF &rarr; Nhập mật khẩu để lấy dữ liệu.

### Cách 2: Chạy dòng lệnh (Automation)

**1. Ẩn dữ liệu (Hỗ trợ nhiều file/folder):**

**Cú pháp:**
```bash
python main.py embed <PDF_Gốc> <Input_1> [Input_2 ...] <PDF_Output> -p "<Mật_Khẩu>"
```
*(Nếu input là Folder hoặc nhiều file/folder, tool sẽ tự động nén Zip trước khi giấu)*

**Ví dụ:**
Bạn muốn giấu file `bi_mat.txt` vào file `tai_lieu.pdf`, tạo ra file `tai_lieu_secure.pdf` với mật khẩu là `123456`:

```bash
python main.py embed tai_lieu.pdf bi_mat.txt tai_lieu_secure.pdf -p "123456"
```

**Ví dụ:**
Giấu một file ảnh, một file text và cả một thư mục code vào file `baocao.pdf`:

```bash
python main.py embed baocao.pdf hinh.png secret.txt ./SourceCode baocao_stego.pdf -p "123456"
```
*(Tool sẽ tự động gom 3 thành phần trên thành 1 file nén và nhúng vào PDF)*

**2. Trích xuất dữ liệu:**

**Cú pháp:**
```bash
# -o: (Optional) Thư mục để lưu file giải nén (Mặc định là thư mục hiện tại)
python main.py extract <File_PDF_Stego> -o <Thư_mục_Output> -p <Mật_Khẩu>
```

**Ví dụ:**
Lấy dữ liệu từ `tai_lieu_secure.pdf` lưu vào thư mục `ket_qua`:

```bash
python main.py extract tai_lieu_secure.pdf -o ./ket_qua -p "123456"
```
*(Nếu dữ liệu là bị tool nén trước khi giấu, tool sẽ tự động giải nén ra nguyên trạng)*

---

## Lưu ý quan trọng về Mật khẩu

### 1. Khi chạy chế độ Dòng lệnh
Nếu mật khẩu của bạn có chứa **khoảng trắng (dấu cách)** hoặc **các ký tự đặc biệt** (ví dụ: `!`, `@`, `$`, `&`), **BẮT BUỘC** phải đặt mật khẩu trong dấu ngoặc kép `""`.

*   ❌ **Sai:** `python main.py ... -p mat khau 123` (Chương trình sẽ hiểu 'khau' và '123' là tên file)
*   ✅ **Đúng:** `python main.py ... -p "mat khau 123"`
*   ✅ **Đúng:** `python main.py ... -p "P@ssw0rd!"`

### 2. Khi chạy chế độ Tương tác (Interactive Menu)
Khi chương trình hỏi `Nhập mật khẩu:`, hãy nhập trực tiếp mật khẩu mà **KHÔNG** cần thêm dấu ngoặc kép (trừ khi mật khẩu của bạn thực sự chứa dấu ngoặc kép). Chương trình sẽ đọc chính xác những gì đã gõ.

---

## Cơ chế kỹ thuật

*   **Injection Strategy:** Tạo một Stream Object mới chứa dữ liệu đã mã hóa, gán Type là `/OutputIntent` và gắn vào `Root/OutputIntents`.
*   **Structure Preservation:** Sử dụng chế độ `pikepdf.ObjectStreamMode.disable` khi lưu để bảo toàn cấu trúc object gốc, giúp file tránh bị các phần mềm diệt virus nghi ngờ do nén quá mức.

---

## Công cụ hỗ trợ kiểm thử

Để thuận tiện cho việc đánh giá, dự án cung cấp sẵn script tạo file PDF mẫu (Clean PDF) sử dụng thư viện `reportlab`.

**File:** `test/create_pdf.py`

**Chức năng:** Tạo ra file `Sample.pdf` chuẩn A4 chứa văn bản mẫu để làm dữ liệu đầu vào (Cover file) cho quá trình giấu tin.

**Cách sử dụng:**

1. Đảm bảo đã cài đặt đầy đủ thư viện (bao gồm `reportlab`):
   ```bash
   pip install -r requirements.txt
   ```

2. Chạy script tạo file:
   ```bash
   python test/create_pdf.py
   ```
   *(File `Sample.pdf` sẽ được tạo ra ngay tại thư mục hiện tại)*