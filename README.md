# GhostStego - Tool Ẩn Dữ Liệu Vào PDF (LSB Steganography)

**GhostStego** là một công cụ Steganography (giấu tin) nâng cao dành cho file PDF, được viết bằng Python.

Khác với các công cụ thông thường sử dụng phương pháp nối đuôi file (Append) dễ bị phát hiện, **GhostStego** sử dụng kỹ thuật **LSB (Least Significant Bit)** để nhúng dữ liệu vào từng điểm ảnh (pixel) của các hình ảnh nằm bên trong file PDF. Điều này giúp file PDF đầu ra giữ nguyên cấu trúc chuẩn, khó bị phát hiện bởi các công cụ forensic cơ bản.
## 🚀 Tính Năng Nổi Bật

1.  **Siêu Tàng Hình (Anti-Forensics):**
    *   Không thay đổi cấu trúc file PDF (Không thêm Object lạ, không nối đuôi file).
    *   Không bị phát hiện bởi các lệnh `strings`, `binwalk` hay `pdf-parser` thông thường.
    *   Nội dung file PDF vẫn hiển thị bình thường.
2.  **Bảo Mật Cấp Cao (High Security):**
    *   Sử dụng thư viện **PyCryptodome**.
    *   Mã hóa **AES-256 chế độ GCM** (Authenticated Encryption): Đảm bảo dữ liệu không thể bị đọc và không thể bị chỉnh sửa trái phép.
    *   **Scrypt KDF:** Chống tấn công dò mật khẩu (Brute-force) tốt hơn PBKDF2.
3.  **Tối Ưu Hóa:**
    *   Tự động nén dữ liệu (Zlib) trước khi giấu để tiết kiệm dung lượng.
    *   Hỗ trợ file PDF chứa nhiều ảnh (tự động phân phối dữ liệu qua các ảnh).

---

## 🛠️ Yêu Cầu Cài Đặt

### 1. Chuẩn bị môi trường
*   Python 3.x trở lên.
*   Hệ điều hành: Windows, Linux hoặc macOS đều được.

### 2. Cài đặt thư viện phụ thuộc
Mở Terminal (hoặc CMD/PowerShell) và chạy lệnh sau để cài đặt các thư viện cần thiết:

```bash
pip install -r requirements.txt
```

*   `pycryptodome`: Dùng để mã hóa AES-GCM và tạo key Scrypt.
*   `pikepdf`: Dùng để phân tích cấu trúc PDF và trích xuất/thay thế stream hình ảnh.
*   `pillow` (PIL): Dùng để xử lý ma trận điểm ảnh (Pixel manipulation).
---

## 📖 Hướng Dẫn Sử Dụng

### 1. Ẩn dữ liệu (Embed)
Dùng để giấu một file bất kỳ vào trong file PDF.

**Cú pháp:**
```bash
python ghostpixel.py embed <File_PDF_Gốc> <File_Cần_Giấu> <File_PDF_Đầu_Ra> -p "<Mật_Khẩu>"
```

**Ví dụ:**
Bạn muốn giấu file `bi_mat.txt` vào file `tai_lieu.pdf`, tạo ra file `tai_lieu_secure.pdf` với mật khẩu là `123456`:

```bash
python ghostpixel.py embed tai_lieu.pdf bi_mat.txt tai_lieu_secure.pdf -p "123456"
```

> **Lưu ý:** File PDF gốc (`tai_lieu.pdf`) **bắt buộc phải có hình ảnh** bên trong (ví dụ: sách scan, slide bài giảng có hình minh họa...). Nếu file chỉ toàn chữ, tool sẽ báo lỗi không tìm thấy chỗ chứa.

### 2. Trích xuất dữ liệu (Extract)
Dùng để lấy file ẩn ra khỏi file PDF đã stego.

**Cú pháp:**
```bash
python ghostpixel.py extract <File_PDF_Stego> <File_Đầu_Ra> -p "<Mật_Khẩu>"
```

**Ví dụ:**
Lấy dữ liệu từ `tai_lieu_secure.pdf` lưu ra thành `kho_bau.txt`:

```bash
python ghostpixel.py extract tai_lieu_secure.pdf kho_bau.txt -p "123456"
```

---

## 🧠 Nguyên Lý Hoạt Động (Dành cho báo cáo)

Nếu thầy giáo hỏi tool hoạt động thế nào, hãy trình bày theo 3 bước sau:

### Bước 1: Tiền xử lý & Mã hóa (Cryptography)
1.  Dữ liệu cần giấu được nén bằng **Zlib** để giảm kích thước.
2.  Mật khẩu người dùng được đưa qua thuật toán **Scrypt** (với Salt ngẫu nhiên) để tạo ra khóa 256-bit mạnh mẽ.
3.  Dữ liệu nén được mã hóa bằng **AES-GCM**. Kết quả bao gồm: `Salt` + `Nonce` + `Tag` (xác thực toàn vẹn) + `Ciphertext`.

### Bước 2: Nhúng vào ảnh (Image Steganography)
1.  Tool dùng thư viện `pikepdf` để quét toàn bộ các Object trong file PDF.
2.  Khi tìm thấy một Object là hình ảnh (`/Type /XObject /Subtype /Image`), tool sẽ giải nén stream ảnh đó ra thành ma trận điểm ảnh (RGB).
3.  Tool thực hiện kỹ thuật **LSB Replacement**: Thay thế bit cuối cùng (bit thứ 0) của các kênh màu Red, Green, Blue bằng từng bit của dữ liệu mã hóa.
    *   *Mắt thường không thể phân biệt sự thay đổi này vì giá trị màu chỉ thay đổi 1 đơn vị (ví dụ RGB(200, 100, 50) thành RGB(201, 100, 50)).*

### Bước 3: Tái tạo PDF (Reconstruction)
1.  Sau khi nhúng xong, ảnh được nén lại (FlateDecode) và đưa ngược vào cấu trúc PDF.
2.  File PDF được lưu lại với cấu trúc hoàn toàn hợp lệ.

---

## ⚠️ Các Lưu Ý Quan Trọng

1.  **Giới hạn dung lượng:** Dung lượng có thể giấu phụ thuộc vào **tổng diện tích (pixel)** của các hình ảnh trong file PDF.
    *   *Công thức ước tính:* (Tổng số Pixel * 3) / 8 = Số byte tối đa có thể giấu.
    *   Ví dụ: Một ảnh 800x600 px có thể chứa khoảng: (480,000 * 3)/8 ≈ 180 KB dữ liệu.
2.  **Kích thước file PDF:** File PDF sau khi stego có thể tăng dung lượng nhẹ (do dữ liệu ngẫu nhiên đã mã hóa thường khó nén hơn dữ liệu ảnh gốc), nhưng không đáng kể.
3.  **Tương thích:** File PDF đầu ra mở được trên mọi trình đọc (Adobe Acrobat, Foxit Reader, Chrome, Edge...).

---