# OpenVPN 3 Client GUI

Một ứng dụng GUI dành cho OpenVPN 3 trên Linux (được thiết kế giống với OpenVPN Connect trên Windows/Mac). App hỗ trợ:
- Giao diện Dark mode hiện đại.
- Hiển thị danh sách profile hiện có.
- Connect / Disconnect với các file cấu hình.
- Nút "Import Profile" để nhập các cấu hình `.ovpn`.
- Tự động bắt link xác thực (Auth URL/SSO) và mở bằng trình duyệt tùy chọn.
- Tính năng Advance (Cài đặt nâng cao):
  - Thông báo khi VPN ngắt kết nối đột ngột (thông qua `notify-send` trên Linux).
  - Tự động kết nối lại (Auto-reconnect) nếu bị rớt mạng hoặc ngắt kết nối đột ngột (không auto-reconnect nếu bấm Disconnect thủ công).
  - Lựa chọn trình duyệt (System Default, Google Chrome, Firefox, Brave, Edge) để xử lý Auth SSO.

## Yêu cầu hệ thống

- Linux Debian/Ubuntu based OS.
- `openvpn3` đã được cài đặt.
- `libnotify-bin` (để hiển thị thông báo desktop).
- Python 3.

## Cách chạy ứng dụng môi trường Dev

Do các phiên bản Linux mới (như Debian 12, Ubuntu 24.04) áp dụng cơ chế bảo vệ hệ thống (PEP 668), bạn bắt buộc phải dùng môi trường ảo để cài đặt thư viện.

1. Cài đặt các gói hệ thống cần thiết (để hỗ trợ tạo môi trường ảo và build):
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv libnotify-bin -y
   ```

2. Tạo môi trường ảo (virtual environment) tại thư mục chứa code:
   ```bash
   python3 -m venv venv
   ```

3. Kích hoạt môi trường ảo (lệnh này phải chạy mỗi khi bạn mở terminal mới):
   ```bash
   source venv/bin/activate
   ```

4. Cài đặt thư viện Python:
   ```bash
   pip install -r requirements.txt
   ```

5. Chạy ứng dụng:
   ```bash
   python main.py
   ```

## Cách Build và Deploy ra file .deb (Không cần cài thư viện khi chạy)

Sử dụng script `build_deb.sh` đi kèm để đóng gói toàn bộ app, bao gồm cả các thư viện Python (thông qua PyInstaller) thành một file `.deb` duy nhất.

1. Bật môi trường ảo (BẮT BUỘC để `pyinstaller` nhận diện được các thư viện đã cài):
   ```bash
   source venv/bin/activate
   ```

2. Hãy chắc chắn bạn đã cài đặt các thư viện trong `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

3. Chạy script đóng gói:
   ```bash
   ./build_deb.sh
   ```

4. Script này sẽ thực hiện các bước sau:
   - Dùng `pyinstaller` để build mã nguồn Python thành các file executable (nằm trong thư mục `dist/openvpnclient`).
   - Tạo cấu trúc thư mục của một file `.deb` chuẩn Debian (với folder `DEBIAN`, `/opt/openvpnclient`, `/usr/share/applications/`).
   - Copy file executable vào `/opt/openvpnclient/` và tạo file desktop để bạn có thể search app trong menu hệ thống.
   - Build ra file cài đặt `openvpnclient_1.0.0_amd64.deb`.

4. Cài đặt file `.deb` đã build:
   ```bash
   sudo dpkg -i openvpnclient_1.0.0_amd64.deb
   ```
   *Lưu ý: Nếu bị thiếu dependencies, bạn có thể chạy thêm `sudo apt-get install -f`.*

5. Mở ứng dụng từ Application Menu bằng cách tìm kiếm "OpenVPN Client".
